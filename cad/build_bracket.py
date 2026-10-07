"""Open PCB bracket, in mm. Actual ESP STEP reference; TFT is a drawing proxy.

Run with .cad-venv/Scripts/python.exe cad/build_bracket.py.
Only frame and rear_keeper are printable. Hardware and boards are references.
"""
from pathlib import Path
import json
import math
import cadquery as cq
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad'/'bracket_corrected'
OUT.mkdir(exist_ok=True)
ESP_PATH=Path(r'C:\Users\HunterD\Downloads\esp32-c3-supermini-1.snapshot.2\ESP32-C3 supermini v5.step')
W,L=21.08,73.15
TFT_PCB_T=1.6  # Not supplied in drawing. Bolted mounting accommodates thickness.
TFT_HOLES=((2.41,2.41),(18.67,2.41))
ESP_Z=-11.0   # Backside of ESP PCB, component face points backwards.
ESP_Y=30.0
CLAMP_HOLES=((-2.0,29.0),(23.08,29.0),(-2.0,54.0),(23.08,54.0))

def box(x,y,z,w,l,h):
    return cq.Workplane('XY').box(w,l,h,centered=(False,False,False)).translate((x,y,z)).val()

def cyl(x,y,z,r,h):
    return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z)).val()

def fuse(parts):
    return parts[0].fuse(*parts[1:]).clean()

def drill(shape, holes, z, height, radius=1.1):
    return shape.cut(*[cyl(x,y,z,radius,height) for x,y in holes]).clean()

def bounds(shape):
    b=shape.BoundingBox()
    return [round(v,4) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)]

# Import real topology, not Cartesian-point extrema in a STEP text file.
ref=cq.importers.importStep(str(ESP_PATH)).solids().vals()
pcb=ref[0]
pb=pcb.BoundingBox()
assert abs(pb.xlen-17.8)<1e-3 and abs(pb.zlen-22.7)<1e-3
tx=W/2-(pb.xmin+pb.xmax)/2
ty=ESP_Y-pb.zmin
tz=ESP_Z+pb.ymin
esp_parts=[s.rotate((0,0,0),(1,0,0),-90).translate((tx,ty,tz)) for s in ref]
esp=cq.Compound.makeCompound(esp_parts)
esp_pcb=esp_parts[0]
eb=esp_pcb.BoundingBox()
ex0,ex1,ey0,ey1=eb.xmin,eb.xmax,eb.ymin,eb.ymax

# Main structural frame: all branches must fuse to ONE solid.
parts=[
    box(-3.9,0,-4,3.8,69.2,3),
    box(W+.1,0,-4,3.8,69.2,3),
    box(-3.9,0,-4,W+7.8,5.2,3),
    box(-3.9,66,-4,W+7.8,3.2,3),
    # Contact only bare TFT PCB strips outside the LCM edges (x=1.53..19.43).
    box(0,66.5,-1,1.3,2.7,1),
    box(W-1.3,66.5,-1,1.3,2.7,1),
]
parts += [cyl(x,y,-4,2.2,4) for x,y in TFT_HOLES]
parts += [cyl(x,y,-12.4,1.95,11.4) for x,y in CLAMP_HOLES]
# Rear cross-members clear components because they lie towards the TFT.
parts += [box(-3.9,27.5,-8.8,W+7.8,3.2,2),
          box(-3.9,52.25,-8.8,W+7.8,3.25,2)]
# Four PCB seats, away from the ESP header solder pads.
for x in (ex0,ex1-2.56):
    for y,length in ((ey0,.65),(ey1-.45,.45)):
        parts.append(box(x,y,ESP_Z,2.56,length,4.2))
frame=drill(fuse(parts),TFT_HOLES+CLAMP_HOLES,-15,17)

# Single removable rear keeper. Side limbs are outside the GPIO rows;
# short end lips contact PCB corners, with a completely open USB mouth.
kp=[box(-3.9,27.5,-14.4,3.8,28,2),
    box(W+.1,27.5,-14.4,3.8,28,2),
    box(-3.9,27.5,-14.4,W+7.8,2,2),
    box(-3.9,29.5,-14.4,ex0+2.56+3.9,.95,2),
    box(ex1-2.56,29.5,-14.4,W+3.9-(ex1-2.56),.95,2),
    box(-3.9,52.25,-14.4,ex0+2.56+3.9,3.25,2),
    box(ex1-2.56,52.25,-14.4,W+3.9-(ex1-2.56),3.25,2)]
