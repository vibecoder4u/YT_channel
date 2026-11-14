#!/usr/bin/env python3
"""Colorful, narration-synchronized wildlife explainer built from animated diagrams.

This is the deliberate fallback when character animation is not convincing:
no stick figures, no static slides, no stock footage. Each chapter animates a
different explanatory visual: habitat layers, sensory waves, scent trail,
hunting sequence, diet wheel, food web, and habitat protection.
"""
import argparse, math
from PIL import Image, ImageDraw
import engine

W,H=1280,720
BG=(244,248,241); INK=(35,53,48); MUTED=(101,121,110)
GREEN=(62,139,91); MINT=(151,207,166); GOLD=(244,180,67)
ORANGE=(226,119,68); BLUE=(91,157,198); PURPLE=(145,119,183)
PALETTE=[GREEN,GOLD,BLUE,ORANGE,PURPLE]

def mix(a,b,t):
    t=max(0,min(1,t)); return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
def rr(d,box,r=20,fill=(255,255,255),outline=None,width=2):
    d.rounded_rectangle(tuple(map(int,box)),radius=r,fill=fill,outline=outline,width=width)
def label(d,xy,s,size=20,color=INK,anchor="mm",bold=True):
    d.text(xy,str(s),font=engine.font(size,bold),fill=color,anchor=anchor)
def line(d,pts,color=INK,width=5):
    d.line([(int(x),int(y)) for x,y in pts],fill=color,width=width,joint="curve")
def dot(d,x,y,r,color,outline=None):
    d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r)),fill=color,outline=outline)
def arrow(d,a,b,color=GREEN,width=6):
    line(d,[a,b],color,width)
    ang=math.atan2(b[1]-a[1],b[0]-a[0]); n=16
    p=(b[0]-n*math.cos(ang-.55),b[1]-n*math.sin(ang-.55))
    q=(b[0]-n*math.cos(ang+.55),b[1]-n*math.sin(ang+.55))
    d.polygon([b,p,q],fill=color)
def fox_icon(d,cx,cy,s=1):
    # A small, consistent flat wildlife emblem used as a diagram symbol.
    orange=(211,103,51); cream=(250,226,184); dark=(70,55,44)
    d.ellipse((cx-49*s,cy-24*s,cx+35*s,cy+31*s),fill=orange,outline=dark,width=max(2,int(3*s)))
    d.polygon([(cx-26*s,cy-13*s),(cx-37*s,cy-59*s),(cx-3*s,cy-34*s)],fill=orange,outline=dark)
    d.polygon([(cx+2*s,cy-20*s),(cx+29*s,cy-62*s),(cx+31*s,cy-5*s)],fill=orange,outline=dark)
    d.ellipse((cx+16*s,cy-11*s,cx+63*s,cy+18*s),fill=cream)
    dot(d,cx+49*s,cy+1*s,5*s,dark)
    dot(d,cx+13*s,cy-9*s,4*s,(255,255,255)); dot(d,cx+14*s,cy-8*s,2*s,dark)
    line(d,[(cx-43*s,cy+6*s),(cx-85*s,cy-15*s),(cx-105*s,cy-4*s)],orange,max(8,int(15*s)))
    dot(d,cx-107*s,cy-4*s,9*s,cream)
def tree(d,x,y,s=1,phase=0):
    sway=math.sin(phase+x*.01)*5*s
    line(d,[(x,y),(x+sway,y-100*s)],(111,91,66),int(13*s))
    for ox,oy,r,c in [(-26,-103,37,(73,139,88)),(18,-126,44,(91,157,99)),(48,-91,31,(111,174,111))]:
        dot(d,x+ox*s+sway,y+oy*s,r*s,c)
def panel(d,box,title,subtitle=None):
    rr(d,box,26,(255,255,255),(220,230,219),2)
    x0,y0,x1,y1=box
    label(d,(x0+28,y0+31),title,22,INK,"lm")
    if subtitle: label(d,(x0+28,y0+62),subtitle,15,MUTED,"lm")
