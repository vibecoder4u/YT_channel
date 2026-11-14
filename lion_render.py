#!/usr/bin/env python3
"""Hand-drawn line-art lion drinking at a desert waterhole.

Uses the narration/timing pipeline from engine.py and draws every frame
procedurally: no stock footage and no static animal image.
"""
import argparse, math
from PIL import Image, ImageDraw
import engine

W,H=1280,720
INK=(39,36,34); PAPER=(239,211,169); GOLD=(206,151,88)
MANE=(153,91,48); MANE_DARK=(105,61,39); FACE=(231,184,125)
WATER=(64,157,166); WATER_LIGHT=(139,211,204); GREEN=(75,112,68)

def ellipse(d,b,fill,outline=INK,width=4):
    d.ellipse(tuple(int(v) for v in b),fill=fill,outline=outline,width=max(1,int(width)))
def line(d,pts,fill=INK,width=5):
    d.line([(int(x),int(y)) for x,y in pts],fill=fill,width=max(1,int(width)),joint="curve")
def label(d,xy,s,size=20,color=INK,anchor="mm"):
    d.text(xy,str(s),font=engine.font(size,True),fill=color,anchor=anchor)

def desert(d,t):
    d.rectangle((0,0,W,H),fill=(239,204,151))
    d.ellipse((965,62,1115,212),fill=(250,226,171))
    d.polygon([(0,390),(190,315),(390,385),(630,300),(850,370),(1080,315),(1280,380),(1280,720),(0,720)],fill=(222,169,112))
    d.polygon([(0,490),(210,410),(430,475),(700,395),(930,470),(1120,410),(1280,470),(1280,720),(0,720)],fill=(194,137,85))
    d.polygon([(0,575),(230,500),(470,560),(730,480),(990,555),(1280,480),(1280,720),(0,720)],fill=(169,111,69))
    # sparse thorn scrub
    for i in range(7):
        x=(i*213+int(t*2))%W; y=490+(i%3)*42
        line(d,[(x,y),(x,y-32),(x-15,y-46)],GREEN,5)
        line(d,[(x,y-17),(x+17,y-35)],GREEN,5)
    # heat shimmer
    for i in range(6):
        x=(i*231+int(t*24))%W; y=315+(i%2)*34
        d.arc((x,y,x+80,y+18),185,345,fill=(250,224,183),width=3)

def waterhole(d,t):
    # still pool with ripples that respond to the lion's drinking
    ellipse(d,(700,500,1210,610),(48,135,145),None)
    ellipse(d,(735,508,1170,584),WATER,None)
    for k in range(5):
        pulse=(t*52+k*76)%230
        cx=930; cy=545
        box=(cx-pulse,cy-pulse*.20,cx+pulse,cy+pulse*.20)
        d.arc(tuple(map(int,box)),190,350,fill=WATER_LIGHT,width=3)

