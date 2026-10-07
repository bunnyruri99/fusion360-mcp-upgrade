"""Build the M3 revision in the active Fusion document, with visible metal inserts."""
import importlib.util
import json
from pathlib import Path
import adsk.core
import adsk.fusion

NAME='FLIP_CLOCK_CASE_V3_M3_INSERTS_NATIVE'

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def hardware_components(design,assembly,R,api):
    mgr=adsk.fusion.TemporaryBRepManager.get()
    inserts,screws=R.hardware()
    def point(start,direction,distance=0):
        return adsk.core.Point3D.create(*[(a+b*distance)/10 for a,b in zip(start,direction)])
    def cylinder(start,direction,r,h,offset=0,r2=None):
        return mgr.createCylinderOrCone(point(start,direction,offset),r/10,
                                       point(start,direction,offset+h),(r if r2 is None else r2)/10)
    for name,items,is_insert,color in [('HW_12_M3_HEAT_SET_INSERTS',inserts,True,(207,159,49)),
                                       ('HW_12_M3_FASTENER_ENVELOPES',screws,False,(92,98,105))]:
        if any(o.component.name.startswith(name) for o in assembly.occurrences):continue
        comp=api['component'](assembly,name)
        bf=comp.features.baseFeatures.add();bf.name='M3_reference_envelopes_no_thread_detail';bf.startEdit()
        try:
            for item in items:
                start,d=item['start'],item['direction'];h=item['length']
                if is_insert:
                    solid=cylinder(start,d,item['radius'],h)
                    if not mgr.booleanOperation(solid,cylinder(start,d,item['bore'],h),adsk.fusion.BooleanTypes.DifferenceBooleanType):
                        raise RuntimeError('Insert bore subtraction failed')
                else:
                    hr,hh=item['head_radius'],item['head_height']
                    if item['head']=='countersunk':
                        solid=cylinder(start,d,hr,hh,r2=item['radius'])
                        shaft=cylinder(start,d,item['radius'],h-hh,offset=hh)
                    else:
                        solid=cylinder(start,d,hr,hh,offset=-hh)
                        shaft=cylinder(start,d,item['radius'],h)
                    if not mgr.booleanOperation(solid,shaft,adsk.fusion.BooleanTypes.UnionBooleanType):
                        raise RuntimeError('Screw union failed')
                body=comp.bRepBodies.add(solid,bf);body.name=item['name']
                body.attributes.add('hardware','specification','M3 brass heat-set OD4.6 L4' if is_insert else item['name'])
        finally:bf.finishEdit()
        for body in comp.bRepBodies:api['set_color'](design,body,name+'_color',*color)

