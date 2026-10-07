"""Verify delivered Fusion meshes and the four case-to-frame clamp contact faces."""
from pathlib import Path
import json
import cadquery as cq
import trimesh
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

out=Path(__file__).resolve().parent/'case_v3'
native=json.loads((out/'fusion_case_verification.json').read_text())
report={'STL_parts':{},'case_frame_contact_area_mm2':{}}
step_volumes={}
for name,solid in native['printed_parts'].items():
    label=name.partition(' (')[0];path=out/'deliverables'/(label+'.stl')
    mesh=trimesh.load(str(path),force='mesh')
    assert mesh.is_watertight and mesh.is_volume and len(mesh.split())==1,label
    relative=abs(mesh.volume-solid['volume_mm3'])/solid['volume_mm3']
    assert relative<.005,(label,relative)
    bounds=mesh.bounds.flatten().tolist()
    assert max(abs(a-b) for a,b in zip(bounds,solid['bounds_mm']))<.02,(label,bounds)
    step=cq.importers.importStep(str(out/'native_exports'/('native_'+label+'.step'))).solids().val()
    props=GProp_GProps();BRepGProp.VolumeProperties_s(step.wrapped,props,1e-9,True,False);accurate=props.Mass()
    step_relative=abs(mesh.volume-accurate)/accurate;assert step_relative<.005,(label,step_relative)
    step_volumes[label]=accurate
    report['STL_parts'][label]={'closed':True,'connected_components':1,'volume_mm3':mesh.volume,'native_STEP_volume_mm3':accurate,'volume_error_fraction':step_relative,'bytes':path.stat().st_size}
frame=cq.importers.importStep(str(out/'native_exports'/'native_01_KHUNG_HA_ESP.step')).solids().val()
case=cq.importers.importStep(str(out/'native_exports'/'native_03_THAN_CASE.step')).solids().val()
for side,dx in [('left',-.001),('right',.001)]:
    contact=frame.translate((dx,0,0)).intersect(case).Volume()/.001
    assert contact>60,(side,contact)
    report['case_frame_contact_area_mm2'][side]=contact
(out/'delivery_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
verification=out/'native_exports_verification.json'
if verification.exists():
    data=json.loads(verification.read_text())
    labels={'frame':'01_KHUNG_HA_ESP','keeper':'02_NEP_ESP','case':'03_THAN_CASE','lid':'04_NAP_SAU'}
    for key,label in labels.items():data['printed_parts'][key]['volume_mm3']=step_volumes[label]
    data['volume_calculation']='Adaptive integration, epsilon 1e-9, for exported B-spline surfaces'
    verification.write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