def lion(d,x,ground,t,action="approach",scale=1.0):
    s=scale
    # Action curve: lower head to drink, tiny tongue lapping, then lift.
    if action=="drink":
        dip=16+8*math.sin(t*5.5)
    elif action=="lower":
        dip=22*min(1,max(0,t/1.8))
    elif action=="lift":
        dip=22*(1-min(1,max(0,t/1.5)))
    else:
        dip=0
    walk=action in ("approach","walk")
    phase=t*6.0
    bob=math.sin(phase*2)*3*s if walk else math.sin(t*2)*1.5*s
    x=float(x); g=ground+bob
    # Tail curves behind and flicks at the tuft.
    tail_sway=math.sin(t*2.4)*13*s
    line(d,[(x-100*s,g-105*s),(x-151*s,g-125*s+tail_sway),(x-180*s,g-91*s+tail_sway)],INK,9*s)
    line(d,[(x-180*s,g-91*s+tail_sway),(x-197*s,g-82*s+tail_sway),(x-188*s,g-68*s+tail_sway)],MANE_DARK,13*s)
    # Legs, with alternating gait and visible paws.
    for idx, lx in enumerate((x-74*s,x+47*s)):
        for side in (0,1):
            off=math.sin(phase+(idx+side)*math.pi)*22*s if walk else 0
            hipx=lx+(side*17-8)*s
            knee=(hipx+off*.45,g-52*s+abs(off)*.10)
            paw=(hipx+off,g-3*s)
            line(d,[(hipx,g-91*s),knee,paw],INK,14*s)
            line(d,[(hipx,g-91*s),knee,paw],GOLD,8*s)
            ellipse(d,(paw[0]-12*s,paw[1]-7*s,paw[0]+22*s,paw[1]+7*s),GOLD,INK,3*s)
            for claw in range(2):
                line(d,[(paw[0]+10*s+claw*5*s,paw[1]-2*s),(paw[0]+14*s+claw*5*s,paw[1]+3*s)],INK,2*s)
    # Body and chest silhouette.
    ellipse(d,(x-119*s,g-169*s,x+91*s,g-38*s),GOLD,INK,5*s)
    ellipse(d,(x-108*s,g-155*s,x+76*s,g-51*s),(218,162,98),None)
    # Mane: layered uneven locks create a hand-drawn outline.
    hx=x+100*s; hy=g-169*s+dip
    ellipse(d,(hx-80*s,hy-93*s,hx+83*s,hy+80*s),MANE_DARK,INK,5*s)
    for k in range(13):
        a=2*math.pi*k/13
        cx=hx+72*s*math.cos(a); cy=hy-8*s+78*s*math.sin(a)
        r=20*s
        ellipse(d,(cx-r,cy-r,cx+r,cy+r),MANE,INK,2*s)
    # Face and muzzle move down toward the pool.
    ellipse(d,(hx-45*s,hy-67*s,hx+52*s,hy+54*s),FACE,INK,4*s)
    # ears
    ellipse(d,(hx-47*s,hy-72*s,hx-14*s,hy-37*s),FACE,INK,3*s)
    ellipse(d,(hx+19*s,hy-72*s,hx+52*s,hy-37*s),FACE,INK,3*s)
    ellipse(d,(hx-39*s,hy-63*s,hx-21*s,hy-45*s),(139,75,57),None)
    ellipse(d,(hx+27*s,hy-63*s,hx+45*s,hy-45*s),(139,75,57),None)
    # eyes blink periodically, gaze angles down while drinking
    blink=(t%4.6)<.14
    for ex in (hx-22*s,hx+23*s):
        ey=hy-14*s
        if blink or action in ("lower","drink"):
            line(d,[(ex-7*s,ey),(ex+7*s,ey+2*s)],INK,3*s)
        else:
            ellipse(d,(ex-5*s,ey-5*s,ex+5*s,ey+6*s),(255,246,221),INK,2*s)
            ellipse(d,(ex-2*s,ey-3*s,ex+3*s,ey+4*s),INK,None)
    # muzzle pads, nose and mouth
    ellipse(d,(hx-25*s,hy+13*s,hx+3*s,hy+42*s),(247,224,187),None)
    ellipse(d,(hx+1*s,hy+13*s,hx+29*s,hy+42*s),(247,224,187),None)
    d.polygon([(hx-7*s,hy+17*s),(hx+8*s,hy+17*s),(hx+s,hy+28*s)],fill=INK)
    line(d,[(hx+s,hy+27*s),(hx+s,hy+40*s),(hx-9*s,hy+45*s)],INK,3*s)
    # Tongue flicks down during drinking.
    if action=="drink" and int(t*5)%3!=0:
        line(d,[(hx+2*s,hy+39*s),(hx+7*s,hy+56*s),(hx+3*s,hy+64*s)],(190,91,93),5*s)
    # whiskers
    for side in (-1,1):
        for k in range(2):
            yy=hy+28*s+k*7*s
            line(d,[(hx+side*16*s,yy),(hx+side*48*s,yy-5*s)],(105,78,57),2*s)

def draw_frame(scene,frame,frames,size,scene_number,scene_count,title):
    w,h=size
    t=frame/max(1,frames-1)*max(1.0,float(scene.get("duration",5)))
    im=Image.new("RGB",size,(239,204,151))
    d=ImageDraw.Draw(im)
    desert(d,t)
    # Pool appears in waterhole scenes and grows into view on reveal.
    if scene.get("water",False):
        waterhole(d,t)
    action=scene.get("animal_action","approach")
    movement=scene.get("movement","approach")
    if movement=="approach":
        x=lerp(190,775,min(1,t/max(1,float(scene.get("duration",5)))))
    elif movement=="exit":
        x=lerp(760,1350,min(1,t/max(1,float(scene.get("duration",5)))))
    else:
        x=760+math.sin(t*.45)*4
    lion(d,x,590,t,action,1.05)
    # Small animated dust puffs during approach.
    if movement=="approach":
        for k in range(4):
            px=x-112*s if False else x-95-k*17+math.sin(t*7+k)*4
            py=582-k*9
            r=5+k*2
            ellipse(d,(px-r,py-r,px+r,py+r),(225,178,125),None)
    # Typography stays outside the character silhouette.
    d.rounded_rectangle((48,38,w-48,112),radius=18,fill=(248,230,199),outline=(109,76,51),width=2)
    label(d,(76,76),title[:62],18,(106,79,57),"lm")
    d.rounded_rectangle((48,h-101,w-48,h-35),radius=16,fill=(248,237,216),outline=(165,127,91),width=2)
    label(d,(w//2,h-68),scene.get("caption",scene.get("heading","")),22,(68,51,39))
    progress=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    d.rounded_rectangle((48,h-20,w-48,h-13),radius=4,fill=(209,183,148))
    d.rounded_rectangle((48,h-20,48+int((w-96)*progress),h-13),radius=4,fill=(88,130,92))
    return im

def lerp(a,b,t):
    return a+(b-a)*t

engine.make_frame=draw_frame
def run(story_path,output):
    engine.run(story_path,output)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--script",default="demo/lion_water_2min.json")
    p.add_argument("--output",default="output/lion-water-documentary.mp4")
    a=p.parse_args()
    run(a.script,a.output)
