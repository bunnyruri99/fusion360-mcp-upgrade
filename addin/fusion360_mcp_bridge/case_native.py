"""Native sketches, extrudes and cuts for the complete flip-clock enclosure."""
import importlib.util
import json
import math
from pathlib import Path
import adsk.core
import adsk.fusion

NAME='FLIP_CLOCK_CASE_LAP_RAP_NATIVE'

def load_recipe():
    spec=importlib.util.spec_from_file_location('flip_case_recipe',Path(__file__).with_name('case_recipe.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def extrude(comp,shape,label,body=None):
    kind=shape['kind'];p=shape['p']
    if kind=='cone_x':
        start,y,z,r1,r2,h=p
        profiles=[]
        for i,(x,r) in enumerate(((start,r1),(start+h,r2))):
            pi=comp.constructionPlanes.createInput()
            pi.setByOffset(comp.yZConstructionPlane,adsk.core.ValueInput.createByReal(x*comp.yZConstructionPlane.geometry.normal.x/10))
            pl=comp.constructionPlanes.add(pi);pl.name=label+'_plane_'+str(i);pl.isLightBulbOn=False
            sk=comp.sketches.add(pl);sk.name=label+'_profile_'+str(i)
            center=sk.modelToSketchSpace(adsk.core.Point3D.create(x/10,y/10,z/10))
            sk.sketchCurves.sketchCircles.addByCenterRadius(center,r/10)
            profiles.append(sk.profiles.item(0));sk.isVisible=False
        op=adsk.fusion.FeatureOperations.CutFeatureOperation if body else adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        li=comp.features.loftFeatures.createInput(op)
        for profile in profiles:li.loftSections.add(profile)
        if body:li.participantBodies=[body]
        f=comp.features.loftFeatures.add(li);f.name=label
        return f.bodies.item(0)
    if kind=='circle_x':
        start,y,z,r,h=p
        plane=comp.yZConstructionPlane;axis=plane.geometry.normal.x
        corner0=adsk.core.Point3D.create(0,y/10,z/10)
    elif kind=='rounded_xz':
        x,y,start,w,l,h,r=p
        plane=comp.xZConstructionPlane
        axis=plane.geometry.normal.y
        corner0=adsk.core.Point3D.create(x/10,0,y/10)
        corner1=adsk.core.Point3D.create((x+w)/10,0,(y+l)/10)
    else:
        plane=comp.xYConstructionPlane
        axis=plane.geometry.normal.z
        if kind=='hex':
            x,y,start,af,h=p
        elif kind=='circle':
            x,y,start,r,h=p
        else:
            x,y,start,w,l,h=p[:6]
            r=p[6] if kind=='rounded' else 0
        corner0=adsk.core.Point3D.create(x/10,y/10,0)
        if kind not in ('circle','hex'): corner1=adsk.core.Point3D.create((x+w)/10,(y+l)/10,0)
    sk=comp.sketches.add(plane)
    sk.name=label+'_sketch'
    p0=sk.modelToSketchSpace(corner0)
    if kind=='hex':
        radius=af/math.sqrt(3)/10
        points=[adsk.core.Point3D.create(p0.x+radius*math.cos(i*math.pi/3),p0.y+radius*math.sin(i*math.pi/3),0) for i in range(6)]
        for i in range(6):sk.sketchCurves.sketchLines.addByTwoPoints(points[i],points[(i+1)%6])
    elif kind in ('circle','circle_x'):
        sk.sketchCurves.sketchCircles.addByCenterRadius(p0,r/10)
    elif kind=='box':
        sk.sketchCurves.sketchLines.addTwoPointRectangle(p0,sk.modelToSketchSpace(corner1))
    else:
        p1=sk.modelToSketchSpace(corner1)
        u,v=min(p0.x,p1.x),min(p0.y,p1.y)
        sw,sl,rr=abs(p1.x-p0.x),abs(p1.y-p0.y),r/10
        def pt(a,b):return adsk.core.Point3D.create(a,b,0)
        ln=sk.sketchCurves.sketchLines
        for a,b in [((u+rr,v),(u+sw-rr,v)),((u+sw,v+rr),(u+sw,v+sl-rr)),
                    ((u+sw-rr,v+sl),(u+rr,v+sl)),((u,v+sl-rr),(u,v+rr))]:
            ln.addByTwoPoints(pt(*a),pt(*b))
        arcs=sk.sketchCurves.sketchArcs
        for center,startpt in [((u+sw-rr,v+rr),(u+sw-rr,v)),
                               ((u+sw-rr,v+sl-rr),(u+sw,v+sl-rr)),
                               ((u+rr,v+sl-rr),(u+rr,v+sl)),
                               ((u+rr,v+rr),(u,v+rr))]:
            arcs.addByCenterStartSweep(pt(*center),pt(*startpt),math.pi/2)
    if sk.profiles.count!=1:
        raise RuntimeError(label+': expected 1 closed profile, got '+str(sk.profiles.count))
    operation=adsk.fusion.FeatureOperations.CutFeatureOperation if body else adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    inp=comp.features.extrudeFeatures.createInput(sk.profiles.item(0),operation)
    inp.startExtent=adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(start*axis/10))
    distance=adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(h/10))
    direction=adsk.fusion.ExtentDirections.PositiveExtentDirection if axis>0 else adsk.fusion.ExtentDirections.NegativeExtentDirection
    inp.setOneSideExtent(distance,direction)
    if body:inp.participantBodies=[body]
    feat=comp.features.extrudeFeatures.add(inp)
    feat.name=label
    sk.isVisible=False
    if not body:feat.bodies.item(0).name=label
    return feat.bodies.item(0)