def habitat(d,t):
    # Three moving depth planes create parallax rather than a flat background.
    d.rectangle((0,180,W,590),fill=(224,238,220))
    for layer,(col,base,amp,speed) in enumerate([((190,218,188),380,36,3),((139,185,132),455,30,7),((91,145,94),555,23,13)]):
        pts=[(0,590)]
        for x in range(-20,W+40,20):
            y=base+math.sin(x*.008+t*speed*.02+layer)*amp
            pts.append((x,y))
        pts.extend([(W,590),(0,590)])
        d.polygon(pts,fill=col)
    for i in range(13):
        x=(i*119-int(t*(4+i%3)*2))%(W+150)-70
        tree(d,x,500+(i%3)*18,.65+(i%4)*.12,t)
    # drifting canopy light motes
    for i in range(24):
        x=(i*67+int(t*17))%W; y=220+(i*53)%290+math.sin(t+i)*7
        dot(d,x,y,2.5,(249,221,139))
def radar(d,cx,cy,t):
    for k in range(4):
        r=34+k*34+(t*28)%34
        d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=mix((196,222,204),GREEN,.35),width=3)
    a=t*1.8
    line(d,[(cx,cy),(cx+145*math.cos(a),cy+145*math.sin(a))],GREEN,5)
    fox_icon(d,cx,cy,.8)
def scent(d,t):
    pts=[]
    for i in range(100):
        u=i/99
        x=350+u*560
        y=420-160*math.sin(u*math.pi)+28*math.sin(u*13+t*2)
        pts.append((x,y))
    for i in range(0,96,3):
        x,y=pts[i]; x2,y2=pts[i+3]
        line(d,[(x,y),(x2,y2)],ORANGE,5)
    for i in range(14):
        u=(i/14+t*.14)%1
        x=350+u*560; y=420-160*math.sin(u*math.pi)+28*math.sin(u*13+t*2)
        dot(d,x,y,7,GOLD)
    fox_icon(d,260,445,.75)
    # scent source / pawprint-like target marker
    dot(d,930,260,35,(245,222,176),ORANGE)
    label(d,(930,260),"SCENT",14,INK)
def hunt(d,t):
    # Staged hunting sequence: listen -> focus -> pounce. Motion marker follows an arc.
    stage=(t%9)/9
    fox_x=300+min(1,stage*1.45)*440
    prey_x=860
    fox_icon(d,fox_x,430,.9)
    # Grass blades around the prey and target.
    for i in range(18):
        x=prey_x-80+i*10
        line(d,[(x,500),(x+math.sin(t+i)*8,460-(i%4)*8)],GREEN,3)
    dot(d,prey_x,450,17,(176,143,103))
    dot(d,prey_x+9,445,4,(255,255,255)); dot(d,prey_x+10,445,2,INK)
    if stage<.33:
        label(d,(640,245),"1  LISTEN",22,BLUE)
        for k in range(3):
            r=35+k*24+(t*25)%22
            d.arc((fox_x+25-r,390-r,fox_x+25+r,390+r),210,330,fill=BLUE,width=4)
    elif stage<.68:
        label(d,(640,245),"2  FOCUS",22,GOLD)
        for k in range(3):
            r=65+k*28
            d.arc((prey_x-r,450-r,prey_x+r,450+r),190,350,fill=GOLD,width=3)
    else:
        label(d,(640,245),"3  POUNCE",22,ORANGE)
        u=(stage-.68)/.32
        px=fox_x+u*120; py=390-110*math.sin(u*math.pi)
        dot(d,px,py,12,ORANGE)
        line(d,[(fox_x+80,390),(px,py)],ORANGE,5)
def diet_wheel(d,t):
    cx,cy=660,405
    items=[("SMALL MAMMALS",GREEN),("INSECTS",GOLD),("FRUIT",ORANGE),("BIRDS",BLUE),("OTHER FOOD",PURPLE)]
    for i,(txt,col) in enumerate(items):
        a=-math.pi/2+i*2*math.pi/len(items)
        x=cx+210*math.cos(a); y=cy+155*math.sin(a)
        pulse=1+0.07*math.sin(t*3-i)
        rr(d,(x-100*pulse,y-35*pulse,x+100*pulse,y+35*pulse),18,mix((255,255,255),col,.13),col,3)
        label(d,(x,y),txt,15,INK)
        arrow(d,(cx+70*math.cos(a),cy+50*math.sin(a)),(x-100*math.cos(a)*.7,y-35*math.sin(a)*.7),col,4)
    fox_icon(d,cx,cy,.72)