pcb_face=ESP_Z-pb.ylen
for x in (ex0,ex1-2.56):
    for y,length in ((ey0,.45),(ey1-.45,.45)):
        kp.append(box(x,y,-12.4,2.56,length,pcb_face+12.4))
    # End stops prevent the PCB sliding along its long axis.
    kp += [box(x,ey0-.45,-12.4,2.56,.45,1.5),
           box(x,ey1,-12.4,2.56,.45,1.5)]
for x in (ex0-.95,ex1+.15):
    for y,length in ((ey0,.45),(ey1-.45,.45)):
        kp.append(box(x,y,-12.4,.8,length,1.5))
keeper=drill(fuse(kp),CLAMP_HOLES,-16,8)

# TFT dimensional proxy: PCB, two real hole locations, LCD footprint.
tft_pcb=drill(box(0,0,0,W,L,TFT_PCB_T),TFT_HOLES,-1,5,1.25)
lcd=box(1.98,L-4.2-60.55,TFT_PCB_T,17,60.55,1.5)
active=box(3.08,L-5.15-55.295,TFT_PCB_T+1.5,14.797,55.295,.05)
# Header envelope: pin row is 1.65mm from the top PCB edge.
header=box(.33,L-1.65-1.25,-6,20.42,2.5,6)

def screw(x,y,z,length):
    return fuse([cyl(x,y,z,1,length),cyl(x,y,z+length,1.9,1.5)])

def nut(x,y,z):
    n=cq.Workplane('XY').center(x,y).polygon(6,4.62).extrude(1.6).translate((0,0,z)).val()
    return n.cut(cyl(x,y,z-.1,1,1.8))

# TFT heads in front; rear keeper screws point towards TFT, heads behind.
hardware=[]
for x,y in TFT_HOLES:
    hardware.extend([screw(x,y,TFT_PCB_T-8,8),nut(x,y,-5.6)])
for x,y in CLAMP_HOLES:
    s=screw(0,0,0,16).rotate((0,0,0),(1,0,0),180).translate((x,y,1.6))
    hardware.extend([s,nut(x,y,-1)])

checks={}
for name,s in [('frame',frame),('rear_keeper',keeper)]:
    assert s.isValid() and len(s.Solids())==1, (name,'invalid or disconnected')
    cq.exporters.export(s,str(OUT/f'{name}.step'))
    cq.exporters.export(s,str(OUT/f'{name}.stl'),tolerance=.04,angularTolerance=.1)
    mesh=trimesh.load(str(OUT/f'{name}.stl'),force='mesh')
    checks[name]={'solid_count':len(s.Solids()),'valid':s.isValid(),
                  'stl_watertight':bool(mesh.is_watertight),
                  'stl_connected_components':len(mesh.split()),'bounds_mm':bounds(s)}
    assert mesh.is_watertight and len(mesh.split())==1
    # STEP roundtrip checks the actual deliverable, not only the in-memory shape.
    reloaded=cq.importers.importStep(str(OUT/f'{name}.step')).val()
    assert reloaded.isValid() and len(reloaded.Solids())==1

for name,a,b in [('frame_esp',frame,esp),('keeper_esp',keeper,esp),
                  ('frame_keeper',frame,keeper),('frame_tft_pcb',frame,tft_pcb),
                  ('frame_lcd',frame,lcd),('keeper_lcd',keeper,lcd),
                  ('frame_header',frame,header)]:
    v=a.intersect(b).Volume()
    checks[name+'_intersection_mm3']=round(v,7)
    if v>1e-5 and name.endswith('esp'):
        for i,s in enumerate(esp_parts):
            clash=a.intersect(s)
            if clash.Volume()>1e-5:
                print('CLASH',name,i,clash.Volume(),bounds(clash),flush=True)
    assert v<1e-5,(name,v)
