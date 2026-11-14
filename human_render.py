#!/usr/bin/env python3
"""Three-character illustrated interaction prototype: The Rescue at the River."""
import argparse, math
from PIL import Image, ImageDraw
import engine
W,H=1280,720
INK=(38,43,48); SKIN=(224,166,125); DARK=(48,47,54); TEAL=(36,133,139); MUSTARD=(207,151,55); OLIVE=(100,126,75); PALE=(244,231,207)
def smooth(v):
 v=max(0,min(1,v)); return v*v*(3-2*v)
def line(d,pts,c=INK,w=6): d.line([(int(x),int(y)) for x,y in pts],fill=c,width=max(1,int(w)),joint="curve")
def ellipse(d,b,c,outline=INK,w=3): d.ellipse(tuple(int(v) for v in b),fill=c,outline=outline,width=max(1,int(w)) if outline else 1)
def bg(t):
 im=Image.new("RGB",(W,H),(190,218,220)); d=ImageDraw.Draw(im)
 d.polygon([(0,300),(180,205),(350,290),(550,190),(770,290),(1000,200),(1280,290),(1280,720),(0,720)],fill=(111,151,127))
 d.polygon([(0,390),(250,315),(450,395),(700,300),(930,390),(1120,315),(1280,370),(1280,720),(0,720)],fill=(93,132,100))
 d.polygon([(0,530),(1280,500),(1280,720),(0,720)],fill=(153,132,99))
 d.polygon([(430,480),(540,445),(680,465),(810,425),(970,470),(1120,450),(1280,500),(1280,720),(430,720)],fill=(65,147,164))
 for i in range(12):
  x=(i*113+int(t*28))%850+430; y=520+(i%4)*36
  d.arc((x,y,x+75,y+12),180,350,fill=(177,226,222),width=3)
 # stepping stones
 for x,y in [(590,492),(710,476),(835,488),(960,470)]: ellipse(d,(x-34,y-12,x+35,y+14),(130,126,105),None)
 return im
def person(im,x,ground,t,kind,pose="idle",scale=1.0,look=0):
 d=ImageDraw.Draw(im); shirt={"maya":TEAL,"arun":MUSTARD,"leena":OLIVE}[kind]
 # pose values control arm/leg articulation
 walk=pose in ("walk","arrive","depart"); phase=t*7+(0 if kind=="maya" else 2 if kind=="arun" else 4)
 stride=math.sin(phase)*20 if walk else 0; lift=max(0,math.cos(phase))*13 if walk else 0
 hip=(x,ground-75*scale); shoulder=(x,ground-180*scale)
 # legs behind torso
 for side in (-1,1):
  dx=side*13*scale; swing=stride*(1 if side==1 else -1)
  knee=(x+dx+swing*.45,ground-39*scale-lift*.3)
  ankle=(x+dx+swing,ground-lift)
  line(d,[(hip[0]+dx*.5,hip[1]),knee,ankle],DARK,14*scale)
  line(d,[(ankle[0]-8*scale,ankle[1]),(ankle[0]+14*scale,ankle[1])],(48,45,43),9*scale)
 # torso and backpack
 if kind=="arun": ellipse(d,(x-37*scale,ground-192*scale,x-12*scale,ground-105*scale),(119,91,65),None)
 ellipse(d,(x-27*scale,ground-190*scale,x+28*scale,ground-76*scale),shirt,INK,3*scale)
 # neck and head
 ellipse(d,(x-9*scale,ground-211*scale,x+10*scale,ground-184*scale),SKIN,None)
 ellipse(d,(x-25*scale+look*2,ground-254*scale,x+25*scale+look*2,ground-202*scale),SKIN,INK,3*scale)
 # hair
 if kind=="maya": ellipse(d,(x-27*scale,ground-260*scale,x+27*scale,ground-225*scale),DARK,None)
 elif kind=="arun":
  ellipse(d,(x-25*scale,ground-260*scale,x+25*scale,ground-239*scale),DARK,None)
 else:
  ellipse(d,(x-26*scale,ground-260*scale,x+25*scale,ground-231*scale),DARK,None); ellipse(d,(x+15*scale,ground-245*scale,x+33*scale,ground-209*scale),DARK,None)
 # face eyes and mouth
 ex=x+look*2
 ellipse(d,(ex-10*scale,ground-235*scale,ex-5*scale,ground-230*scale),INK,None)
 ellipse(d,(ex+6*scale,ground-235*scale,ex+11*scale,ground-230*scale),INK,None)
 line(d,[(ex-5*scale,ground-218*scale),(ex+5*scale,ground-217*scale)],(111,62,54),2*scale)
 # arms, gesture poses
 if pose=="point" or (kind=="maya" and pose=="plan"):
  arm=[(x-20*scale,ground-174*scale),(x-48*scale,ground-205*scale),(x-78*scale,ground-225*scale)]
 elif pose=="reach" or pose=="slip":
  arm=[(x-20*scale,ground-174*scale),(x-55*scale,ground-205*scale),(x-80*scale,ground-235*scale)]
 elif pose=="pull":
  arm=[(x-20*scale,ground-174*scale),(x-54*scale,ground-155*scale),(x-78*scale,ground-160*scale)]
 else:
  arm=[(x-20*scale,ground-174*scale),(x-40*scale,ground-145*scale),(x-42*scale,ground-125*scale)]
 line(d,arm,SKIN,11*scale); ellipse(d,(arm[-1][0]-6,arm[-1][1]-6,arm[-1][0]+6,arm[-1][1]+6),SKIN,None)
 arm2=[(x+20*scale,ground-174*scale),(x+44*scale,ground-145*scale),(x+43*scale,ground-125*scale)]
 if pose in ("pull","rescue"): arm2=[(x+20*scale,ground-174*scale),(x+52*scale,ground-160*scale),(x+78*scale,ground-160*scale)]
 line(d,arm2,SKIN,11*scale); ellipse(d,(arm2[-1][0]-6,arm2[-1][1]-6,arm2[-1][0]+6,arm2[-1][1]+6),SKIN,None)