def window_reveal(comp,body,sections,radius):
    profiles=[]
    for index,(x,y,z,w,h,r) in enumerate(sections):
        plane_input=comp.constructionPlanes.createInput()
        plane_input.setByOffset(comp.xYConstructionPlane,adsk.core.ValueInput.createByReal(z/10))
        plane=comp.constructionPlanes.add(plane_input)
        plane.name='Window_reveal_plane_'+str(index+1);plane.isLightBulbOn=False
        sk=comp.sketches.add(plane);sk.name='Window_reveal_profile_'+str(index+1)
        x,y,w,h,r=[v/10 for v in (x,y,w,h,r)]
        def pt(a,b):return adsk.core.Point3D.create(a,b,0)
        lines=sk.sketchCurves.sketchLines
        for a,b in [((x+r,y),(x+w-r,y)),((x+w,y+r),(x+w,y+h-r)),
                    ((x+w-r,y+h),(x+r,y+h)),((x,y+h-r),(x,y+r))]:
            lines.addByTwoPoints(pt(*a),pt(*b))
        for c,s in [((x+w-r,y+r),(x+w-r,y)),((x+w-r,y+h-r),(x+w,y+h-r)),
                    ((x+r,y+h-r),(x+r,y+h)),((x+r,y+r),(x,y+r))]:
            sk.sketchCurves.sketchArcs.addByCenterStartSweep(pt(*c),pt(*s),math.pi/2)
        if sk.profiles.count!=1:raise RuntimeError('Window loft requires one profile')
        profiles.append(sk.profiles.item(0));sk.isVisible=False
    inp=comp.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.CutFeatureOperation)
    for profile in profiles:inp.loftSections.add(profile)
    inp.participantBodies=[body]
    feat=comp.features.loftFeatures.add(inp);feat.name='CUA_SO_VAT_DAN_XUONG_MAN'
    soften_window_rim(comp,radius)

def soften_window_rim(comp,radius):
    # Only soften the entry rim; keep the viewing aperture dimension unchanged.
    edges=adsk.core.ObjectCollection.create()
    for edge in comp.bRepBodies.item(0).edges:
        bb=edge.boundingBox
        if (abs(bb.minPoint.z-.53)<1e-6 and abs(bb.maxPoint.z-.53)<1e-6
            and bb.minPoint.x>0 and bb.maxPoint.x<2.108
            and bb.minPoint.y>1 and bb.maxPoint.y<7.2):edges.add(edge)
    # Fusion can merge the tangent profile into one closed NURBS edge.
    if edges.count<1:raise RuntimeError('Window entry rim was not found')
    fi=comp.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(edges,adsk.core.ValueInput.createByReal(radius/10),True)
    fillet=comp.features.filletFeatures.add(fi);fillet.name='BO_MEM_MEP_CUA_SO_R'+str(radius)

