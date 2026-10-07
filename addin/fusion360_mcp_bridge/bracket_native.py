"""Construct the PCB bracket through native Fusion sketches and features."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion

W=21.08
TFT_HOLES=[(2.41,2.41),(18.67,2.41)]
REAR_HOLES=[(-2,29),(23.08,29),(-2,54),(23.08,54)]

def value(v):
    return adsk.core.ValueInput.createByReal(v/10)

def component(parent,name):
    occ=parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name=name
    return occ.component

def primitive(comp,kind,coords,label):
    sketch=comp.sketches.add(comp.xYConstructionPlane)
    sketch.name=label+'_sketch'
    if kind=='box':
        x,y,z,w,l,h=coords
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(x/10,y/10,0),
            adsk.core.Point3D.create((x+w)/10,(y+l)/10,0))
    else:
        x,y,z,r,h=coords
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x/10,y/10,0),r/10)
    ext=comp.features.extrudeFeatures.createInput(
        sketch.profiles.item(0),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.startExtent=adsk.fusion.OffsetStartDefinition.create(value(z))
    ext.setDistanceExtent(False,value(h))
    feature=comp.features.extrudeFeatures.add(ext)
    feature.name=label+'_extrude'
    sketch.isVisible=False
    feature.bodies.item(0).name=label
    return feature.bodies.item(0)

def join(comp,name):
    target=comp.bRepBodies.item(0)
    tools=adsk.core.ObjectCollection.create()
    for i in range(1,comp.bRepBodies.count): tools.add(comp.bRepBodies.item(i))
    combine=comp.features.combineFeatures.createInput(target,tools)
    combine.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    combine.isKeepToolBodies=False
    feat=comp.features.combineFeatures.add(combine)
    feat.name=name+'_join'
    if comp.bRepBodies.count!=1:
        raise RuntimeError(name+' must be one body, got '+str(comp.bRepBodies.count))
    body=comp.bRepBodies.item(0)
    body.name=name
    return body

def drill(comp,body,holes,z,height,r=1.1):
    sketch=comp.sketches.add(comp.xYConstructionPlane)
    sketch.name='M2_hole_locations'
    for x,y in holes:
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x/10,y/10,0),r/10)
    profiles=adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count): profiles.add(sketch.profiles.item(i))
    ext=comp.features.extrudeFeatures.createInput(profiles,adsk.fusion.FeatureOperations.CutFeatureOperation)
    ext.startExtent=adsk.fusion.OffsetStartDefinition.create(value(z))
    ext.setDistanceExtent(False,value(height))
    ext.participantBodies=[body]
    cut=comp.features.extrudeFeatures.add(ext)
    cut.name='M2_clearance_holes'
    sketch.isVisible=False

def set_color(design,body,name,r,g,b):
    appearance=design.appearances.itemByName(name)
    if not appearance:
        base=body.appearance
        for library in adsk.core.Application.get().materialLibraries:
            try:
                candidate=library.appearances.itemByName('Plastic - Matte (White)')
            except RuntimeError:
                candidate=None
            if candidate:
                base=candidate
                break
        appearance=design.appearances.addByCopy(base,name)
    for prop in appearance.appearanceProperties:
        color=adsk.core.ColorProperty.cast(prop)
        if color:
            try: color.value=adsk.core.Color.create(r,g,b,255)
            except Exception: pass
    body.appearance=appearance

def interference(a,b):
    mgr=adsk.fusion.TemporaryBRepManager.get()
    temp=mgr.copy(a)
    other=mgr.copy(b)
    ok=mgr.booleanOperation(temp,other,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return temp.volume*1000 if ok else 0.0

def describe_body(body):
    bb=body.boundingBox
    return {'name':body.name,'solid':body.isSolid,'volume_mm3':body.volume*1000,
            'bounds_mm':[v*10 for v in (bb.minPoint.x,bb.minPoint.y,bb.minPoint.z,
                                        bb.maxPoint.x,bb.maxPoint.y,bb.maxPoint.z)]}

def inspect(design,assembly):
    frame=assembly.occurrences.item(0).component
    keeper=assembly.occurrences.item(1).component
    result={'component':assembly.name,'frame_body_count':frame.bRepBodies.count,
            'keeper_body_count':keeper.bRepBodies.count,
            'frame_sketch_count':frame.sketches.count,
            'keeper_sketch_count':keeper.sketches.count,
            'frame':describe_body(frame.bRepBodies.item(0)),
            'keeper':describe_body(keeper.bRepBodies.item(0)),
            'native_sketch_extrude':True}
    fb=frame.bRepBodies.item(0)
    kb=keeper.bRepBodies.item(0)
    epcb=assembly.occurrences.item(3).component.bRepBodies.item(0)
    result['frame_keeper_overlap_mm3']=interference(fb,kb)
    result['frame_esp_overlap_mm3']=interference(fb,epcb)
    result['keeper_esp_overlap_mm3']=interference(kb,epcb)
    return result

def build(design,args):
    if args.get('action','').endswith('_case_v3'):
        import importlib.util
        spec=importlib.util.spec_from_file_location('fusion_case_v3_native',Path(__file__).with_name('case_v3_native.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        return mod.run(design,args,globals())
    if args.get('action','').endswith('_case_v2'):
        import importlib.util
        spec=importlib.util.spec_from_file_location('fusion_case_v2_native',Path(__file__).with_name('case_v2_native.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        return mod.run(design,args,globals())
    if args.get('action') in ('build_case','finish_case','inspect_case','present_case','export_case'):
        import importlib.util
        spec=importlib.util.spec_from_file_location('fusion_case_native',Path(__file__).with_name('case_native.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        return mod.run(design,args,globals())
    if design.designIntent == adsk.fusion.DesignIntentTypes.PartDesignIntentType:
        design.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
    root=design.rootComponent
    name='KHUNG_GA_PCB_TFT_ESP32_NATIVE'
    if args.get('action')=='state':
        result=[]
        for occ in root.occurrences:
            item={'name':occ.component.name,'transform':occ.transform2.asArray(),'children':[]}
            for child in occ.component.occurrences:
                item['children'].append({'name':child.component.name,
                    'transform':child.transform2.asArray(),
                    'visible':child.isLightBulbOn,
                    'bodies':[describe_body(b) for b in child.component.bRepBodies]})
            result.append(item)
        return {'design_intent':int(design.designIntent),'occurrences':result}
    if args.get('action')=='inspect':
        for occ in root.occurrences:
            if occ.component.name==name:
                design.activateRootComponent()
                if 'show_references' in args:
                    for child in occ.component.occurrences:
                        if child.component.name.startswith('REF_'):
                            child.isLightBulbOn=bool(args['show_references'])
                if args.get('refresh_colors'):
                    set_color(design,occ.component.occurrences.item(0).component.bRepBodies.item(0),'Bracket_matte_blue',60,152,178)
                    set_color(design,occ.component.occurrences.item(1).component.bRepBodies.item(0),'Keeper_matte_orange',230,138,50)
                app=adsk.core.Application.get()
                if args.get('fit'): app.activeViewport.fit()
                app.activeViewport.refresh()
                result=inspect(design,occ.component)
                if args.get('report_path'):
                    Path(args['report_path']).write_text(json.dumps(result,indent=2),encoding='utf-8')
                return result
        raise RuntimeError('Native PCB bracket is not present')
    for occ in root.occurrences:
        if occ.component.name==name:
            raise RuntimeError('Native bracket already exists; inspect it rather than duplicating')
    assembly=component(root,name)
    frame=component(assembly,'01_KHUNG_CHINH')
    keeper=component(assembly,'02_NEP_GIU_ESP32')
    frames=[
        ('box',(-3.9,0,-4,3.8,69.2,3)),
        ('box',(W+.1,0,-4,3.8,69.2,3)),
        ('box',(-3.9,0,-4,W+7.8,5.2,3)),
        ('box',(-3.9,66,-4,W+7.8,3.2,3)),
        ('box',(0,66.5,-1,1.3,2.7,1)),
        ('box',(W-1.3,66.5,-1,1.3,2.7,1)),
        ('box',(-3.9,27.5,-8.8,W+7.8,3.2,2)),
        ('box',(-3.9,52.25,-8.8,W+7.8,3.25,2)),
    ]
    frames += [('circle',(x,y,-4,2.2,4)) for x,y in TFT_HOLES]
    frames += [('circle',(x,y,-12.4,1.95,11.4)) for x,y in REAR_HOLES]
    for x in (1.64,16.88):
        for y,l in ((30,.65),(52.25,.45)):
            frames.append(('box',(x,y,-11,2.56,l,4.2)))
    for i,(kind,p) in enumerate(frames): primitive(frame,kind,p,'Frame_'+str(i+1))
    frame_body=join(frame,'KHUNG_LIEN_KHOI')
    drill(frame,frame_body,TFT_HOLES+REAR_HOLES,-15,17)
    frame_body=frame.bRepBodies.item(0)
    set_color(design,frame_body,'Bracket_blue',45,133,158)

    keepers=[
        ('box',(-3.9,27.5,-14.4,3.8,28,2)),
        ('box',(W+.1,27.5,-14.4,3.8,28,2)),
        ('box',(-3.9,27.5,-14.4,W+7.8,2,2)),
        ('box',(-3.9,29.5,-14.4,8.1,.95,2)),
        ('box',(16.88,29.5,-14.4,8.1,.95,2)),
        ('box',(-3.9,52.25,-14.4,8.1,3.25,2)),
        ('box',(16.88,52.25,-14.4,8.1,3.25,2)),
    ]
    for x in (1.64,16.88):
        for y,l in ((30,.45),(52.25,.45)):
            keepers.append(('box',(x,y,-12.4,2.56,l,.5)))
        keepers += [('box',(x,29.55,-12.4,2.56,.45,1.5)),
                    ('box',(x,52.7,-12.4,2.56,.45,1.5))]
    for x in (.69,19.59):
        for y in (30,52.25): keepers.append(('box',(x,y,-12.4,.8,.45,1.5)))
    for i,(kind,p) in enumerate(keepers): primitive(keeper,kind,p,'Keeper_'+str(i+1))
    keeper_body=join(keeper,'NEP_ESP32_THAO_ROI')
    drill(keeper,keeper_body,REAR_HOLES,-16,8)
    keeper_body=keeper.bRepBodies.item(0)
    set_color(design,keeper_body,'Keeper_orange',236,144,55)

    # Native dimensional references, each clearly marked as a proxy.
    tft=component(assembly,'REF_TFT_PCB_LCD_DIMENSIONAL_PROXY')
    tpcb=primitive(tft,'box',(0,0,0,W,73.15,1.6),'TFT_PCB_proxy_thickness_1p6')
    drill(tft,tpcb,TFT_HOLES,-1,5,1.25)
    set_color(design,tft.bRepBodies.item(0),'TFT_green',20,102,50)
    lcd=primitive(tft,'box',(1.98,8.4,1.6,17,60.55,1.5),'LCD_proxy')
    set_color(design,lcd,'LCD_black',25,30,34)
    esp=component(assembly,'REF_ESP32_PCB_MEASURED_FROM_STEP')
    epcb=primitive(esp,'box',(1.64,30,-11.9,17.8,22.7,.9),'ESP_PCB_17p8_22p7_0p9')
    set_color(design,epcb,'ESP_blue',20,65,140)
    usb=primitive(esp,'box',(6.04,46.6,-15.1,9,7.4,3.2),'USB_C_DIMENSIONAL_PROXY')
    set_color(design,usb,'USB_silver',160,168,175)

    # Hide the known earlier failed bracket bodies, preserving their history.
    for body in root.bRepBodies:
        if body.name.startswith(('V3_','V2_','TFT_RAIL_','ESP_RAIL_','ESP_STOP_','ESP_LIP_','SPACER_')) or body.name=='BRACKET_TEST':
            body.isVisible=False
    for sketch in root.sketches: sketch.isVisible=False
    design.activateRootComponent()
    app=adsk.core.Application.get()
    app.activeViewport.fit()
    app.activeViewport.refresh()
    result=inspect(design,assembly)
    result['frame_keeper_overlap_mm3']=interference(frame_body,keeper_body)
    result['frame_esp_overlap_mm3']=interference(frame_body,epcb)
    result['keeper_esp_overlap_mm3']=interference(keeper_body,epcb)
    result['assumptions']=['TFT thickness and LCD thickness are dimensional proxies; real backside components need fit check.']
    out=args.get('report_path')
    if out: Path(out).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
