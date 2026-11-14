#!/usr/bin/env python3
"""Expressive layered lion animation: articulated limbs, hinged head and drinking cycle."""
import argparse, math
from PIL import Image, ImageDraw
import engine

W,H=1280,720
INK=(43,35,29); SKY=(239,205,151); GOLD=(207,148,79); GOLD_L=(231,178,105)
MANE=(151,83,43); MANE_D=(91,49,31); FACE=(236,190,132); CREAM=(249,225,183)
WATER=(45,139,151); WATER_L=(132,213,211); SCRUB=(86,111,61)

def ell(d,b,fill,outline=INK,width=3):
    d.ellipse(tuple(int(v) for v in b),fill=fill,outline=outline,width=max(1,int(width)) if outline else 1)
def stroke(d,p,c=INK,w=5):
    d.line([(int(x),int(y)) for x,y in p],fill=c,width=max(1,int(w)),joint="curve")
def label(d,p,s,n=20,c=INK,a="mm"):
    d.text(p,str(s),font=engine.font(n,True),fill=c,anchor=a)
def clamp(v): return max(0.,min(1.,v))
def smooth(v):
    v=clamp(v); return v*v*(3-2*v)
def lerp(a,b,u): return a+(b-a)*u

def landscape(t):
    im=Image.new("RGB",(W,H),SKY); d=ImageDraw.Draw(im)
    sx=1030+math.sin(t*.035)*12
    ell(d,(sx-66,65,sx+66,197),(250,226,174),None)
    d.polygon([(0,375),(170,300),(360,380),(585,292),(820,370),(1050,305),(1280,370),(1280,720),(0,720)],fill=(221,166,107))
    d.polygon([(0,468),(210,394),(430,470),(690,390),(920,465),(1110,400),(1280,458),(1280,720),(0,720)],fill=(190,130,79))
    d.polygon([(0,565),(230,493),(460,558),(735,480),(1000,552),(1280,480),(1280,720),(0,720)],fill=(158,101,63))
    for i in range(11):
        x=(i*137+int(t*8))%1370-40; y=505+(i%3)*36; sw=math.sin(t*1.8+i)*7
        stroke(d,[(x,y),(x+sw,y-34),(x+sw-12,y-48)],SCRUB,4)
        stroke(d,[(x+sw,y-20),(x+sw+16,y-36)],SCRUB,4)
    for i in range(24):
        x=(i*61+int(t*22))%W; y=290+(i*37)%260
        d.arc((x,y,x+62,y+12),185,345,fill=(249,222,179),width=2)
    return im

def pool(im,t,activity):
    d=ImageDraw.Draw(im)
    ell(d,(760,493,1245,630),(120,91,58),None)
    ell(d,(748,478,1235,608),(31,112,124),None)
    ell(d,(770,487,1208,588),WATER,None)
    for i in range(6):
        phase=(t*38+i*57)%230; cx=1002+math.sin(t*.5+i)*8; cy=541+math.cos(t*.7+i)*2
        rx=25+phase*.75; ry=5+phase*.12
        d.arc((cx-rx,cy-ry,cx+rx,cy+ry),190,350,fill=WATER_L,width=2 if i%2 else 3)
    if activity:
        for i in range(3):
            x=1005+math.sin(t*6+i)*15; y=515-((t*31+i*17)%48)
            ell(d,(x-3,y-5,x+3,y+5),(204,238,218),None)

def leg(d,hip,phase,gait,front=True,far=False):
    hx,hy=hip; direction=1 if front else -1
    stride=math.sin(phase+(math.pi if far else 0))*30*gait
    lift=max(0,math.cos(phase+(math.pi if far else 0)))*17*gait
    knee=(hx+direction*9+stride*.42,hy+39-lift*.35); ankle=(hx+stride,hy+83-lift)
    col=(146,98,57) if far else GOLD
    stroke(d,[(hx,hy),knee,ankle],INK,17); stroke(d,[(hx,hy),knee,ankle],col,10)
    ell(d,(ankle[0]-15,ankle[1]-7,ankle[0]+25,ankle[1]+9),col,INK,3)
    for j in range(3): stroke(d,[(ankle[0]+12+j*4,ankle[1]-1),(ankle[0]+15+j*4,ankle[1]+4)],INK,2)

