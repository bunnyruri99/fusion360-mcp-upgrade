from pathlib import Path
import json
import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
ESP = Path(r'C:\Users\HunterD\Downloads\esp32-c3-supermini-1.snapshot.2\ESP32-C3 supermini v5.step')

def describe(shape):
    b = shape.BoundingBox()
    return dict(volume=round(shape.Volume(), 4), valid=shape.isValid(),
                bounds=[round(v,4) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)],
                size=[round(v,4) for v in (b.xlen,b.ylen,b.zlen)])

esp = cq.importers.importStep(str(ESP))
print('ESP solids',len(esp.solids().vals()))
for i,s in enumerate(esp.solids().vals()):
    print(i,json.dumps(describe(s)))

old = cq.importers.importStep(str(ROOT/'flip_clock_pcb_bracket_v3.step'))
pieces=old.solids().vals()
fused=pieces[1].fuse(*pieces[2:]).clean()
print('V3 raw solids', len(pieces),'after fuse (excluding TEST)',len(fused.Solids()))
print('V3 fused bounds',json.dumps(describe(fused)))
