#!/usr/bin/env python3
"""Original illustrated forest-animal renderer layered over the narration engine.

Draws a continuous woodland environment and an articulated fox with animated
legs, tail, ears, head, eyes and sniffing motion. No stock images are used.
"""
import argparse
import math
from PIL import Image, ImageDraw
import engine

W, H = 1280, 720
INK = (48, 43, 39)
CREAM = (250, 246, 231)
GREEN = (49, 91, 65)

def lerp(a, b, t):
    return a + (b-a)*t

def ellipse(d, box, fill, outline=None, width=1):
    d.ellipse(tuple(int(v) for v in box), fill=fill, outline=outline, width=width)

def polygon(d, pts, fill, outline=None):
    d.polygon([(int(x), int(y)) for x,y in pts], fill=fill)
    if outline:
        d.line([(int(x),int(y)) for x,y in pts+[pts[0]]], fill=outline, width=3, joint="curve")

def forest_background(im, t, scene):
    d=ImageDraw.Draw(im)
    # Dawn sky and distant mist bands.
    d.rectangle((0,0,W,H), fill=(205,222,205))
    d.rectangle((0,0,W,390), fill=(190,214,198))
    for i in range(5):
        yy=245+i*48
        drift=math.sin(t*.18+i)*24
        d.ellipse((int(-180+drift),yy-28,int(760+drift),yy+55),fill=(211,225,207))
    # Distant tree trunks and rounded canopies.
    for i in range(13):
        x=(i*137-((t*7)%137))
        top=115+(i%4)*32
        col=[(89,128,91),(104,143,101),(76,119,85)][i%3]
        d.rectangle((x+30,top+85,x+58,520),fill=(111,105,78))
        for ox,oy,r in [(-30,80,78),(35,52,94),(83,96,72),(18,0,68)]:
            ellipse(d,(x+ox-r,top+oy-r,x+ox+r,top+oy+r),col)
    # Forest floor with a softly undulating horizon.
    d.polygon([(0,450),(160,420),(330,462),(510,430),(710,458),(910,418),(1100,450),(1280,425),(1280,720),(0,720)],fill=(83,125,77))
    d.polygon([(0,540),(230,505),(450,552),(710,515),(940,552),(1140,510),(1280,535),(1280,720),(0,720)],fill=(63,105,68))
    # Foreground ferns/leaves move gently in the breeze.
    for i in range(28):
        x=(i*53+int(math.sin(t*.7+i)*7))%W
        y=590+(i%4)*28
        length=24+(i%5)*7
        d.line((x,y,x-12,y-length),fill=(42,91,57),width=4)
        d.ellipse((x-29,y-length-7,x-7,y-length+9),fill=(68,132,78))
        d.ellipse((x-7,y-length-18,x+15,y-length+1),fill=(77,145,83))
    # A few floating motes and light shafts.
    for i in range(18):
        x=(i*83+int(t*12*(1 if i%2 else -1)))%W
        y=170+(i*47)%330+int(math.sin(t+i)*8)
        ellipse(d,(x,y,x+4,y+4),(238,228,164))
    # Dark framing foliage creates depth.
    for side in (0,1):
        x=0 if side==0 else W
        for j in range(5):
            yy=30+j*75
            bx=x+(1 if side==0 else -1)*j*13
            ellipse(d,(bx-70,yy-55,bx+95,yy+80),(39,83,57))
    # Scene label.
    label=scene.get("environment_label","WOODLAND • DAWN")
    d.rounded_rectangle((54,42,370,88),radius=18,fill=(24,56,43))
    d.text((76,55),label,font=engine.font(18,True),fill=(245,241,218))

