"""Geometric verification of the M3 assembly using the user's 61-solid ESP STEP."""
from pathlib import Path
import importlib.util
import json
import math
import cadquery as cq
import trimesh
import argparse
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

parser=argparse.ArgumentParser();parser.add_argument('--native',action='store_true');args=parser.parse_args()

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad'/'case_v3';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('case_v3_recipe',ROOT/'addin'/'fusion360_mcp_bridge'/'case_v3_recipe.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)

def precise_volume(s):
    # Adaptive integration is necessary for Fusion's exported B-spline loft faces.
    props=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,props,1e-9,True,False)
    return props.Mass()

def shape(s):
    k=s['kind'];p=s['p']
    if k=='box':
        x,y,z,w,l,h=p
        return cq.Workplane('XY').box(w,l,h,centered=False).translate((x,y,z)).val()
    if k=='circle':
        x,y,z,r,h=p
        return cq.Solid.makeCylinder(r,h,(x,y,z),(0,0,1))
    if k=='circle_x':
        x,y,z,r,h=p
        return cq.Solid.makeCylinder(r,h,(x,y,z),(1,0,0))
    if k=='cone_x':
        x,y,z,r1,r2,h=p
        return cq.Solid.makeCone(r1,r2,h,(x,y,z),(1,0,0))
    if k=='hex':
        x,y,z,af,h=p;r=af/math.sqrt(3)
        points=[(x+r*math.cos(i*math.pi/3),y+r*math.sin(i*math.pi/3)) for i in range(6)]
        return cq.Workplane('XY').polyline(points).close().extrude(h).translate((0,0,z)).val()
    x,y,z,w,l,h,r=p
    s=cq.Workplane('XY').center(x+w/2,y+l/2).rect(w,l).extrude(h).edges('|Z').fillet(r).val()
    if k=='rounded_xz':return s.rotate((0,0,0),(1,0,0),90).translate((0,z+h,0))
    return s.translate((0,0,z))

def fused(items):
    ss=[shape(s) for s in items]
    return ss[0].fuse(*ss[1:]).clean()

def rounded_wire(p):
    x,y,z,w,l,r=p
    s=cq.Workplane('XY').center(x+w/2,y+l/2).rect(w,l).extrude(1).edges('|Z').fillet(r)
    return s.faces('<Z').wires().val().translate((0,0,z))

def hardware_body(item,insert=False):
    start=cq.Vector(*item['start']);d=cq.Vector(*item['direction']);h=item['length']
    if insert:
        return cq.Solid.makeCylinder(item['radius'],h,start,d).cut(cq.Solid.makeCylinder(item['bore'],h,start,d))
    if item['head']=='countersunk':
        head=cq.Solid.makeCone(item['head_radius'],item['radius'],item['head_height'],start,d)
        shaft=cq.Solid.makeCylinder(item['radius'],h-item['head_height'],start+d.multiply(item['head_height']),d)
    else:
        head=cq.Solid.makeCylinder(item['head_radius'],item['head_height'],start-d.multiply(item['head_height']),d)
        shaft=cq.Solid.makeCylinder(item['radius'],h,start,d)
    return head.fuse(shaft).clean()

rec=R.recipe();parts={}
for name in ('frame','keeper'):
    parts[name]=fused(rec[name]['parts']).cut(*[shape(c) for c in rec[name]['cuts']]).clean()
    assert parts[name].isValid() and len(parts[name].Solids())==1,(name,'not one valid solid')
    print(name,'one connected solid',flush=True)
parts['case']=shape(rec['case']['outer']).cut(shape(rec['case']['cavity'])).clean()
parts['case']=parts['case'].fuse(*[shape(s) for s in rec['case']['bosses']]).clean()
parts['case']=parts['case'].cut(*[shape(s) for s in rec['case']['cuts']]).clean()
parts['case']=parts['case'].cut(cq.Solid.makeLoft([rounded_wire(p) for p in R.WINDOW_LOFT],ruled=True)).clean()
edges=[]
for e in parts['case'].Edges():
    b=e.BoundingBox()
    if abs(b.zmin-R.CASE_FRONT)<1e-5 and abs(b.zmax-R.CASE_FRONT)<1e-5 and b.xmin>0 and b.xmax<21.08 and b.ymin>10 and b.ymax<72:edges.append(e)
assert len(edges)==8,len(edges)
parts['case']=parts['case'].fillet(R.WINDOW_RIM_FILLET,edges).clean()
lip=shape(rec['lid']['lip']).cut(shape(rec['lid']['lip_inside']))
parts['lid']=shape(rec['lid']['outer']).fuse(lip,*[shape(s) for s in rec['lid']['parts']]).clean()
parts['lid']=parts['lid'].cut(*[shape(s) for s in rec['lid']['cuts']]).clean()
if args.native:
    filenames={'frame':'01_KHUNG_HA_ESP','keeper':'02_NEP_ESP','case':'03_THAN_CASE','lid':'04_NAP_SAU'}
    parts={key:cq.importers.importStep(str(OUT/'native_exports'/('native_'+label+'.step'))).solids().val() for key,label in filenames.items()}

