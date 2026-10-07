"""Millimetre recipe shared by native Fusion features and geometry verification."""
import math

W,L=21.08,73.15
ESP_BACK_Z=-6.2
USB_FRONT_Y=-2.45
USB_X,USB_Z=10.54,-8.7
CASE_OUT=(-6.45,-2.7,33.98,78.55)
CASE_IN=(-4.45,-.7,29.98,74.55)
CASE_FRONT=5.3
CASE_BACK=-13.6
LID_TOP=-11.6
TFT_HOLES=[(2.41,2.41),(18.67,2.41)]
ESP_HOLES=[(-2,1.5),(23.08,1.5),(-2,23),(23.08,23)]
FRAME_HOLES=[(-2,28),(23.08,28),(-2,61.5),(23.08,61.5)]
LID_HOLES=[(-4.25,34),(25.33,34),(-4.25,69.5),(25.33,69.5)]
ESP_SOURCE=r'C:\Users\HunterD\Downloads\esp32-c3-supermini-1.snapshot.2\ESP32-C3 supermini v5.step'
ESP_TRANSFORM=[-1,0,0,-9.3905831467846, 0,0,-1,16.6736646226333,
               0,-1,0,-3.0, 0,0,0,1]

def box(*p): return {'kind':'box','p':list(p)}
def cylinder(x,y,z,r,h): return {'kind':'circle','p':[x,y,z,r,h]}
def rounded(x,y,z,w,l,h,r): return {'kind':'rounded','p':[x,y,z,w,l,h,r]}
def holes(points,z,h,r): return [cylinder(x,y,z,r,h) for x,y in points]
def nut_pockets(): return [{'kind':'hex','p':[x,y,-4,4.2,1.75]} for x,y in TFT_HOLES]

def recipe():
    frame=[box(-3.9,0,-4,3.8,69.2,3),box(W+.1,0,-4,3.8,69.2,3),
           box(-3.9,0,-4,W+7.8,5.2,3),box(-3.9,66,-4,W+7.8,3.2,3),
           box(0,66.5,-1,1.3,2.7,1),box(W-1.3,66.5,-1,1.3,2.7,1),
           box(-3.9,20.8,-4,W+7.8,4,3),
           box(5.2,-1.15,-4,10.68,2.15,2),
           box(1.64,-1.15,-5.8,17.8,.45,2.6)]
    frame+=holes(TFT_HOLES,-4,4,2.2)+holes(ESP_HOLES,-7.6,6.6,1.95)
    for x in (1.64,16.88):
        frame+=[box(x,-1.15,-6.2,2.56,.45,.4),box(x,21.1,-6.2,2.56,.45,2.2)]
    frame_cuts=holes(TFT_HOLES+FRAME_HOLES,-10,12,1.1)+holes(ESP_HOLES,-7.6,5.5,.85)+nut_pockets()

    keeper=[box(-3.9,.2,-9.6,3.8,24.5,2),box(W+.1,.2,-9.6,3.8,24.5,2),
            box(-3.9,23,-9.6,W+7.8,1.7,2),
            box(-3.9,.2,-9.6,8.1,3.3,2),box(16.88,.2,-9.6,8.1,3.3,2),
            box(.69,-1.15,-9.6,3.51,1.35,2),box(16.88,-1.15,-9.6,3.51,1.35,2),
            box(-3.9,21.1,-9.6,8.1,1.9,2),box(16.88,21.1,-9.6,8.1,1.9,2)]
    for x in (1.64,16.88):
        for y in (-1.15,21.1): keeper.append(box(x,y,-7.6,2.56,.45,.5))
        keeper += [box(x,-1.6,-7.6,2.56,.45,1.5),box(x,21.55,-7.6,2.56,.45,1.5)]
    for x in (.69,19.59):
        for y in (-1.15,21.1): keeper.append(box(x,y,-7.6,.8,.45,1.5))
    keeper_cuts=holes(ESP_HOLES,-11,7,1.1)

    ox,oy,ow,ol=CASE_OUT
    ix,iy,iw,il=CASE_IN
    body=[rounded(ox,oy,LID_TOP,ow,ol,CASE_FRONT-LID_TOP,3)]
    body+=holes(FRAME_HOLES,-1,4.4,1.8)
    body+=holes(LID_HOLES,LID_TOP,6.6,1.9)
    cavity=rounded(ix,iy,LID_TOP-.1,iw,il,14.999999999999998,1)
    # Local internal relief accommodates PCB end and keeper; exterior USB outline stays intact.
    relief=box(.4,-1.8,-10,20.28,1.2,8.4)
    window=rounded(2.78,12.405,3.2,15.397,55.895,2.3,.6)
    usb_cut={'kind':'rounded_xz','p':[USB_X-4.8,USB_Z-1.9,-3.1,9.6,3.8,4.1,1.8]}
    # Cavity is cut before bosses are added so posts survive the hollowing operation.
    body_cuts=[relief,window,usb_cut]+holes(FRAME_HOLES,-1,3.8,.85)+holes(LID_HOLES,LID_TOP,5.8,.85)

    lid=[rounded(ox,oy,CASE_BACK,ow,ol,2,3)]
    lip=rounded(ix+.3,iy+.3,LID_TOP,iw-.6,il-.6,.9,.7)
    lip_inside=rounded(ix+1.2,iy+1.2,LID_TOP-.1,iw-2.4,il-2.4,1.2,.1)
    lid_cuts=holes(LID_HOLES,CASE_BACK-.1,3,1.1)
    counterbores=holes(LID_HOLES,CASE_BACK-.1,1.0,2)
    lip_clearance=holes(LID_HOLES,LID_TOP-.05,1.1,2.15)
    return {'frame':{'parts':frame,'cuts':frame_cuts},
            'keeper':{'parts':keeper,'cuts':keeper_cuts},
            'case':{'outer':body[0],'cavity':cavity,'bosses':body[1:],'cuts':body_cuts},
            'lid':{'outer':lid[0],'lip':lip,'lip_inside':lip_inside,
                   'cuts':lid_cuts+counterbores+lip_clearance}}