def head_layer(pivot,t,action,dip,s):
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer); px,py=pivot
    ell(d,(px-91*s,py-103*s,px+91*s,py+86*s),MANE_D,INK,5*s)
    for i in range(16):
        a=2*math.pi*i/16; cx=px+76*s*math.cos(a); cy=py-8*s+82*s*math.sin(a); r=(18 if i%2 else 22)*s
        ell(d,(cx-r,cy-r,cx+r,cy+r),MANE,INK,2*s)
    ell(d,(px-48*s,py-68*s,px+49*s,py+61*s),FACE,INK,4*s)
    ell(d,(px-48*s,py-76*s,px-14*s,py-39*s),FACE,INK,3*s)
    ell(d,(px+17*s,py-76*s,px+51*s,py-39*s),FACE,INK,3*s)
    ell(d,(px-42*s,py-68*s,px-21*s,py-47*s),MANE_D,None)
    ell(d,(px+25*s,py-68*s,px+45*s,py-47*s),MANE_D,None)
    blink=(t%5.1)<.16
    for ex in (px-22*s,px+23*s):
        ey=py-13*s
        if blink: stroke(d,[(ex-7*s,ey),(ex+7*s,ey)],INK,3*s)
        else:
            ell(d,(ex-6*s,ey-6*s,ex+6*s,ey+6*s),CREAM,INK,2*s)
            ell(d,(ex-2*s,ey-3*s,ex+3*s,ey+4*s),INK,None)
    ell(d,(px-29*s,py+14*s,px+1*s,py+43*s),CREAM,None)
    ell(d,(px+1*s,py+14*s,px+31*s,py+43*s),CREAM,None)
    d.polygon([(px-8*s,py+17*s),(px+9*s,py+17*s),(px+s,py+29*s)],fill=INK)
    jaw=math.sin(t*8)*3*s if action=="drink" else 0
    if action=="roar":
        ell(d,(px-24*s,py+25*s,px+25*s,py+68*s),(72,34,29),INK,3*s)
        ell(d,(px-18*s,py+52*s,px+18*s,py+61*s),(198,91,83),None)
    stroke(d,[(px+s,py+29*s),(px+s,py+42*s+jaw),(px-9*s,py+46*s+jaw)],INK,3*s)
    for side in (-1,1):
        for k in range(2): stroke(d,[(px+side*17*s,py+28*s+k*8*s),(px+side*51*s,py+22*s+k*8*s)],(112,78,53),2*s)
    if action=="drink":
        lap=math.sin(t*9)>-.15; length=(14+12*max(0,math.sin(t*9)))*s if lap else 3*s
        stroke(d,[(px+3*s,py+42*s),(px+7*s,py+42*s+length)],(183,73,82),5*s)
        if lap and int(t*3)%2==0: ell(d,(px+1*s,py+61*s,px+7*s,py+68*s),(191,231,220),None)
    # Rotate the whole mane/face as one head around its shoulder-side hinge.
    angle=-27*dip
    if action=="listen": angle=12+math.sin(t*1.7)*3
    if action=="roar": angle=-8
    return layer.rotate(angle,resample=Image.Resampling.BICUBIC,center=(int(px-48*s),int(py+55*s)))

def lion(im,x,ground,t,action="walk",scale=1.16,gait=1.0):
    s=scale; bob=math.sin(t*10)*4*s*gait; g=ground+bob; d=ImageDraw.Draw(im)
    d.ellipse((x-155*s,g-3*s,x+160*s,g+18*s),fill=(116,76,48))
    sway=math.sin(t*2.3)*17*s
    stroke(d,[(x-111*s,g-112*s),(x-158*s,g-139*s+sway),(x-194*s,g-105*s+sway)],INK,9*s)
    stroke(d,[(x-194*s,g-105*s+sway),(x-208*s,g-91*s+sway)],MANE_D,14*s)
    leg(d,(x-75*s,g-90*s),t*5.3,gait,False,True); leg(d,(x+55*s,g-90*s),t*5.3,gait,True,True)
    ell(d,(x-132*s,g-184*s,x+107*s,g-42*s),GOLD,INK,5*s)
    ell(d,(x-112*s,g-167*s,x+85*s,g-57*s),GOLD_L,None)
    ell(d,(x+35*s,g-171*s,x+123*s,g-53*s),(193,126,67),INK,4*s)
    stroke(d,[(x-70*s,g-75*s),(x-5*s,g-66*s),(x+57*s,g-74*s)],(159,105,60),3*s)
    leg(d,(x-75*s,g-89*s),t*5.3,gait,False,False); leg(d,(x+55*s,g-89*s),t*5.3,gait,True,False)
    dip=smooth(t/1.8) if action in ("lower","mark") else 1.0 if action=="drink" else 1-smooth(t/1.45) if action=="lift" else 0.0
    head=head_layer((int(x+87*s),int(g-154*s)),t,action,dip,s)
    return Image.alpha_composite(im.convert("RGBA"),head).convert("RGB")

def acacia(im,x,y,scale=1.0):
    d=ImageDraw.Draw(im); s=scale
    stroke(d,[(x,y),(x-5*s,y-155*s),(x+8*s,y-265*s)],(91,66,43),int(17*s))
    stroke(d,[(x,y-120*s),(x-82*s,y-205*s)],(91,66,43),int(11*s))
    stroke(d,[(x+3*s,y-170*s),(x+93*s,y-244*s)],(91,66,43),int(10*s))
    for cx,cy,rx,ry in [(x-5*s,y-276*s,104*s,37*s),(x-82*s,y-215*s,66*s,29*s),(x+94*s,y-252*s,76*s,31*s)]:
        ell(d,(cx-rx,cy-ry,cx+rx,cy+ry),(76,103,53),None)