def draw_fox(d, x, ground, t, action="walk", scale=1.0):
    s=scale
    bob=math.sin(t*5.2)*4 if action=="walk" else math.sin(t*2.2)*2
    x=float(x); ground=float(ground+bob)
    orange=(202,103,45); light=(235,151,75); cream=(247,225,185)
    dark=(65,48,39); inner=(105,60,48)
    # Tail swings behind body with a bright cream tip.
    tail_angle=math.sin(t*2.7)*.20
    tx=x-105*s; ty=ground-94*s
    tipx=tx-93*s*math.cos(tail_angle)
    tipy=ty-45*s+math.sin(tail_angle)*38*s
    d.line((x-38*s,ground-93*s,tx,ty,tipx,tipy),fill=dark,width=int(42*s))
    d.line((x-38*s,ground-93*s,tx,ty,tipx,tipy),fill=orange,width=int(35*s))
    ellipse(d,(tipx-19*s,tipy-17*s,tipx+19*s,tipy+17*s),cream)
    # Torso, shoulder and haunch.
    ellipse(d,(x-112*s,ground-151*s,x+57*s,ground-30*s),orange,dark,int(4*s))
    ellipse(d,(x-92*s,ground-126*s,x+35*s,ground-40*s),light)
    ellipse(d,(x-112*s,ground-114*s,x-30*s,ground-40*s),orange)
    # White chest and belly.
    polygon(d,[(x+5*s,ground-125*s),(x+53*s,ground-107*s),(x+28*s,ground-48*s),(x-20*s,ground-57*s)],cream)
    # Head turns slightly toward the camera while sniffing.
    turn=math.sin(t*1.1)*.12
    hx=x+62*s+math.sin(turn)*8*s
    hy=ground-157*s+(math.sin(t*2.8)*3*s if action=="sniff" else 0)
    # Neck and cheek.
    ellipse(d,(x+20*s,ground-169*s,x+105*s,ground-95*s),light,dark,int(3*s))
    ellipse(d,(hx-40*s,hy-42*s,hx+43*s,hy+36*s),orange,dark,int(4*s))
    # Pointed ears with inner ear detail; ears twitch independently.
    twitch=math.sin(t*3.8)*4*s
    polygon(d,[(hx-30*s,hy-18*s),(hx-43*s,hy-91*s+twitch),(hx+2*s,hy-48*s)],orange,dark)
    polygon(d,[(hx+3*s,hy-28*s),(hx+28*s,hy-91*s-twitch),(hx+40*s,hy-12*s)],orange,dark)
    polygon(d,[(hx-30*s,hy-36*s),(hx-35*s,hy-77*s+twitch),(hx-5*s,hy-48*s)],inner)
    polygon(d,[(hx+13*s,hy-35*s),(hx+25*s,hy-77*s-twitch),(hx+31*s,hy-22*s)],inner)
    # White muzzle and nose.
    ellipse(d,(hx+8*s,hy-5*s,hx+64*s,hy+29*s),cream)
    ellipse(d,(hx+48*s,hy+2*s,hx+62*s,hy+15*s),dark)
    # Eye blinks briefly and gaze shifts.
    blink=(t%4.7)<.16
    eye_x=hx+17*s; eye_y=hy-13*s
    if blink:
        d.line((eye_x-7*s,eye_y,eye_x+7*s,eye_y),fill=dark,width=max(2,int(3*s)))
    else:
        ellipse(d,(eye_x-5*s,eye_y-7*s,eye_x+5*s,eye_y+7*s),(250,246,222))
        ellipse(d,(eye_x-2*s,eye_y-4*s,eye_x+3*s,eye_y+4*s),dark)
    # Whiskers and mouth.
    d.line((hx+35*s,hy+18*s,hx+78*s,hy+9*s),fill=(111,83,65),width=2)
    d.line((hx+35*s,hy+22*s,hx+76*s,hy+29*s),fill=(111,83,65),width=2)
    d.arc((hx+23*s,hy+14*s,hx+48*s,hy+39*s),5,110,fill=dark,width=2)
    # Four articulated legs. Opposing stride keeps feet planted in a walk.
    phase=t*6.4
    for idx, lx in enumerate((x-75*s,x-12*s)):
        for side in (0,1):
            hipx=lx+(side*16-8)*s
            swing=math.sin(phase+(idx+side)*math.pi)*24*s if action in ("walk","trot") else 0
            knee=(hipx+swing*.45,ground-50*s+abs(swing)*.12)
            foot=(hipx+swing,ground-3*s)
            d.line((hipx,ground-83*s,knee[0],knee[1],foot[0],foot[1]),fill=dark,width=max(4,int(13*s)),joint="curve")
            d.line((hipx,ground-83*s,knee[0],knee[1],foot[0],foot[1]),fill=orange,width=max(3,int(8*s)),joint="curve")
            ellipse(d,(knee[0]-5*s,knee[1]-5*s,knee[0]+5*s,knee[1]+5*s),light)
            d.line((foot[0]-3*s,foot[1],foot[0]+17*s,foot[1]+2*s),fill=dark,width=max(4,int(9*s)))
    # Nose dips and rises in a sniffing action.
    if action=="sniff":
        d.line((hx+55*s,hy+20*s,hx+84*s,hy+29*s),fill=cream,width=3)
        for k in range(3):
            px=hx+84*s+k*8*s
            py=hy+30*s-int((t*20+k*13)%18)
            ellipse(d,(px,py,px+4*s,py+4*s),(228,221,176))

