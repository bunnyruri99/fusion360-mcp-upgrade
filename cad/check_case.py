"""Verify the shared case recipe against actual ESP STEP before native construction."""
from pathlib import Path
import importlib.util
import json
import math
import cadquery as cq
import trimesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad'/'case_native'
OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('case_recipe',ROOT/'addin'/'fusion360_mcp_bridge'/'case_recipe.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)

def shape(s):
    p=s['p']; k=s['kind']
    if k=='box':
        x,y,z,w,l,h=p
        return cq.Workplane('XY').box(w,l,h,centered=(False,False,False)).translate((x,y,z)).val()
    if k=='circle':
        x,y,z,r,h=p
        return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z)).val()
    if k=='hex':
        x,y,z,af,h=p
        radius=af/math.sqrt(3)
        pts=[(x+radius*math.cos(i*math.pi/3),y+radius*math.sin(i*math.pi/3)) for i in range(6)]
        return cq.Workplane('XY').polyline(pts).close().extrude(h).translate((0,0,z)).val()
    x,y,z,w,l,h,r=p
    # Rounded rectangles are extruded from exact arcs in the native builder.
    if k=='rounded_xz':
        q=cq.Workplane('XY').center(x+w/2,y+l/2).rect(w,l).extrude(h).edges('|Z').fillet(r).val()
        # Initial (X,Y,Z) -> final (X,Z,Y), with positive depth along global Y.
        return q.rotate((0,0,0),(1,0,0),90).translate((0,z+h,0))
    return cq.Workplane('XY').center(x+w/2,y+l/2).rect(w,l).extrude(h).edges('|Z').fillet(r).translate((0,0,z)).val()

def fused(parts):
    items=[shape(s) for s in parts]
    return items[0].fuse(*items[1:]).clean()

rec=R.recipe()
parts={}
for key in ('frame','keeper'):
    s=fused(rec[key]['parts'])
    parts[key]=s.cut(*[shape(c) for c in rec[key]['cuts']]).clean()
parts['case']=shape(rec['case']['outer']).cut(shape(rec['case']['cavity'])).clean()
parts['case']=parts['case'].fuse(*[shape(b) for b in rec['case']['bosses']]).clean()
parts['case']=parts['case'].cut(*[shape(c) for c in rec['case']['cuts']]).clean()
lip=shape(rec['lid']['lip']).cut(shape(rec['lid']['lip_inside'])).clean()
parts['lid']=shape(rec['lid']['outer']).fuse(lip).clean()
parts['lid']=parts['lid'].cut(*[shape(c) for c in rec['lid']['cuts']]).clean()

source=cq.importers.importStep(R.ESP_SOURCE).solids().vals()
# Rotation from STEP axes into portrait TFT axes, USB directed towards -Y.
esp_parts=[s.rotate((0,0,0),(1,0,0),-90).rotate((0,0,0),(0,0,1),180).translate((-9.3905831467846,16.6736646226333,-3)) for s in source]
esp=cq.Compound.makeCompound(esp_parts)
pcb=cq.Workplane('XY').box(21.08,73.15,1.6,centered=False).val()
pcb=pcb.cut(*[cq.Workplane('XY').center(x,y).circle(1.25).extrude(2).val() for x,y in R.TFT_HOLES])
lcd=shape(R.box(1.98,8.4,1.6,17,60.55,1.5))
header=shape(R.box(.33,70.25,-6,20.42,2.5,6))
report={}
for name,s in parts.items():
    assert s.isValid() and len(s.Solids())==1,(name,'not a valid single solid',len(s.Solids()))
    b=s.BoundingBox()
    report[name]={'volume_mm3':s.Volume(),'solid_count':len(s.Solids()),
                  'bounds_mm':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]}
    cq.exporters.export(s,str(OUT/f'check_{name}.step'))
    cq.exporters.export(s,str(OUT/f'check_{name}.stl'),tolerance=.06,angularTolerance=.15)
    m=trimesh.load(str(OUT/f'check_{name}.stl'),force='mesh')
    assert m.is_watertight and len(m.split())==1,(name,'STL disconnected')
for a in parts:
    for b in list(parts)+['ESP_actual_STEP','TFT_PCB_proxy','LCD_proxy','header_proxy']:
        if b in parts and list(parts).index(b)<=list(parts).index(a):continue
        other=parts.get(b,{'ESP_actual_STEP':esp,'TFT_PCB_proxy':pcb,'LCD_proxy':lcd,'header_proxy':header}.get(b))
        v=parts[a].intersect(other).Volume()
        report[a+'_'+b+'_overlap_mm3']=round(v,8)
        if v>1e-5 and b=='ESP_actual_STEP':
            for i,s in enumerate(esp_parts):
                c=parts[a].intersect(s)
                if c.Volume()>1e-5: print('ESP CLASH',a,i,c.Volume(),c.BoundingBox().__dict__,flush=True)
        assert v<1e-5,(a,b,v)
report['USB_aperture_mm']={'width':9.6,'height':3.8,'corner_radius':1.8,'radial_clearance':.3}
report['USB_front_recess_mm']=R.USB_FRONT_Y-R.CASE_OUT[1]
report['PCB_gap_mm']=6.2
(OUT/'recipe_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