def rival_lion(im,x,y,t):
    d=ImageDraw.Draw(im)
    # distant rival is deliberately a darker, smaller silhouette to establish depth
    ell(d,(x-92,y-85,x+78,y-22),(83,62,46),None)
    ell(d,(x+36,y-121,x+105,y-43),(83,62,46),None)
    stroke(d,[(x-64,y-35),(x-75,y+20)],(66,51,41),9)
    stroke(d,[(x-8,y-35),(x-1,y+20)],(66,51,41),9)
    stroke(d,[(x+40,y-48),(x+56,y+18)],(66,51,41),9)
    stroke(d,[(x-87,y-68),(x-125,y-86+math.sin(t*2)*5)],(66,51,41),6)

def scent_marks(im,t):
    d=ImageDraw.Draw(im)
    for i in range(3):
        yy=470-i*25
        x=835+math.sin(t*1.5+i)*10
        d.arc((x-30,yy-30,x+30,yy+30),205,320,fill=(246,220,168),width=3)

def make_frame(scene,frame,frames,size,scene_number,scene_count,title):
    w,h=size; duration=max(1.,float(scene.get("_render_duration",scene.get("duration",6))))
    t=frame/max(1,frames-1)*duration
    action=scene.get("animal_action","walk"); movement=scene.get("movement","hold")
    im=landscape(t)
    # Scene-specific blocking: each beat has its own landmark, scale and action.
    if scene_number==1:
        acacia(im,1040,535,1.15)
        x=lerp(150,410,smooth(t/duration)); scale=.82; ground=600; gait=.85
    elif scene_number==2:
        acacia(im,1080,555,.88)
        x=lerp(150,800,smooth(t/duration)); scale=1.02; ground=590; gait=1.0
    elif scene_number==3:
        acacia(im,1010,585,1.25)
        x=690+math.sin(t*.35)*5; scale=1.08; ground=590; gait=0.0
        scent_marks(im,t)
    elif scene_number==4:
        x=580; scale=1.20; ground=590; gait=0.0
        # Sound arcs and a moving bird silhouette give the pause a readable purpose.
        d=ImageDraw.Draw(im)
        for i in range(3):
            d.arc((760+i*18,350-i*8,850+i*18,450+i*8),285,75,fill=(250,231,194),width=3)
        bx=lerp(1080,900,(t%duration)/duration)
        stroke(d,[(bx-18,355),(bx,345),(bx+18,355)],(61,57,49),4)
    elif scene_number==5:
        x=620; scale=1.18; ground=590; gait=0.0
        rival_lion(im,1050,530,t)
        d=ImageDraw.Draw(im)
        for i in range(4):
            d.arc((770+i*14,390-i*10,890+i*14,490+i*10),200,340,fill=(239,211,174),width=3)
    else:
        acacia(im,190,570,.95)
        x=lerp(690,1450,smooth(t/duration)); scale=1.02; ground=590; gait=1.0
        # Foreground grass sweeps across frame to reinforce the departure.
        d=ImageDraw.Draw(im)
        for i in range(22):
            gx=(i*59+int(t*34))%w
            stroke(d,[(gx,650),(gx-8,610-(i%4)*7)],(75,96,49),3)
    if action in ("lower","rest","listen","roar","mark"):
        gait=0.0
    if action in ("walk","approach","patrol"):
        gait=1.0 if scene_number in (1,2,6) else gait
    im=lion(im,x,ground,t,action,scale,gait)
    d=ImageDraw.Draw(im)
    # Story-specific visual cue, rather than a repeated generic caption card alone.
    d.rounded_rectangle((48,34,w-48,91),radius=15,fill=(250,235,211),outline=(122,86,55),width=2)
    label(d,(72,63),scene.get("heading",title)[:58],19,(105,75,49),"lm")
    d.rounded_rectangle((48,h-88,w-48,h-34),radius=13,fill=(250,239,219),outline=(165,127,91),width=2)
    label(d,(w//2,h-61),scene.get("caption",scene.get("heading","")),20,(68,51,39))
    progress=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    d.rounded_rectangle((48,h-19,w-48,h-12),radius=4,fill=(205,178,143))
    d.rounded_rectangle((48,h-19,48+int((w-96)*progress),h-12),radius=4,fill=(70,126,91))
    return im

engine.make_frame=make_frame
def run(story_path,output): engine.run(story_path,output)
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--script",default="demo/lion_territory_patrol_60s.json"); p.add_argument("--output",default="output/lion-territory-patrol-60s.mp4")
    a=p.parse_args(); run(a.script,a.output)
