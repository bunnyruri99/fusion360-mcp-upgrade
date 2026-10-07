"""M3 heat-set fixing, independent frame retention; all dimensions in mm."""
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('slim_base',Path(__file__).with_name('case_v2_recipe.py'))
V=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(V)
W,L=V.W,V.L
CASE_OUT,CASE_IN=V.CASE_OUT,V.CASE_IN
CASE_FRONT,CASE_BACK,LID_TOP=5.3,-15.6,-13.6
ESP_BACK_Z=-8.2
USB_FRONT_Y,USB_X,USB_Z=-2.45,10.54,-10.7
ESP_SOURCE=V.ESP_SOURCE
ESP_TRANSFORM=list(V.ESP_TRANSFORM);ESP_TRANSFORM[11]=-5.0
TFT_HOLES=V.TFT_HOLES
ESP_HOLES=[]
KEEPER_Y=[9.3,20.0]
FRAME_HOLES=[(-1.35,y,-5.0) for y in (33,58)]+[(22.43,y,-5.0) for y in (33,58)]
LID_HOLES=[(3.0,42),(18.08,42),(3.0,66),(18.08,66)]
WINDOW_LOFT,WINDOW_RIM_FILLET=V.WINDOW_LOFT,V.WINDOW_RIM_FILLET
INSERT_OD,INSERT_LENGTH,INSERT_PILOT,INSERT_DEPTH=4.6,4.0,4.0,5.0
box,cylinder,rounded,holes,nut_pockets=V.box,V.cylinder,V.rounded,V.holes,V.nut_pockets

def circle_x(x,y,z,r,h):return {'kind':'circle_x','p':[x,y,z,r,h]}
def cone_x(x,y,z,r1,r2,h):return {'kind':'cone_x','p':[x,y,z,r1,r2,h]}

def recipe():
    frame=[box(-1.35,0,-4,2.65,69.2,3),box(19.78,0,-4,2.65,69.2,3),
           box(0,0,-1,1.3,69.2,1),box(19.78,0,-1,1.3,69.2,1),
           box(-1.35,0,-4,23.78,5.2,4),box(-1.35,66,-4,23.78,3.2,4),
           box(-1.35,20.8,-4,23.78,4,3),box(5.2,-1.15,-4,10.68,2.15,2),
           box(1.64,-1.15,-7.8,17.8,.45,4.6)]
    for x in (1.64,16.88):
        frame += [box(x,-1.15,-8.2,2.56,.45,.4),box(x,21.1,-8.2,2.56,.45,4.2)]
    cuts=holes(TFT_HOLES,-10,12,1.1)+nut_pockets()
    for y in KEEPER_Y:
        frame += [circle_x(1.6,y,-4.1,3.9,6),circle_x(13.48,y,-4.1,3.9,6),
                  box(.7,y-3.9,-.8,2.3,7.8,.6),box(18.08,y-3.9,-.8,2.3,7.8,.6)]
        cuts += [box(-2,y-3.3,-8,3.6,6.6,7.2),box(19.48,y-3.3,-8,3.62,6.6,7.2),
                 circle_x(1.6,y,-4.1,2,5),circle_x(14.48,y,-4.1,2,5),
                 circle_x(1.6,y,-4.1,1.7,5.3),circle_x(14.18,y,-4.1,1.7,5.3)]
    for y in (33,58):
        frame += [circle_x(-1.35,y,-5,3.9,6.5),circle_x(15.93,y,-5,3.9,6.5)]
        cuts += [circle_x(-1.35,y,-5,2,5),circle_x(17.43,y,-5,2,5),
                 circle_x(-1.35,y,-5,1.7,6),circle_x(16.43,y,-5,1.7,6)]
    frame+=holes(LID_HOLES,-12.4,8.5,3.9)
    cuts+=holes(LID_HOLES,-12.4,5,2)+holes(LID_HOLES,-12.4,5.5,1.7)

    old=V.recipe()['keeper']
    keeper=[]
    for item in old['parts']:
        s={'kind':item['kind'],'p':list(item['p'])};s['p'][2]-=2;keeper.append(s)
    kc=[]
    for y in KEEPER_Y:
        keeper += [box(0,y-3.1,-7.8,1.6,6.2,6.8),box(19.48,y-3.1,-7.8,1.6,6.2,6.8),
                   box(0,y-3.1,-11.6,1.25,6.2,3.8),box(19.83,y-3.1,-11.6,1.25,6.2,3.8)]
        kc += [circle_x(-.1,y,-4.1,1.7,1.8),circle_x(19.38,y,-4.1,1.7,1.8)]

    ox,oy,ow,ol=CASE_OUT;ix,iy,iw,il=CASE_IN
    outer=rounded(ox,oy,LID_TOP,ow,ol,CASE_FRONT-LID_TOP,2.5)
    cavity=rounded(ix,iy,LID_TOP-.1,iw,il,17,.8)
    seats=[box(0,5.5,1.6,1.3,63.7,1.8),box(19.78,5.5,1.6,1.3,63.7,1.8)]
    seats+=contact_pads()
    usb={'kind':'rounded_xz','p':[5.74,-12.6,-3.1,9.6,3.8,4.1,1.8]}
    cc=[box(.4,-1.8,LID_TOP-.1,20.28,1.2,12.1),
        rounded(2.78,12.405,3.2,15.397,55.895,2.3,.6),usb,
        box(5.74,-3.1,LID_TOP-.1,9.6,4.1,3)]
    for y in (33,58):
        cc += [circle_x(ox-.1,y,-5,1.7,ow+.2),
               cone_x(ox,y,-5,3.1,1.7,1.4),cone_x(ox+ow-1.4,y,-5,1.7,3.1,1.4)]

    lo=rounded(ox,oy,CASE_BACK,ow,ol,2,2.5)
    lip=rounded(ix+.3,iy+.3,LID_TOP,iw-.6,il-.6,.9,.5)
    inside=rounded(ix+1.2,iy+1.2,LID_TOP-.1,iw-2.4,il-2.4,1.2,.1)
    lp=[box(5.84,-2.7,LID_TOP,9.4,.9,2.9)]+holes(LID_HOLES,LID_TOP,1.2,4.1)
    lc=holes(LID_HOLES,CASE_BACK-.1,3.5,1.7)+holes(LID_HOLES,CASE_BACK-.1,1.85,3.1)+[usb]
    return {'frame':{'parts':frame,'cuts':cuts},'keeper':{'parts':keeper,'cuts':kc},
            'case':{'outer':outer,'cavity':cavity,'bosses':seats,'cuts':cc,
                    'window_loft':WINDOW_LOFT,'window_rim_fillet':WINDOW_RIM_FILLET},
            'lid':{'outer':lo,'lip':lip,'lip_inside':inside,'parts':lp,'cuts':lc}}

