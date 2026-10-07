"""Check final geometry and the rear assembly motion against the actual ESP STEP."""
from pathlib import Path
import importlib.util
import json
import math
import cadquery as cq
import trimesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad'/'case_v2';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('case_v2_recipe',ROOT/'addin'/'fusion360_mcp_bridge'/'case_v2_recipe.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)

def shape(s):
    k=s['kind'];p=s['p']
    if k=='box':
        x,y,z,w,l,h=p
        return cq.Workplane('XY').box(w,l,h,centered=False).translate((x,y,z)).val()
    if k=='circle':
        x,y,z,r,h=p
        return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z)).val()
    if k=='hex':
        x,y,z,af,h=p;r=af/math.sqrt(3)
        points=[(x+r*math.cos(i*math.pi/3),y+r*math.sin(i*math.pi/3)) for i in range(6)]
        return cq.Workplane('XY').polyline(points).close().extrude(h).translate((0,0,z)).val()
    x,y,z,w,l,h,r=p
    s=cq.Workplane('XY').center(x+w/2,y+l/2).rect(w,l).extrude(h).edges('|Z').fillet(r).val()
    if k=='rounded_xz':return s.rotate((0,0,0),(1,0,0),90).translate((0,z+h,0))
    return s.translate((0,0,z))

def fused(items):
    shapes=[shape(s) for s in items]
    return shapes[0].fuse(*shapes[1:]).clean()

def rounded_wire(p):
    x,y,z,w,l,r=p
    s=cq.Workplane('XY').center(x+w/2,y+l/2).rect(w,l).extrude(1).edges('|Z').fillet(r)
    return s.faces('<Z').wires().val().translate((0,0,z))

rec=R.recipe();parts={}
for name in ('frame','keeper'):
    parts[name]=fused(rec[name]['parts']).cut(*[shape(c) for c in rec[name]['cuts']]).clean()
parts['case']=shape(rec['case']['outer']).cut(shape(rec['case']['cavity'])).clean()
parts['case']=parts['case'].fuse(*[shape(s) for s in rec['case']['bosses']]).clean()
parts['case']=parts['case'].cut(*[shape(s) for s in rec['case']['cuts']]).clean()
reveal=cq.Solid.makeLoft([rounded_wire(p) for p in R.WINDOW_LOFT],ruled=True)
parts['case']=parts['case'].cut(reveal).clean()
edges=[]
for e in parts['case'].Edges():
    b=e.BoundingBox()
    if abs(b.zmin-5.3)<1e-5 and abs(b.zmax-5.3)<1e-5 and b.xmin>0 and b.xmax<21.08 and b.ymin>10 and b.ymax<72:
        edges.append(e)
assert len(edges)==8,len(edges)
parts['case']=parts['case'].fillet(R.WINDOW_RIM_FILLET,edges).clean()
lip=shape(rec['lid']['lip']).cut(shape(rec['lid']['lip_inside']))
parts['lid']=shape(rec['lid']['outer']).fuse(lip,*[shape(s) for s in rec['lid']['parts']]).clean()
parts['lid']=parts['lid'].cut(*[shape(s) for s in rec['lid']['cuts']]).clean()

source=cq.importers.importStep(R.ESP_SOURCE).solids().vals()
esp_parts=[s.rotate((0,0,0),(1,0,0),-90).rotate((0,0,0),(0,0,1),180).translate((-9.3905831467846,16.6736646226333,-3)) for s in source]
esp=cq.Compound.makeCompound(esp_parts)
pcb=shape(R.box(0,0,0,21.08,73.15,1.6))
pcb=pcb.cut(*[shape(R.cylinder(x,y,0,1.25,2)) for x,y in R.TFT_HOLES])
lcd=shape(R.box(1.98,8.4,1.6,17,60.55,1.5))
header=shape(R.box(.33,70.25,-6,20.42,2.5,6))
references={'ESP_actual_STEP':esp,'TFT_PCB_proxy':pcb,'LCD_proxy':lcd,'header_proxy':header}
report={'printed_parts':{},'intersections_mm3':{}}
for name,s in parts.items():
    assert s.isValid() and len(s.Solids())==1,(name,'not one valid solid')
    b=s.BoundingBox()
    report['printed_parts'][name]={'volume_mm3':s.Volume(),'bounds_mm':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]}
    cq.exporters.export(s,str(OUT/f'check_{name}.step'))
    cq.exporters.export(s,str(OUT/f'check_{name}.stl'),tolerance=.06,angularTolerance=.15)
    mesh=trimesh.load(str(OUT/f'check_{name}.stl'),force='mesh')
    assert mesh.is_watertight and len(mesh.split())==1,(name,'open or disconnected mesh')
    for other,t in list(parts.items())+list(references.items()):
        if other==name or (other in parts and list(parts).index(other)<list(parts).index(name)):continue
        v=s.intersect(t).Volume()
        report['intersections_mm3'][name+' / '+other]=round(v,8)
        assert v<1e-5,(name,other,v)
print('Final geometry: four connected solids, no intersections',flush=True)

hardware=[]
for x,y in R.TFT_HOLES:
    hardware += [shape(R.cylinder(x,y,1.6,1.9,1.2)),shape(R.cylinder(x,y,-4.4,1,6))]
    hardware.append(shape({'kind':'hex','p':[x,y,-3.85,4,1.6]}))
for x,y in R.ESP_HOLES:
    hardware += [shape(R.cylinder(x,y,-10.9,1.9,1.3)),shape(R.cylinder(x,y,-9.6,1,6))]
package=cq.Compound.makeCompound([parts['frame'],parts['keeper'],pcb,lcd,header]+esp_parts+hardware)
motion=[]
for index in range(49):
    dz=-24+index*.5
    v=package.translate((0,0,dz)).intersect(parts['case']).Volume()
    motion.append({'Z_offset_mm':dz,'intersection_mm3':round(v,8)})
    assert v<1e-5,('module insertion blocked',dz,v)
print('Module insertion: 49 positions, no interference',flush=True)
# Closing the lid must also clear the assembled electronics and frame.
for index in range(25):
    dz=-12+index*.5
    v=parts['lid'].translate((0,0,dz)).intersect(package).Volume()
    assert v<1e-5,('lid insertion blocked',dz,v)
print('Lid insertion: 25 positions, no interference',flush=True)
report['module_insertion_samples']=motion
report['lid_insertion_samples']=25
report['case_width_reduction_mm']=33.98-R.CASE_OUT[2]
(OUT/'recipe_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['printed_parts'],indent=2),flush=True)