def create_lid(design,assembly,recipe,api):
    lid=api['component'](assembly,'04_NAP_SAU')
    body=extrude(lid,recipe['outer'],'Lid_outer')
    lip=extrude(lid,recipe['lip'],'Lid_location_lip')
    extrude(lid,recipe['lip_inside'],'Lid_lip_hollow',lip)
    for i,s in enumerate(recipe.get('parts',[])):extrude(lid,s,'Lid_support_'+str(i+1))
    body=api['join'](lid,'NAP_SAU_LIEN_KHOI')
    for i,s in enumerate(recipe['cuts']):extrude(lid,s,'Lid_cut_'+str(i+1),body)
    api['set_color'](design,lid.bRepBodies.item(0),'Lid_matte',125,130,136)

def add_references(design,assembly,R,api):
    root=design.rootComponent
    if not any(o.component.name.startswith('REF_TFT') for o in assembly.occurrences):
        previous=next(o for o in root.occurrences if o.component.name=='KHUNG_GA_PCB_TFT_ESP32_NATIVE')
        tft=next(o.component for o in previous.component.occurrences if o.component.name.startswith('REF_TFT'))
        assembly.occurrences.addExistingComponent(tft,adsk.core.Matrix3D.create())
    if not any(o.component.name.startswith('REF_ESP32_ACTUAL_STEP') for o in assembly.occurrences):
        esp_comp=api['component'](assembly,'REF_ESP32_ACTUAL_STEP')
        manager=adsk.core.Application.get().importManager
        options=manager.createSTEPImportOptions(R.ESP_SOURCE)
        if not manager.importToTarget(options,esp_comp):raise RuntimeError('ESP reference import failed')

def transform_from_mm(data):
    a=list(data)
    for i in (3,7,11):a[i]/=10
    m=adsk.core.Matrix3D.create();m.setWithArray(a)
    return m

def multiply(a,b):
    return [sum(a[i*4+k]*b[k*4+j] for k in range(4)) for i in range(4) for j in range(4)]

def world_bodies(occ):
    mgr=adsk.fusion.TemporaryBRepManager.get()
    # Root-context occurrence proxies include the placement overrides of parents.
    mat=occ.transform2
    out=[]
    for b in occ.component.bRepBodies:
        copied=mgr.copy(b);mgr.transform(copied,mat)
        out.append((b.name,copied))
    for child in occ.childOccurrences:out+=world_bodies(child)
    return out

