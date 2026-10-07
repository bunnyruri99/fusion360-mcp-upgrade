"""Slim case with PCB seating ledges and a rear insertion path, in mm."""
import math

W,L=21.08,73.15
ESP_BACK_Z=-6.2
USB_FRONT_Y=-2.45
USB_X,USB_Z=10.54,-8.7
CASE_OUT=(-3.95,-2.7,28.98,78.55)
CASE_IN=(-1.95,-1.2,24.98,75.55)
CASE_FRONT,CASE_BACK,LID_TOP=5.3,-13.6,-11.6
TFT_HOLES=[(2.41,2.41),(18.67,2.41)]
ESP_HOLES=[(.15,1.5),(20.93,1.5),(.15,23),(20.93,23)]
FRAME_HOLES=[]
LID_HOLES=[(-1.65,36),(22.73,36),(-1.65,64),(22.73,64)]
ESP_SOURCE=r'C:\Users\HunterD\Downloads\esp32-c3-supermini-1.snapshot.2\ESP32-C3 supermini v5.step'
ESP_TRANSFORM=[-1,0,0,-9.3905831467846,0,0,-1,16.6736646226333,
               0,-1,0,-3.0,0,0,0,1]
WINDOW_LOFT=[(2.78,12.405,3.3,15.397,55.895,.6),
             (.48,10.105,5.5,19.997,60.495,2.9)]
WINDOW_RIM_FILLET=.35

def box(*p):return {'kind':'box','p':list(p)}
def cylinder(x,y,z,r,h):return {'kind':'circle','p':[x,y,z,r,h]}
def rounded(x,y,z,w,l,h,r):return {'kind':'rounded','p':[x,y,z,w,l,h,r]}
def holes(points,z,h,r):return [cylinder(x,y,z,r,h) for x,y in points]
def nut_pockets():return [{'kind':'hex','p':[x,y,-4,4.2,1.75]} for x,y in TFT_HOLES]

def recipe():
    frame=[box(-1.35,0,-4,2.65,69.2,3),box(19.78,0,-4,2.65,69.2,3),
           box(0,0,-1,1.3,69.2,1),box(19.78,0,-1,1.3,69.2,1),
           box(-1.35,0,-4,23.78,5.2,4),box(-1.35,66,-4,23.78,3.2,4),
           box(-1.35,20.8,-4,23.78,4,3),
           box(5.2,-1.15,-4,10.68,2.15,2),
           box(1.64,-1.15,-5.8,17.8,.45,2.6)]
    frame+=holes(ESP_HOLES,-7.6,3.7,1.4)
    for x in (1.64,16.88):
        frame += [box(x,-1.15,-6.2,2.56,.45,.4),box(x,21.1,-6.2,2.56,.45,2.2)]
    frame_cuts=holes(TFT_HOLES,-10,12,1.1)+holes(ESP_HOLES,-7.6,5.5,.85)
    frame_cuts+=nut_pockets()+holes(LID_HOLES,-12,16,1.85)

    keeper=[box(-1.25,.2,-9.6,2.8,24.5,2),box(19.53,.2,-9.6,2.8,24.5,2),
            box(-1.25,23,-9.6,23.58,1.7,2),
            box(-1.25,.2,-9.6,5.45,3.3,2),box(16.88,.2,-9.6,5.45,3.3,2),
            box(.69,-1.15,-9.6,3.51,1.35,2),box(16.88,-1.15,-9.6,3.51,1.35,2),
            box(-1.25,21.1,-9.6,5.45,1.9,2),box(16.88,21.1,-9.6,5.45,1.9,2)]
    for x in (1.64,16.88):
        for y in (-1.15,21.1):keeper.append(box(x,y,-7.6,2.56,.45,.5))
        keeper += [box(x,-1.6,-7.6,2.56,.45,1.5),box(x,21.55,-7.6,2.56,.45,1.5)]
    for x in (.69,19.59):
        for y in (-1.15,21.1):keeper.append(box(x,y,-7.6,.8,.45,1.5))
    keeper_cuts=holes(ESP_HOLES,-11,7,1.1)

    ox,oy,ow,ol=CASE_OUT;ix,iy,iw,il=CASE_IN
    case_outer=rounded(ox,oy,LID_TOP,ow,ol,16.9,2.5)
    cavity=rounded(ix,iy,LID_TOP-.1,iw,il,15,.8)
    # Front seats contact bare PCB strips; the lens remains clear by 0.2 mm.
    bosses=holes(LID_HOLES,LID_TOP,6.6,1.55)
    bosses += [box(0,5.5,1.6,1.3,63.7,1.8),box(19.78,5.5,1.6,1.3,63.7,1.8)]
    relief=box(.4,-1.8,LID_TOP-.1,20.28,1.2,10.1)
    throat=rounded(2.78,12.405,3.2,15.397,55.895,2.3,.6)
    usb={'kind':'rounded_xz','p':[5.74,-10.6,-3.1,9.6,3.8,4.1,1.8]}
    # Open to the rear for straight insertion; the lid supplies the lower outline.
    usb_insertion=box(5.74,-3.1,LID_TOP-.1,9.6,4.1,3)
    case_cuts=[relief,throat,usb,usb_insertion]+holes(LID_HOLES,LID_TOP,5.8,.85)

    lid_outer=rounded(ox,oy,CASE_BACK,ow,ol,2,2.5)
    lip=rounded(ix+.3,iy+.3,LID_TOP,iw-.6,il-.6,.9,.5)
    inside=rounded(ix+1.2,iy+1.2,LID_TOP-.1,iw-2.4,il-2.4,1.2,.1)
    lid_parts=[box(5.84,-2.7,LID_TOP,9.4,.9,2.9)]
    # Four ribs transfer lid closure to the frame's rear face.
    for x in (0,19.78):
        for y in (28,55):lid_parts.append(box(x,y,LID_TOP,1.3,6,7.6))
    lid_cuts=holes(LID_HOLES,CASE_BACK-.1,3,1.1)
    lid_cuts+=holes(LID_HOLES,CASE_BACK-.1,1,2)
    lid_cuts+=holes(LID_HOLES,LID_TOP-.05,1.1,1.85)+[usb]
    lid_cuts+=holes(ESP_HOLES,LID_TOP-.05,1.1,2.1)
    return {'frame':{'parts':frame,'cuts':frame_cuts},
            'keeper':{'parts':keeper,'cuts':keeper_cuts},
            'case':{'outer':case_outer,'cavity':cavity,'bosses':bosses,'cuts':case_cuts,
                    'window_loft':WINDOW_LOFT,'window_rim_fillet':WINDOW_RIM_FILLET},
            'lid':{'outer':lid_outer,'lip':lip,'lip_inside':inside,'parts':lid_parts,'cuts':lid_cuts}}