def frame(scene,frame,frames,size,scene_number,scene_count,title):
 w,h=size; dur=float(scene.get("_render_duration",scene.get("duration",8))); t=frame/max(1,frames-1)*dur
 im=bg(t); d=ImageDraw.Draw(im); action=scene.get("human_action","arrive")
 if scene_number==1:
  xs=[300+math.sin(t)*18,490+math.sin(t+1)*18,680+math.sin(t+2)*18]; poses=["walk","walk","walk"]
 elif scene_number==2:
  xs=[340,540,740]; poses=["point","idle","point"]
 elif scene_number==3:
  xs=[360,650,850]; poses=["reach","slip","reach"]
 elif scene_number==4:
  xs=[330,690+math.sin(t*2)*24,500]; poses=["pull","reach","pull"]
 else:
  xs=[390,570,750]; poses=["walk","walk","walk"]
 # Draw Leena first, Arun middle, Maya foreground for readable overlap.
 for idx in (2,1,0):
  kind=("maya","arun","leena")[idx]; pose=poses[idx]
  if scene_number==3 and kind=="arun": pose="slip"
  if scene_number==4: pose="pull" if kind in ("maya","leena") else "reach"
  if scene_number==2 and kind=="maya": pose="point"
  person(im,xs[idx],600,t,kind,pose,1.0, 1 if scene_number==2 and kind=="arun" else 0)
 d=ImageDraw.Draw(im)
 # Rope is a shared prop connecting Leena/Maya's hands to Arun during rescue.
 if scene_number==4:
  rope_y=438+math.sin(t*3)*5
  line(d,[(xs[2]-78,440),(xs[0]+78,rope_y),(xs[1]-72,455)],(193,151,83),7)
  for i in range(4):
   x=570+i*34; d.arc((x,500-i*4,x+65,516+i*4),190,350,fill=(193,232,226),width=3)
 if scene_number==3:
  d.arc((xs[1]-65,360,xs[1]+70,470),205,335,fill=(250,244,218),width=4)
 # label and subtitle panel
 d.rounded_rectangle((42,30,w-42,86),radius=14,fill=(250,242,222),outline=(88,91,75),width=2)
 d.text((66,58),scene.get("heading",title),font=engine.font(21,True),fill=INK,anchor="lm")
 d.rounded_rectangle((42,h-82,w-42,h-30),radius=12,fill=(250,242,222),outline=(88,91,75),width=2)
 d.text((w//2,h-56),scene.get("caption",""),font=engine.font(19,False),fill=INK,anchor="mm")
 progress=((scene_number-1)+frame/max(1,frames))/scene_count
 d.rounded_rectangle((42,h-17,w-42,h-10),radius=3,fill=(205,195,171))
 d.rounded_rectangle((42,h-17,42+int((w-84)*progress),h-10),radius=3,fill=(45,132,123))
 return im
engine.make_frame=frame
def run(story,output): engine.run(story,output)
if __name__=="__main__":
 p=argparse.ArgumentParser(); p.add_argument("--script",default="demo/rescue_at_the_river_55s.json"); p.add_argument("--output",default="output/rescue-at-the-river-55s.mp4"); a=p.parse_args(); run(a.script,a.output)