def inspect(design,occ,R,api):
    groups={child.component.name:world_bodies(child) for child in occ.childOccurrences}
    printed=[name for name in groups if name.startswith(('01_','02_','03_','04_'))]
    report={'assembly':NAME,'native_sketch_extrude':True,'printed_parts':{},'intersections_mm3':{}}
    for name in printed:
        bodies=groups[name]
        if len(bodies)!=1 or not bodies[0][1].isSolid:raise RuntimeError(name+' is not one solid')
        report['printed_parts'][name]=api['describe_body'](bodies[0][1])
    keys=list(groups)
    for i,a in enumerate(keys):
        if a not in printed:continue
        for b in keys:
            if b==a or b.startswith('HW_') or (b in printed and keys.index(b)<i):continue
            total=sum(api['interference'](ba,bb) for _,ba in groups[a] for _,bb in groups[b])
            report['intersections_mm3'][a+' / '+b]=round(total,8)
            if total>1e-4:raise RuntimeError('Collision '+a+' / '+b+': '+str(total)+' mm3')
    esp_name=next(n for n in groups if n.startswith('REF_ESP'))
    report['ESP_reference_body_count']=len(groups[esp_name])
    def measured_solid(dimensions):
        matches=[]
        for name,solid in groups[esp_name]:
            bounds=api['describe_body'](solid)['bounds_mm']
            if all(abs(bounds[i+3]-bounds[i]-dimensions[i])<1e-5 for i in range(3)):
                matches.append(solid)
        if len(matches)!=1:raise RuntimeError('Expected one ESP solid of size '+str(dimensions))
        return matches[0]
    # Fusion's STEP importer assigns Body1...Body61; identify using measured sizes.
    board=measured_solid((17.8,22.7,.9))
    usb=measured_solid((9,7.4,3.2))
    report['ESP_board']=api['describe_body'](board)
    report['USB_body']=api['describe_body'](usb)
    report['PCB_gap_mm']=-board.boundingBox.maxPoint.z*10
    report['USB_front_recess_mm']=usb.boundingBox.minPoint.y*10-R.CASE_OUT[1]
    report['case_outer_mm']=[R.CASE_OUT[2],R.CASE_OUT[3],R.CASE_FRONT-R.CASE_BACK]
    tft_name=next(n for n in groups if n.startswith('REF_TFT'))
    tft_pcb=next(s for n,s in groups[tft_name] if n.startswith('TFT_PCB'))
    frame_body=groups[next(n for n in printed if n.startswith('01_'))][0][1]
    report['TFT_to_frame_seating_gap_mm']=(tft_pcb.boundingBox.minPoint.z-frame_body.boundingBox.maxPoint.z)*10
    mgr=adsk.fusion.TemporaryBRepManager.get();seating_copy=mgr.copy(tft_pcb)
    seating_matrix=adsk.core.Matrix3D.create()
    seating_matrix.translation=adsk.core.Vector3D.create(0,0,-.0001)
    mgr.transform(seating_copy,seating_matrix)
    report['TFT_frame_contact_area_mm2']=api['interference'](frame_body,seating_copy)/.001
    report['USB_opening_mm']={'width':9.6,'height':3.8,'corner_radius':1.8,'clearance_each_side':.3}
    report['frame_mount_holes_mm']=R.FRAME_HOLES
    report['lid_mount_holes_mm']=R.LID_HOLES
    report['TFT_nut_pockets_mm']={'across_flats':4.2,'depth':1.75,'screws':'M2 x 6 with M2 hex nuts'}
    report['assembly_rigid_groups']=[{'name':g.name,'occurrence_count':g.occurrences.count,'component':comp.name} for comp in (design.rootComponent,occ.component) for g in comp.rigidGroups]
    report['assembly_grounded']=occ.isGrounded
    report['native_features']={}
    for child in occ.childOccurrences:
        if child.component.name not in printed:continue
        comp=child.component
        features=list(comp.features.extrudeFeatures)+list(comp.features.combineFeatures)+list(comp.features.loftFeatures)+list(comp.features.filletFeatures)
        errors=[{'feature':f.name,'message':f.errorOrWarningMessage} for f in features if f.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
        report['native_features'][comp.name]={'sketches':comp.sketches.count,'extrudes':comp.features.extrudeFeatures.count,'combines':comp.features.combineFeatures.count,'lofts':comp.features.loftFeatures.count,'fillets':comp.features.filletFeatures.count,'warnings_or_errors':errors}
    report['assumptions']=['TFT PCB thickness 1.6mm + LCD 1.5mm remain dimensional references until measured.',
                           'TFT header envelope assumed 6mm behind PCB; wiring requires physical fit check.',
                           'M2 plastic pilot holes are 1.7mm; fit depends on print material and settings.']
    return report

def finish(design,assembly_occ,R,api):
    root=design.rootComponent
    frame=next(o.component for o in assembly_occ.childOccurrences if o.component.name.startswith('01_KHUNG_HA_ESP'))
    for i,shape in enumerate(R.nut_pockets()):
        label='TFT_M2_nut_pocket_'+str(i+1)
        if not any(f.name==label for f in frame.features.extrudeFeatures):
            extrude(frame,shape,label,frame.bRepBodies.item(0))
    esp=next(o for o in assembly_occ.childOccurrences if o.component.name.startswith('REF_ESP32_ACTUAL_STEP'))
    esp.transform2=transform_from_mm(R.ESP_TRANSFORM)
    if design.snapshots.hasPendingSnapshot:design.snapshots.add()
    report=inspect(design,assembly_occ,R,api)
    group_name=getattr(R,'GROUP_NAME','LAP_RAP_CO_DINH_KHUNG_CASE')
    if not any(g.name==group_name for comp in (root,assembly_occ.component) for g in comp.rigidGroups):
        items=adsk.core.ObjectCollection.create()
        for child in assembly_occ.childOccurrences:items.add(child)
        group=root.rigidGroups.add(items,True)
        if not group:raise RuntimeError('Unable to create assembly rigid group')
        group.name=group_name
    assembly_occ.isGrounded=True
    for occ in root.occurrences:
        if occ.component.name=='KHUNG_GA_PCB_TFT_ESP32_NATIVE':occ.isLightBulbOn=False
    assembly_occ.isLightBulbOn=True
    design.activateRootComponent()
    return inspect(design,assembly_occ,R,api)

def present(design,occ,args):
    mode=args.get('view','assembled')
    for child in occ.childOccurrences:
        child.isLightBulbOn=(child.component.name.startswith('04_NAP_SAU') if mode=='cover' else
                            not (mode=='inside' and child.component.name.startswith('04_NAP_SAU')))
    app=adsk.core.Application.get();view=app.activeViewport;cam=view.camera
    app.userInterface.activeSelections.clear()
    target=adsk.core.Point3D.create(1.054,3.6575,-.415)
    if mode=='inside':
        eye=adsk.core.Point3D.create(9,-9,-16)
        up=adsk.core.Vector3D.create(0,1,0)
    else:
        eye=adsk.core.Point3D.create(11,-15,15)
        up=adsk.core.Vector3D.create(0,0,1)
    cam.eye=eye;cam.target=target;cam.upVector=up
    cam.isFitView=True;cam.isSmoothTransition=False
    view.camera=cam;view.refresh()
    if args.get('image_path'):
        view.saveAsImageFile(args['image_path'],1600,1200)
    return {'view':mode}

def export(design,occ,args):
    out=Path(args['output_dir']);out.mkdir(parents=True,exist_ok=True)
    manager=design.exportManager;files=[]
    archive=out/args.get('archive_name','flip_clock_case_native.f3d')
    options=manager.createFusionArchiveExportOptions(str(archive),occ.component)
    if not manager.execute(options):raise RuntimeError('Native archive export failed')
    files.append(str(archive))
    for child in occ.component.occurrences:
        if not child.component.name.startswith(('01_','02_','03_','04_')):continue
        path=out/(child.component.name.partition(' (')[0]+'.stl')
        options=manager.createSTLExportOptions(child.component.bRepBodies.item(0),str(path))
        options.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        options.sendToPrintUtility=False
        if not manager.execute(options):raise RuntimeError('STL export failed: '+str(path))
        files.append(str(path))
    return {'files':files}

def run(design,args,api):
    R=load_recipe();rec=R.recipe();root=design.rootComponent
    existing=next((o for o in root.occurrences if o.component.name==NAME),None)
    if args['action']=='debug_case':
        if not existing:raise RuntimeError('Case assembly does not exist')
        c=next(o.component for o in existing.component.occurrences if o.component.name.startswith('03_THAN_CASE'))
        return {'bodies':[api['describe_body'](b) for b in c.bRepBodies],
                'planes':[{'name':p.name,'origin':p.geometry.origin.asArray(),'normal':p.geometry.normal.asArray()} for p in c.constructionPlanes],
                'sketches':[{'name':s.name,'transform':s.transform.asArray(),'bounds_mm':api['describe_body'](c.bRepBodies.item(0))['bounds_mm']} for s in c.sketches if s.name.startswith('Window_reveal')],
                'top_edges':[{'bounds_mm':[v*10 for v in (e.boundingBox.minPoint.x,e.boundingBox.minPoint.y,e.boundingBox.minPoint.z,e.boundingBox.maxPoint.x,e.boundingBox.maxPoint.y,e.boundingBox.maxPoint.z)],'type':e.geometry.objectType} for e in c.bRepBodies.item(0).edges if abs(e.boundingBox.minPoint.z-.53)<1e-6 and abs(e.boundingBox.maxPoint.z-.53)<1e-6]}
    if args['action']=='resume_case':
        if not existing:raise RuntimeError('Case assembly does not exist')
        assembly=existing.component
        case=next(o.component for o in assembly.occurrences if o.component.name.startswith('03_THAN_CASE'))
        if rec['case'].get('window_loft') and case.features.filletFeatures.count==0:
            soften_window_rim(case,rec['case']['window_rim_fillet'])
        api['set_color'](design,case.bRepBodies.item(0),'Case_matte',155,159,164)
        if not any(o.component.name.startswith('04_NAP_SAU') for o in assembly.occurrences):
            create_lid(design,assembly,rec['lid'],api)
        add_references(design,assembly,R,api)
        report=finish(design,existing,R,api)
        if args.get('report_path'):Path(args['report_path']).write_text(json.dumps(report,indent=2),encoding='utf-8')
        adsk.core.Application.get().activeViewport.fit()
        return report
    if args['action'] in ('finish_case','present_case','export_case'):
        if not existing:raise RuntimeError('Case assembly does not exist')
        if args['action']=='present_case':return present(design,existing,args)
        if args['action']=='export_case':return export(design,existing,args)
        report=finish(design,existing,R,api)
        if args.get('report_path'):Path(args['report_path']).write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report
    if args['action']=='inspect_case':
        if not existing:raise RuntimeError('Case assembly does not exist')
        report=inspect(design,existing,R,api)
        if args.get('report_path'):Path(args['report_path']).write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report
    if existing:raise RuntimeError('Case already exists; inspect rather than create duplicates')
    previous=next((o for o in root.occurrences if o.component.name=='KHUNG_GA_PCB_TFT_ESP32_NATIVE'),None)
    assembly=api['component'](root,NAME)
    for key,name,color in [('frame','01_KHUNG_HA_ESP',(50,140,164)),
                           ('keeper','02_NEP_ESP',(230,145,65))]:
        comp=api['component'](assembly,name)
        for i,s in enumerate(rec[key]['parts']):extrude(comp,s,key+'_part_'+str(i+1))
        body=api['join'](comp,name)
        nut_index=0
        for i,s in enumerate(rec[key]['cuts']):
            label=key+'_cut_'+str(i+1)
            if key=='frame' and s['kind']=='hex':
                nut_index+=1;label='TFT_M2_nut_pocket_'+str(nut_index)
            extrude(comp,s,label,body)
        api['set_color'](design,comp.bRepBodies.item(0),name+'_color',*color)
    case=api['component'](assembly,'03_THAN_CASE')
    body=extrude(case,rec['case']['outer'],'Case_outer_R3')
    extrude(case,rec['case']['cavity'],'Case_cavity_wall_2mm',body)
    for i,s in enumerate(rec['case']['bosses']):extrude(case,s,'Case_mount_boss_'+str(i+1))
    body=api['join'](case,'THAN_CASE_LIEN_KHOI')
    for i,s in enumerate(rec['case']['cuts']):extrude(case,s,'Case_cut_'+str(i+1),body)
    if rec['case'].get('window_loft'):
        window_reveal(case,body,rec['case']['window_loft'],rec['case']['window_rim_fillet'])
    api['set_color'](design,case.bRepBodies.item(0),'Case_matte',155,159,164)
    create_lid(design,assembly,rec['lid'],api)
    add_references(design,assembly,R,api)
    app=adsk.core.Application.get()
    assembly_occ=next(o for o in root.occurrences if o.component==assembly)
    report=finish(design,assembly_occ,R,api)
    if args.get('report_path'):Path(args['report_path']).write_text(json.dumps(report,indent=2),encoding='utf-8')
    app.activeViewport.fit();app.activeViewport.refresh()
    return report