def draw_scene(scene, frame, frames, size, scene_number, scene_count, title):
    w,h=size
    t=frame/max(1,frames-1)*max(1.0,float(scene.get("duration",5)))
    im=Image.new("RGB",size)
    # Render background at target size.
    bg=Image.new("RGB",(W,H))
    forest_background(bg,t,scene)
    if size!=(W,H):
        bg=bg.resize(size)
    im.paste(bg)
    d=ImageDraw.Draw(im)
    # Animal traverses a measured path, then pauses to sniff or look around.
    movement=scene.get("movement","walk")
    if movement=="walk":
        x=lerp(240,1010,min(1,t/max(1,float(scene.get("duration",5)))))
    elif movement=="enter":
        x=lerp(-80,650,min(1,t/max(1,float(scene.get("duration",5)))))
    elif movement=="exit":
        x=lerp(650,1370,min(1,t/max(1,float(scene.get("duration",5)))))
    else:
        x=650+math.sin(t*.5)*10
    action=scene.get("animal_action","walk")
    draw_fox(d,x,594,t,action,1.12)
    # Foreground grass blades overlap the paws to seat the character in the world.
    for i in range(45):
        gx=(i*31+int(t*4))%w
        gy=610+(i%3)*22
        d.line((gx,gy,gx-7,gy-24-(i%4)*4),fill=(39,87,54),width=3)
    # Editorial title, narration caption and chapter progress.
    d.rounded_rectangle((48,110,w-48,184),radius=18,fill=(25,52,42))
    heading=scene.get("heading","A life in the forest")
    d.text((76,127),heading[:54],font=engine.font(34,True),fill=CREAM)
    d.rounded_rectangle((48,h-108,w-48,h-36),radius=16,fill=(250,246,231),outline=(216,209,185),width=2)
    caption=scene.get("caption",scene.get("takeaway",""))
    d.text((w//2,h-72),caption[:100],font=engine.font(23,True),fill=(48,61,49),anchor="mm")
    progress=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    d.rounded_rectangle((48,h-20,w-48,h-13),radius=4,fill=(207,215,197))
    d.rounded_rectangle((48,h-20,48+int((w-96)*progress),h-13),radius=4,fill=(218,145,65))
    return im

_original_make_frame=engine.make_frame
def make_frame(scene,frame,frames,size,scene_number,scene_count,title):
    return draw_scene(scene,frame,frames,size,scene_number,scene_count,title)

engine.make_frame=make_frame

def run(story_path,output):
    engine.run(story_path,output)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Render an illustrated forest animal documentary")
    parser.add_argument("--script",default="demo/forest_fox_2min.json")
    parser.add_argument("--output",default="output/forest-fox-documentary.mp4")
    args=parser.parse_args()
    run(args.script,args.output)