source=cq.importers.importStep(R.ESP_SOURCE).solids().vals()
esp_parts=[s.rotate((0,0,0),(1,0,0),-90).rotate((0,0,0),(0,0,1),180).translate((R.ESP_TRANSFORM[3],R.ESP_TRANSFORM[7],R.ESP_TRANSFORM[11])) for s in source]
esp=cq.Compound.makeCompound(esp_parts)
pcb=shape(R.box(0,0,0,21.08,73.15,1.6)).cut(*[shape(R.cylinder(x,y,0,1.25,2)) for x,y in R.TFT_HOLES])
lcd=shape(R.box(1.98,8.4,1.6,17,60.55,1.5))
header=shape(R.box(.33,70.25,-6,20.42,2.5,6))
refs={'ESP_actual_STEP':esp,'TFT_PCB_proxy':pcb,'LCD_proxy':lcd,'header_proxy':header}
report={'printed_parts':{},'intersections_mm3':{},'hardware_clearances_mm3':{}}
for name,s in parts.items():
    assert s.isValid() and len(s.Solids())==1,(name,'not one valid solid')
    b=s.BoundingBox();report['printed_parts'][name]={'volume_mm3':precise_volume(s),'bounds_mm':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]}
    cq.exporters.export(s,str(OUT/f'check_{name}.step'))
    cq.exporters.export(s,str(OUT/f'check_{name}.stl'),tolerance=.06,angularTolerance=.15)
    mesh=trimesh.load(str(OUT/f'check_{name}.stl'),force='mesh')
    assert mesh.is_watertight and len(mesh.split())==1,(name,'open or disconnected mesh')
    if args.native:
        delivered=trimesh.load(str(OUT/'deliverables'/(filenames[name]+'.stl')),force='mesh')
        assert delivered.is_watertight and delivered.is_volume and len(delivered.split())==1,(name,'Fusion STL is not one closed solid')
        relative=abs(delivered.volume-precise_volume(s))/precise_volume(s)
        assert relative<.005,(name,'Fusion mesh volume differs',relative)
        report['printed_parts'][name]['Fusion_STL_volume_error_fraction']=relative
    for other,t in list(parts.items())+list(refs.items()):
        if other==name or (other in parts and list(parts).index(other)<list(parts).index(name)):continue
        v=s.intersect(t).Volume();report['intersections_mm3'][name+' / '+other]=round(v,8)
        assert v<1e-5,(name,other,v)
print('Final geometry: four connected solids, no intersections',flush=True)

ins,scr=R.hardware()
insert_shapes={i['name']:hardware_body(i,True) for i in ins}
screw_shapes={i['name']:hardware_body(i) for i in scr}
for n,s in list(insert_shapes.items())+list(screw_shapes.items()):
    # Insert knurls intentionally occupy plastic; screws must clear every printed part.
    targets=refs if n in insert_shapes else dict(parts,**refs)
    for other,t in targets.items():
        v=s.intersect(t).Volume();report['hardware_clearances_mm3'][n+' / '+other]=round(v,8)
        assert v<1e-5,(n,other,v)
for n,s in screw_shapes.items():
    for other,t in insert_shapes.items():
        v=s.intersect(t).Volume();assert v<1e-5,(n,other,v)
print('12 M3 screws and 12 inserts: clear electronics, screw envelopes clear plastic',flush=True)

tft_hw=[]
for x,y in R.TFT_HOLES:
    tft_hw += [shape(R.cylinder(x,y,1.6,1.9,1.2)),shape(R.cylinder(x,y,-4.4,1,6)),shape({'kind':'hex','p':[x,y,-3.85,4,1.6]})]
keeper_screws=[s for n,s in screw_shapes.items() if n.startswith('NEP_')]
package=cq.Compound.makeCompound([parts['frame'],parts['keeper'],pcb,lcd,header]+esp_parts+tft_hw+list(insert_shapes.values())+keeper_screws)
motion=[]
for index in range(49):
    dz=-24+index*.5;v=package.translate((0,0,dz)).intersect(parts['case']).Volume()
    motion.append({'Z_offset_mm':dz,'intersection_mm3':round(v,8)})
    assert v<1e-5,('module insertion blocked',dz,v)
print('Module insertion: 49 positions, no interference',flush=True)
for index in range(25):
    dz=-12+index*.5
    for target,t in [('assembled module',package),('case',parts['case'])]:
        v=parts['lid'].translate((0,0,dz)).intersect(t).Volume()
        assert v<1e-5,('lid insertion blocked',target,dz,v)
print('Lid insertion: 25 positions, no interference',flush=True)
report.update(module_insertion_samples=motion,lid_insertion_samples=25,M3_screw_count=len(scr),M3_insert_count=len(ins),
              insert_mm={'outer_diameter':4.6,'length':4,'pilot_diameter':4,'pocket_depth':5},case_outer_mm=[28.98,78.55,20.9])
report['geometry_source']='Fusion native STEP exports' if args.native else 'Independent CadQuery recipe'
(OUT/('native_exports_verification.json' if args.native else 'recipe_verification.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['printed_parts'],indent=2),flush=True)
