#!/usr/bin/env python3
"""Original illustrated elephant-family river sequence rendered through the narration engine."""
import math
from PIL import Image, ImageDraw
import engine

W,H=1280,720
INK=(48,55,54); SKIN=(119,132,126); LIGHT=(157,168,159); DARK=(83,99,94)
WATER=(50,139,159); FOAM=(185,226,220); BANK=(151,127,91); LEAF=(57,103,72)

def smooth(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def mix(a,b,t): return a+(b-a)*t
def line(d,pts,fill,width=4): d.line([(int(x),int(y)) for x,y in pts],fill=fill,width=max(1,int(width)),joint="curve")
def ellipse(d,b,fill,outline=INK,width=3): d.ellipse(tuple(int(v) for v in b),fill=fill,outline=outline,width=max(1,int(width)) if outline else 1)

def elephant(im,x,ground,t,scale=1.0,phase=0,pose="walk",calf=False,turn=0):
    d=ImageDraw.Draw(im)
    s=scale; bodyw=(145 if calf else 190)*s; bodyh=(105 if calf else 137)*s
    bob=math.sin(t*7+phase)*3*s if pose=="walk" else 0
    gy=ground+bob
    # four independently phased legs with visible foot lift and planted contact
    for idx,off in enumerate((-0.30,0.18,-0.05,0.42)):
        ph=t*5.2+phase+off*math.pi*2
        moving=pose in ("walk","depart","approach")
        stride=math.sin(ph)*17*s if moving else 0
        lift=max(0,math.cos(ph))*12*s if moving else 0
        lx=x+(-bodyw*.43 if idx<2 else bodyw*.35)+stride
        top=gy-bodyh*.15
        knee=gy-28*s-lift*.45
        foot=gy+lift
        col=LIGHT if idx in (0,2) else DARK
        line(d,[(lx,top),(lx+stride*.15,knee),(lx,foot)],INK,19*s)
        line(d,[(lx,top),(lx+stride*.15,knee),(lx,foot)],col,13*s)
        ellipse(d,(lx-14*s,foot-7*s,lx+19*s,foot+8*s),col,INK,3*s)
        for k in range(3):
            line(d,[(lx+8*s+k*4*s,foot+2*s),(lx+10*s+k*4*s,foot+6*s)],(211,211,194),2*s)
    # body and shoulder
    ellipse(d,(x-bodyw*.58,gy-bodyh*.82,x+bodyw*.52,gy+bodyh*.05),SKIN,INK,5*s)
    ellipse(d,(x-bodyw*.42,gy-bodyh*.79,x+bodyw*.38,gy-bodyh*.13),LIGHT,None)
    # ear silhouette with inner folds; ear shape varies with motion
    ear_swing=math.sin(t*2.1+phase)*7*s
    ear=[(x+bodyw*.20,gy-bodyh*.72),(x+bodyw*.56,gy-bodyh*.95+ear_swing),(x+bodyw*.78,gy-bodyh*.68),(x+bodyw*.73,gy-bodyh*.27),(x+bodyw*.48,gy-bodyh*.18)]
    d.polygon(ear,fill=(132,148,137),outline=INK)
    line(d,[(x+bodyw*.42,gy-bodyh*.68),(x+bodyw*.63,gy-bodyh*.78+ear_swing*.5),(x+bodyw*.63,gy-bodyh*.35)],(185,170,151),4*s)
    # head, cheek and eye
    hx=x+bodyw*.47; hy=gy-bodyh*.72
    ellipse(d,(hx-42*s,hy-49*s,hx+53*s,hy+51*s),SKIN,INK,4*s)
    ellipse(d,(hx-26*s,hy-22*s,hx-10*s,hy-6*s),(37,45,42),None)
    ellipse(d,(hx-22*s,hy-20*s,hx-17*s,hy-15*s),(245,240,220),None)
    # trunk: articulated curve with distinct action poses
    if pose=="drink": pts=[(hx+34*s,hy+8*s),(hx+66*s,hy+35*s),(hx+67*s,hy+76*s),(hx+47*s,hy+91*s)]
    elif pose=="stumble": pts=[(hx+33*s,hy+8*s),(hx+67*s,hy+25*s),(hx+87*s,hy+2*s),(hx+101*s,hy-25*s)]
    elif pose in ("search","call"): pts=[(hx+34*s,hy+7*s),(hx+71*s,hy+30*s),(hx+90*s,hy+4*s),(hx+101*s,hy-27*s)]
    elif pose=="reunite": pts=[(hx+34*s,hy+7*s),(hx+65*s,hy+43*s),(hx+89*s,hy+47*s),(hx+105*s,hy+26*s)]
    else: pts=[(hx+34*s,hy+8*s),(hx+62*s,hy+38*s+math.sin(t*3+phase)*7*s),(hx+63*s,hy+75*s),(hx+44*s,hy+91*s)]
    line(d,pts,INK,23*s); line(d,pts,SKIN,16*s)
    ellipse(d,(pts[-1][0]-8*s,pts[-1][1]-7*s,pts[-1][0]+8*s,pts[-1][1]+7*s),DARK,None)
    # tusks, small in calf
    if not calf:
        line(d,[(hx+14*s,hy+33*s),(hx+26*s,hy+56*s),(hx+38*s,hy+55*s)],(242,224,181),8*s)
    # wrinkles and skin texture
    for k in range(3):
        line(d,[(x-bodyw*.16+k*9*s,gy-bodyh*.25),(x-bodyw*.12+k*9*s,gy-bodyh*.12)],(103,119,112),2*s)
    return (hx,hy)

def background(t,scene):
    im=Image.new("RGB",(W,H),(195,220,202)); d=ImageDraw.Draw(im)
    # layered forest canopy and distant hills
    d.polygon([(0,300),(170,190),(360,285),(550,170),(770,280),(980,180),(1280,280),(1280,720),(0,720)],fill=(111,157,119))
    d.polygon([(0,385),(210,290),(410,375),(660,260),(900,375),(1110,280),(1280,360),(1280,720),(0,720)],fill=(76,128,91))
    for i in range(18):
        x=(i*89+int(t*5))%1380-40; y=255+(i%4)*35
        ellipse(d,(x-42,y-28,x+42,y+28),(57,111,76),None)
    d.rectangle((0,520,W,H),fill=(BANK[0],BANK[1],BANK[2]))
    # river current and animated highlights
    d.polygon([(0,440),(270,410),(510,452),(760,405),(1010,443),(1280,410),(1280,610),(0,610)],fill=WATER)
    for i in range(30):
        x=(i*71+int(t*43))%W; y=455+(i*29)%135
        line(d,[(x,y),(x+24+(i%4)*8,y-2),(x+38+(i%4)*8,y)],FOAM,2)
    # foreground gravel and reeds
    for i in range(26):
        x=(i*53+int(t*7))%W; y=612+(i%3)*24
        ellipse(d,(x,y,x+8,y+4),(202,185,145),None)
    return im

def make_frame(scene,frame,frames,size,scene_number,scene_count,title):
    w,h=size; duration=float(scene.get("_render_duration",10)); t=frame/max(1,frames-1)*duration
    im=background(t,scene); d=ImageDraw.Draw(im)
    action=scene.get("animal_action","approach")
    if scene_number==1:
        elephant(im,390,574,t,.98,0,"walk",False); elephant(im,675,590,t,.62,1.2,"walk",True)
        elephant(im,530,584,t,.78,2.1,"walk",True)
    elif scene_number==2:
        elephant(im,610,574,t,.69,1.1,"stumble",True)
        # moving splash crescents around calf
        for k in range(9):
            px=610+math.sin(t*4+k)*65; py=510+(k%3)*27
            d.arc((px-15,py-8,px+18,py+9),190,345,fill=FOAM,width=3)
    elif scene_number==3:
        elephant(im,790,574,t,1.05,0,"search",False)
        elephant(im,1000,586,t,.82,1.5,"call",False)
        for k in range(3):
            d.arc((850+k*17,365-k*10,960+k*17,475+k*10),205,330,fill=(232,245,224),width=3)
    elif scene_number==4:
        elephant(im,470,575,t,1.0,0,"reunite",False)
        elephant(im,670,585,t,.68,1.1,"stumble",True)
        elephant(im,880,585,t,.82,2.2,"walk",False)
        for k in range(10):
            px=680+math.sin(t*3+k)*75; py=522+(k%4)*18
            d.ellipse((px-3,py-5,px+3,py+5),fill=FOAM)
    elif scene_number==5:
        elephant(im,555,574,t,1.02,0,"reunite",False)
        elephant(im,700,585,t,.67,1.1,"reunite",True)
        elephant(im,885,585,t,.84,2.0,"walk",False)
    else:
        x=mix(500,1030,smooth(t/max(.1,duration)))
        elephant(im,x,574,t,.98,0,"depart",False)
        elephant(im,x+185,586,t,.68,1.2,"depart",True)
        elephant(im,x-170,580,t,.82,2.2,"depart",False)
    # cinematic shot label, subtle vignette-like bars, readable scene counter
    d.rounded_rectangle((48,34,500,83),radius=14,fill=(17,43,42),outline=(202,224,204),width=2)
    d.text((68,49),scene.get("heading",title),fill=(245,241,222))
    d.rounded_rectangle((0,0,w,12),radius=0,fill=(42,86,72))
    d.rounded_rectangle((0,h-12,w,h),radius=0,fill=(42,86,72))
    # scene-specific visual continuity marker
    progress=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    d.rectangle((48,h-27,w-48,h-21),fill=(181,202,183))
    d.rectangle((48,h-27,48+int((w-96)*progress),h-21),fill=(48,111,91))
    return im

engine.make_frame=make_frame
def run(story_path,output): engine.run(story_path,output)
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser(); p.add_argument("--script",default="demo/great_river_crossing_90s.json"); p.add_argument("--output",default="output/great-river-crossing.mp4")
 a=p.parse_args(); run(a.script,a.output)