def contact_pads():
    # Local lands carry the side-screw clamp load directly into the frame boss faces.
    return [s for y in (33,58) for s in (circle_x(-1.95,y,-5,3.8,.6),circle_x(22.43,y,-5,3.8,.6))]

def hardware():
    """Conservative envelopes; thread pitch/knurl details are omitted."""
    inserts=[];screws=[]
    def insert(name,start,direction):
        inserts.append({'name':name,'start':start,'direction':direction,'length':4,'radius':2.3,'bore':1.5})
    def screw(name,start,direction,length,head='button'):
        screws.append({'name':name,'start':start,'direction':direction,'length':length,'radius':1.5,
                       'head':head,'head_radius':2.85 if head=='button' else 3.0,'head_height':1.65 if head=='button' else 1.5})
    for y in KEEPER_Y:
        insert('NEP_left_'+str(y),(1.6,y,-4.1),(1,0,0));insert('NEP_right_'+str(y),(19.48,y,-4.1),(-1,0,0))
        screw('NEP_M3x6_left_'+str(y),(0,y,-4.1),(1,0,0),6)
        screw('NEP_M3x6_right_'+str(y),(21.08,y,-4.1),(-1,0,0),6)
    for y in (33,58):
        insert('FRAME_left_'+str(y),(-1.35,y,-5),(1,0,0));insert('FRAME_right_'+str(y),(22.43,y,-5),(-1,0,0))
        # DIN7991 nominal length includes its countersunk head.
        screw('FRAME_DIN7991_M3x8_left_'+str(y),(-3.85,y,-5),(1,0,0),8,'countersunk')
        screw('FRAME_DIN7991_M3x8_right_'+str(y),(24.93,y,-5),(-1,0,0),8,'countersunk')
    for x,y in LID_HOLES:
        insert('LID_'+str(x)+'_'+str(y),(x,y,-12.4),(0,0,1))
        screw('LID_M3x6_'+str(x)+'_'+str(y),(x,y,-13.85),(0,0,1),6)
    return inserts,screws