def run(design,args,api):
    N=load('case_common_v3','case_native.py');R=load('case_recipe_v3','case_v3_recipe.py')
    N.NAME=NAME;N.load_recipe=lambda:R;R.GROUP_NAME='LAP_RAP_M3_CO_DINH_DOC_LAP'
    original_finish=N.finish
    def finish(d,occ,r,a):
        hardware_components(d,occ.component,r,a)
        return original_finish(d,occ,r,a)
    N.finish=finish
    original_inspect=N.inspect
    def inspect(d,occ,r,a):
        report=original_inspect(d,occ,r,a)
        groups={o.component.name:N.world_bodies(o) for o in occ.childOccurrences}
        printed=[n for n in groups if n.startswith(('01_','02_','03_','04_'))]
        references=[n for n in groups if n.startswith('REF_')]
        report['hardware_components']={n:len(bs) for n,bs in groups.items() if n.startswith('HW_')}
        report['hardware_intersections_mm3']={}
        for name,bodies in groups.items():
            if not name.startswith('HW_'):continue
            targets=references+(printed if name.startswith('HW_12_M3_FASTENER') else [])
            for target in targets:
                v=sum(a['interference'](s,t) for _,s in bodies for _,t in groups[target])
                report['hardware_intersections_mm3'][name+' / '+target]=round(v,8)
                if v>1e-4:raise RuntimeError('Hardware collision '+name+' / '+target+': '+str(v))
        if sum(report['hardware_components'].values())!=24:raise RuntimeError('Expected 12 M3 inserts and 12 screw envelopes')
        report['revision_changes']={'frame_to_case':'4 independent DIN7991 countersunk M3x8 screws through side walls into frame heat-set inserts',
            'ESP_keeper':'4 side-entry ISO7380 M3x6 screws into frame inserts',
            'rear_lid':'4 ISO7380 M3x6 screws into frame inserts; lid removal leaves frame fixed to case',
            'TFT':'2 M2x6 with captive M2 hex nuts, unchanged',
            'heat_set_inserts':{'count':12,'OD_mm':4.6,'length_mm':4,'pilot_diameter_mm':4,'pilot_depth_mm':5},
            'case_width_mm':28.98,'case_depth_increase_mm':2,'PCB_seating_gap_mm':0,
            'side_clamp_contacts':'Four Ø7.6 x0.6 internal case lands touch the frame boss faces',
            'assembly_path':'Straight rear insertion; no fixed case posts across path; side screws fitted after insertion'}
        report['assumptions']=[s for s in report['assumptions'] if not s.startswith('M2 plastic')]
        report['assumptions']+=['M3 insert outer knurls intentionally press into the plastic pilot hole; hardware envelopes omit thread and knurl details.',
                                'Insert specification OD4.6 x L4 agreed by user; pilot Ø4 x depth5 requires printed fit calibration.']
        return report
    N.inspect=inspect
    original_present=N.present
    def present(d,occ,options):
        mode=options.get('view','assembled')
        for child in occ.childOccurrences:
            if child.component.name.startswith('HW_12_M3_FASTENER'):
                for body in child.component.bRepBodies:
                    body.isVisible=not (mode=='inside' and body.name.startswith('LID_'))
        if options.get('view')!='frame':return original_present(d,occ,options)
        settings=dict(options);settings['view']='inside';settings.pop('image_path',None)
        original_present(d,occ,settings)
        for child in occ.childOccurrences:
            child.isLightBulbOn=child.component.name.startswith(('01_','02_','HW_12_M3_HEAT_SET'))
        viewport=adsk.core.Application.get().activeViewport;viewport.fit();viewport.refresh()
        if options.get('image_path'):viewport.saveAsImageFile(options['image_path'],1600,1200)
        return {'view':'frame'}
    N.present=present
    original_export=N.export
    def export(d,occ,options):
        result=original_export(d,occ,options)
        if options.get('verification_dir'):
            out=Path(options['verification_dir']);out.mkdir(parents=True,exist_ok=True)
            result['verification_STEP_files']=[]
            for child in occ.component.occurrences:
                if not child.component.name.startswith(('01_','02_','03_','04_')):continue
                path=out/('native_'+child.component.name.partition(' (')[0]+'.step')
                step=d.exportManager.createSTEPExportOptions(str(path),child.component)
                if not d.exportManager.execute(step):raise RuntimeError('Native verification STEP export failed')
                result['verification_STEP_files'].append(str(path))
        return result
    N.export=export
    translated=dict(args);translated['action']=args['action'].replace('_case_v3','_case')
    if translated['action']=='reinforce_case':
        occ=next(o for o in design.rootComponent.occurrences if o.component.name==NAME)
        case=next(o.component for o in occ.childOccurrences if o.component.name.startswith('03_THAN_CASE'))
        if not any(f.name=='M3_CONTACT_PADS_join' for f in case.features.combineFeatures):
            for i,s in enumerate(R.contact_pads()):N.extrude(case,s,'Case_M3_contact_pad_'+str(i+1))
            body=api['join'](case,'M3_CONTACT_PADS')
            for y in (33,58):N.extrude(case,R.circle_x(-4.05,y,-5,1.7,29.18),'M3_pad_clearance_'+str(y),body)
            api['set_color'](design,body,'Case_matte',155,159,164)
        result=inspect(design,occ,R,api)
        if args.get('report_path'):Path(args['report_path']).write_text(json.dumps(result,indent=2),encoding='utf-8')
        return result
    if translated['action']=='export_case':translated.setdefault('archive_name','flip_clock_case_v3_M3_inserts.f3d')
    result=N.run(design,translated,api)
    if translated['action'] in ('build_case','finish_case','resume_case'):
        for occ in design.rootComponent.occurrences:
            if occ.component.name in ('FLIP_CLOCK_CASE_LAP_RAP_NATIVE','FLIP_CLOCK_CASE_V2_SLIM_NATIVE'):occ.isLightBulbOn=False
    if translated['action'] in ('inspect_case','build_case','finish_case','resume_case') and args.get('report_path'):
        Path(args['report_path']).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
