"""Apply the slimmer assembly as native Fusion history in the current document."""
import importlib.util
import json
from pathlib import Path

NAME='FLIP_CLOCK_CASE_V2_SLIM_NATIVE'

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def run(design,args,api):
    N=load('case_common_v2','case_native.py');R=load('case_recipe_v2','case_v2_recipe.py')
    N.NAME=NAME;N.load_recipe=lambda:R
    translated=dict(args);translated['action']=args['action'].replace('_case_v2','_case')
    if translated['action']=='export_case':translated.setdefault('archive_name','flip_clock_case_v2_slim.f3d')
    result=N.run(design,translated,api)
    root=design.rootComponent
    if translated['action'] in ('build_case','finish_case','resume_case'):
        for occ in root.occurrences:
            if occ.component.name=='FLIP_CLOCK_CASE_LAP_RAP_NATIVE':occ.isLightBulbOn=False
    if translated['action'] in ('inspect_case','build_case','finish_case','resume_case'):
        result['revision_changes']={'old_width_mm':33.98,'new_width_mm':R.CASE_OUT[2],
            'PCB_seating_gap_mm':0,'PCB_seat':'Continuous side ledges and end bridges',
            'frame_retention':'Rear lid ribs support frame against front PCB edge seats',
            'assembly_path':'Straight +Z insertion; frame grooves clear lid posts; USB lower edge completed by lid',
            'window_reveal':'Sloped loft with R0.35 entry rim; throat 0.2mm ahead of reference LCD'}
        if args.get('report_path'):Path(args['report_path']).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