def food_web(d,t):
    nodes=[(390,300,"PLANTS",GREEN),(650,245,"INSECTS",GOLD),(900,320,"BIRDS",BLUE),(650,485,"MICE",ORANGE),(930,500,"FOX",PURPLE)]
    edges=[(0,1),(0,3),(1,2),(3,4),(2,4)]
    for a,b in edges:
        p=nodes[a][:2]; q=nodes[b][:2]
        arrow(d,p,q,mix(PALETTE[(a+b)%5],INK,.1),4)
    for i,(x,y,txt,col) in enumerate(nodes):
        r=62+3*math.sin(t*2-i)
        dot(d,x,y,r,mix((255,255,255),col,.22),col)
        label(d,(x,y),txt,17,INK)
    label(d,(650,585),"ENERGY MOVES THROUGH A CONNECTED COMMUNITY",16,MUTED)
def protect(d,t):
    # Habitat map with linked corridors; a moving pulse travels along safe routes.
    d.rounded_rectangle((245,210,1035,570),radius=42,fill=(225,239,220),outline=(177,205,174),width=3)
    for i in range(18):
        x=285+(i*43)%700; y=260+(i*71)%260
        tree(d,x,y,.45,t)
    route=[(340,430),(480,340),(625,410),(790,315),(930,420)]
    line(d,route,(255,255,255),24); line(d,route,GREEN,8)
    for i in range(5):
        x,y=route[i]; dot(d,x,y,17,GOLD,(255,255,255))
    u=(t*.22)%1
    seg=min(3,int(u*4)); f=u*4-seg
    x=route[seg][0]*(1-f)+route[seg+1][0]*f
    y=route[seg][1]*(1-f)+route[seg+1][1]*f
    dot(d,x,y,13,ORANGE,(255,255,255))
    label(d,(640,615),"CONNECTED HABITATS GIVE WILDLIFE ROOM TO MOVE",17,GREEN)
def draw_frame(scene,frame,frames,size,scene_number,scene_count,title):
    w,h=size
    t=frame/max(1,frames-1)*max(1,float(scene.get("duration",5)))
    im=Image.new("RGB",size,BG); d=ImageDraw.Draw(im)
    # Soft top band and editorial framing.
    d.rectangle((0,0,w,14),fill=GREEN)
    label(d,(62,58),title[:65],18,MUTED,"lm")
    label(d,(w-62,58),f"CHAPTER {scene_number:02d} / {scene_count:02d}",15,MUTED,"rm")
    heading=scene.get("heading","Wildlife explained")
    label(d,(64,132),heading,37,INK,"lm")
    sub=scene.get("caption",scene.get("takeaway",""))
    label(d,(65,177),sub[:92],17,MUTED,"lm",False)
    panel(d,(55,215,w-55,h-90),scene.get("visual_title","THE WOODLAND SYSTEM"),scene.get("visual_subtitle"))
    kind=scene.get("diagram","habitat")
    if kind=="habitat": habitat(d,t)
    elif kind=="senses": radar(d,650,405,t)
    elif kind=="scent": scent(d,t)
    elif kind=="hunt": hunt(d,t)
    elif kind=="diet": diet_wheel(d,t)
    elif kind=="web": food_web(d,t)
    elif kind=="protect": protect(d,t)
    # Small animated chapter progress indicator.
    prog=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    rr(d,(55,h-48,w-55,h-37),6,(220,229,219))
    rr(d,(55,h-48,55+(w-110)*prog,h-37),6,GREEN)
    # Captions are short, readable and anchored consistently.
    return im

engine.make_frame=draw_frame

def run(story_path,output):
    engine.run(story_path,output)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--script",default="demo/forest_fox_2min.json")
    p.add_argument("--output",default="output/forest-fox-explainer.mp4")
    a=p.parse_args(); run(a.script,a.output)