usb=esp_parts[1]
ub=usb.BoundingBox()
# Connector approach: wider than the 9mm USB socket, 6.5mm tall.
approach=box((ub.xmin+ub.xmax)/2-5.5,ub.ymax,-16.5,11,18,6.5)
for name,s in [('frame',frame),('keeper',keeper)]:
    vol=s.intersect(approach).Volume()
    checks[name+'_usb_approach_intersection_mm3']=round(vol,7)
    assert vol<1e-5,(name,'USB approach blocked',vol)
checks['esp_pcb_mm']=[round(pb.xlen,4),round(pb.zlen,4),round(pb.ylen,4)]
checks['esp_board_bounds_mm']=bounds(esp_pcb)
checks['esp_transform']={'x_rotation_deg':-90,'translation_mm':[tx,ty,tz]}
checks['tft_hole_centres_mm']=TFT_HOLES
checks['assumptions']=['TFT PCB thickness 1.6mm, LCD thickness proxy 1.5mm; not measured.',
                       'TFT rear components not supplied; rear support clearance requires physical fit check.',
                       'ESP STEP has no soldered headers; GPIO solder space stays open.',
                       'FDM fit and keeper contact require a physical test print.']

assy=cq.Assembly(name='PCB_bracket_corrected')
assy.add(frame,name='print_frame',color=cq.Color(.18,.52,.62))
assy.add(keeper,name='print_rear_keeper',color=cq.Color(.92,.54,.18))
assy.add(esp,name='ESP32_C3_actual_STEP',color=cq.Color(.12,.3,.55))
assy.add(tft_pcb,name='TFT_PCB_drawing_proxy',color=cq.Color(.05,.38,.20))
assy.add(lcd,name='LCD_proxy',color=cq.Color(.1,.12,.14))
assy.add(active,name='Active_area_proxy',color=cq.Color(.18,.22,.26))
for i,h in enumerate(hardware):
    assy.add(h,name=f'M2_hardware_{i}',color=cq.Color(.65,.67,.7))
assy.export(str(OUT/'assembly.step'))
printassy=cq.Assembly(name='PRINT_ONLY_two_parts')
printassy.add(frame,name='frame')
printassy.add(keeper,name='rear_keeper')
printassy.export(str(OUT/'print_parts.step'))

# Engineering preview generated from the same CAD solids (not an AI rendering).
def draw(ax,shape,color,offset=(0,0,0),alpha=1):
    verts,tri=shape.tessellate(.18,.2)
    v=np.array([p.toTuple() for p in verts])+np.array(offset)
    ax.add_collection3d(Poly3DCollection(v[np.array(tri)],facecolors=color,
        edgecolors=color,linewidths=0,alpha=alpha,shade=True,lightsource=matplotlib.colors.LightSource(320,55)))

fig=plt.figure(figsize=(16,8),layout='constrained')
for k,(label,elev,azim,exploded) in enumerate([
    ('ASSEMBLED - display side',30,-65,False),
    ('ASSEMBLED - rear / USB / GPIO',-28,-65,False),
    ('EXPLODED - 2 printed parts + M2 screws',22,-62,True)]):
    ax=fig.add_subplot(1,3,k+1,projection='3d')
    draw(ax,frame,'#30869e')
    draw(ax,keeper,'#ec9039',(0,0,-9) if exploded else (0,0,0))
    for i,s in enumerate(esp_parts):
        color='#16498b' if i==0 else '#969b9e' if i==1 else '#404549'
        draw(ax,s,color,(0,0,-4.5) if exploded else (0,0,0))
    shift=(0,0,8) if exploded else (0,0,0)
    draw(ax,tft_pcb,'#186d3e',shift)
    draw(ax,lcd,'#1d2529',shift)
    draw(ax,active,'#323f45',shift)
    if not exploded:
        for h in hardware: draw(ax,h,'#b0b6bc')
    ax.set(xlim=(-10,32),ylim=(-5,78),zlim=(-28,16))
    ax.set_box_aspect((42,83,44))
    ax.view_init(elev=elev,azim=azim)
    ax.set_axis_off()
    ax.set_title(label,fontsize=11,pad=12)
fig.suptitle('Open PCB bracket - actual ESP32 STEP + TFT dimensional proxy',fontsize=16)
fig.savefig(OUT/'preview.png',dpi=160,facecolor='#f4f6f8')
plt.close(fig)
(OUT/'verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
