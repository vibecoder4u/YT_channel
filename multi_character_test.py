#!/usr/bin/env python3
"""Three-anatomy animation benchmark: dog, bird and human in one timed scene.

This is a deterministic rig/motion integration test, not an AI art generator.
Each subject has a separate anatomy model and motion function. The shared
director timeline controls shots, focus and camera framing.
"""
from __future__ import annotations
import argparse, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DURATION = 1280, 720, 24, 12.0
INK=(38,43,46); CREAM=(247,241,225)

def clamp(x): return max(0.0,min(1.0,x))
def smooth(x):
    x=clamp(x); return x*x*(3-2*x)
def mix(a,b,t): return a+(b-a)*t
def ellipse(d, box, fill, outline=INK, width=3):
    d.ellipse(tuple(int(v) for v in box), fill=fill, outline=outline, width=width)
def poly(d, pts, fill, outline=INK, width=3):
    p=[(int(x),int(y)) for x,y in pts]
    d.polygon(p,fill=fill)
    if outline and len(p)>1: d.line(p+[p[0]],fill=outline,width=width,joint="curve")
def line(d, pts, fill, width=6):
    d.line([(int(x),int(y)) for x,y in pts],fill=fill,width=max(1,int(width)),joint="curve")
def font(size,bold=False):
    candidates=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        try: return ImageFont.truetype(p,size)
        except OSError: pass
    return ImageFont.load_default()
def label(d,xy,text,size=18,color=INK,bold=True):
    d.text(xy,text,font=font(size,bold),fill=color,anchor="mm")

def background(t, shot):
    im=Image.new("RGB",(W,H),(224,235,226)); d=ImageDraw.Draw(im)
    # layered woodland / park backdrop with independently drifting depth planes
    d.rectangle((0,0,W,420),fill=(201,222,218))
    ellipse(d,(930,65,1090,225),(248,226,174),None,0)
    for layer,(base,col,amp,speed) in enumerate([
        (350,(180,207,185),28,2.2),(430,(127,170,133),34,4.5),(520,(77,126,88),25,7.0)]):
        pts=[(0,H)]
        for x in range(-20,W+40,16):
            y=base+math.sin(x*.008+t*speed+layer)*amp
            pts.append((x,y))
        pts.extend([(W,H)])
        d.polygon(pts,fill=col)
    # tree trunks and canopy, parallax varies by layer
    for i in range(11):
        x=(i*151-int(t*(4+i%3)*3))%(W+160)-80
        y=410+(i%3)*22
        d.rectangle((x-13,y-180,x+15,610),fill=(104,91,70))
        for ox,oy,r,c in [(-35,-180,58,(81,139,94)),(22,-210,70,(92,151,100)),(66,-160,53,(73,128,88))]:
            ellipse(d,(x+ox-r,y+oy-r,x+ox+r,y+oy+r),c,None,0)
    # path and foreground grass
    d.polygon([(0,585),(250,555),(510,590),(790,552),(1040,585),(1280,550),(1280,720),(0,720)],fill=(169,169,119))
    d.polygon([(0,640),(250,610),(510,645),(790,608),(1040,640),(1280,605),(1280,720),(0,720)],fill=(117,145,91))
    for i in range(90):
        x=(i*47+int(math.sin(t*.7+i)*5))%W; y=610+(i%5)*20
        line(d,[(x,y),(x-5+(i%3)*5,y-18-(i%4)*5)],(65,113,72),2)
    return im

def draw_dog(im, x, ground, t, scale=1.0, action="walk", facing=1):
    """Quadruped: shoulder/hip gait, hock/knee flex, head, muzzle, ears and tail."""
    d=ImageDraw.Draw(im); s=scale
    walk=1.0 if action in ("walk","trot") else 0.0
    cycle=t*2*math.pi*(1.35 if action=="walk" else 2.0)
    bob=abs(math.sin(cycle))*5*walk + (math.sin(t*2)*2 if not walk else 0)
    g=ground-bob
    coat=(178,119,73); light=(213,158,104); cream=(244,222,183); dark=(77,55,43)
    # tail pivot, wagging independently
    wag=math.sin(t*5.2)*.32
    tail=[(x-92*s,g-88*s),(x-145*s,g-115*s),(x-188*s,g-104*s+wag*28*s)]
    line(d,tail,dark,22*s); line(d,tail,(190,128,80),15*s)
    ellipse(d,(x-200*s,g-116*s+wag*28*s,x-174*s,g-90*s+wag*28*s),cream,None,0)
    # far-side legs then body mass
    for idx,hx in enumerate((x-65*s,x+67*s)):
        for side in (0,1):
            phase=cycle+idx*math.pi+(side*math.pi)
            swing=math.sin(phase)*23*s*walk
            lift=max(0,math.cos(phase))*13*s*walk
            hip=(hx+(side*13-6)*s,g-63*s)
            knee=(hx+swing*.48,g-31*s-lift*.5)
            paw=(hx+swing,g-2*s-lift)
            col=(143,91,58) if side==0 else coat
            line(d,[hip,knee,paw],dark,17*s); line(d,[hip,knee,paw],col,11*s)
            ellipse(d,(knee[0]-7*s,knee[1]-7*s,knee[0]+7*s,knee[1]+7*s),light,None,0)
            ellipse(d,(paw[0]-13*s,paw[1]-7*s,paw[0]+17*s,paw[1]+6*s),dark,None,0)
    # torso, shoulder, chest
    ellipse(d,(x-125*s,g-151*s,x+112*s,g-35*s),coat,dark,int(4*s))
    ellipse(d,(x-88*s,g-133*s,x+79*s,g-47*s),light,None,0)
    poly(d,[(x+30*s,g-128*s),(x+91*s,g-110*s),(x+65*s,g-48*s),(x+8*s,g-55*s)],cream,None,0)
    # neck and head
    ellipse(d,(x+58*s,g-157*s,x+134*s,g-78*s),coat,dark,int(3*s))
    hx=x+119*s*facing; hy=g-164*s+math.sin(t*3)*2*s
    ellipse(d,(hx-39*s,hy-43*s,hx+43*s,hy+35*s),coat,dark,int(4*s))
    # floppy ears bounce
    ear=math.sin(t*5.5)*9*s
    poly(d,[(hx-24*s,hy-21*s),(hx-50*s,hy-61*s+ear),(hx-45*s,hy+9*s),(hx-21*s,hy+14*s)],(112,69,48),dark,int(3*s))
    poly(d,[(hx+17*s,hy-23*s),(hx+43*s,hy-59*s-ear),(hx+45*s,hy+12*s),(hx+23*s,hy+15*s)],(112,69,48),dark,int(3*s))
    # muzzle, nose, eye and cheek markings
    ellipse(d,(hx+5*s,hy-1*s,hx+65*s,hy+31*s),cream,None,0)
    ellipse(d,(hx+52*s,hy+4*s,hx+66*s,hy+18*s),dark,None,0)
    ellipse(d,(hx+5*s,hy-19*s,hx+17*s,hy-5*s),(250,246,225),dark,int(2*s))
    ellipse(d,(hx+10*s,hy-17*s,hx+15*s,hy-7*s),dark,None,0)
    line(d,[(hx+30*s,hy+20*s),(hx+40*s,hy+25*s),(hx+52*s,hy+19*s)],dark,2*s)
    # collar and tag
    line(d,[(x+67*s,g-121*s),(x+123*s,g-112*s)],(44,111,133),9*s)
    ellipse(d,(x+102*s,g-107*s,x+119*s,g-87*s),(237,186,76),dark,int(2*s))

def rotate_point(cx,cy,x,y,a):
    ca,sa=math.cos(a),math.sin(a)
    return (cx+x*ca-y*sa,cy+x*sa+y*ca)

def draw_bird(im,x,y,t,scale=1.0,action="fly",facing=1):
    """Avian rig: shoulder-driven wings, primaries, tail fan, beak and tucked legs."""
    d=ImageDraw.Draw(im); s=scale
    flap=math.sin(t*2*math.pi*2.1)
    wing_angle=flap*.82 if action=="fly" else .10*math.sin(t*2)
    body=(55,132,155); wing=(39,103,130); light=(115,183,190); dark=(36,62,70); gold=(231,170,66)
    # tail feathers fan and adjust for pitch
    for i in range(5):
        off=(i-2)*9*s
        poly(d,[(x-49*s,y+12*s),(x-112*s,y+38*s+off),(x-57*s,y+30*s+off*.25)],light,dark,int(2*s))
    # far wing behind body; shoulder pivot and feather fingers
    for side in (-1,1):
        a=wing_angle*side
        shoulder=(x-3*s,y-14*s)
        local=[(0,0),(-24*s,-35*s),( -70*s,-92*s),(-100*s,-112*s),(-91*s,-49*s),(-58*s,-6*s)]
        pts=[rotate_point(*shoulder,px,py,a) for px,py in local]
        poly(d,pts,wing,dark,int(3*s))
        for k in range(4):
            bx,by=rotate_point(*shoulder,-62*s-k*7*s,-35*s+k*9*s,a)
            ex,ey=rotate_point(*shoulder,-104*s-k*2*s,-84*s+k*14*s,a)
            line(d,[(bx,by),(ex,ey)],light,3*s)
    # torso, throat and head
    ellipse(d,(x-67*s,y-35*s,x+56*s,y+42*s),body,dark,int(3*s))
    ellipse(d,(x-22*s,y-12*s,x+50*s,y+36*s),(225,222,190),None,0)
    ellipse(d,(x+18*s,y-77*s,x+91*s,y-4*s),body,dark,int(3*s))
    # crown feathers
    poly(d,[(x+41*s,y-68*s),(x+48*s,y-105*s),(x+59*s,y-75*s),(x+68*s,y-108*s),(x+75*s,y-69*s)],light,dark,int(2*s))
    # beak points forward; slight open/close on chirp
    open_beak=(math.sin(t*9)>0.65)
    poly(d,[(x+76*s,y-47*s),(x+119*s,y-34*s),(x+78*s,y-22*s)],gold,dark,int(2*s))
    if open_beak:
        poly(d,[(x+79*s,y-22*s),(x+111*s,y-14*s),(x+80*s,y-11*s)],(197,117,51),dark,int(2*s))
    ellipse(d,(x+57*s,y-54*s,x+68*s,y-42*s),(255,248,218),dark,int(2*s))
    ellipse(d,(x+61*s,y-52*s,x+66*s,y-44*s),dark,None,0)
    # legs trail behind body
    for i in range(2):
        lx=x-20*s+i*25*s
        line(d,[(lx,y+34*s),(lx-8*s,y+55*s),(lx-18*s,y+58*s)],gold,4*s)
        for toe in range(3):
            line(d,[(lx-18*s,y+58*s),(lx-25*s+toe*7*s,y+65*s)],gold,2*s)

def draw_human(im,x,ground,t,scale=1.0,action="walk"):
    """Biped rig: pelvis, torso, shoulder/elbow, hip/knee, head and hand gesture."""
    d=ImageDraw.Draw(im); s=scale
    cycle=t*2*math.pi*1.25
    walk=action=="walk"
    stride=math.sin(cycle) if walk else 0
    bob=abs(math.sin(cycle))*5 if walk else math.sin(t*2)*1.5
    g=ground-bob
    skin=(190,126,91); skinlight=(218,160,119); hair=(48,43,42)
    jacket=(43,112,133); jacketlight=(73,153,165); pants=(49,66,83); boot=(65,51,43)
    hip=(x,g-106*s); shoulder=(x,g-265*s)
    # legs articulated at hip and knee
    for side in (-1,1):
        ph=stride*side
        knee=(x+side*17*s+ph*25*s,g-53*s-abs(ph)*8*s)
        foot=(x+side*18*s+ph*43*s,g-4*s)
        line(d,[(hip[0]+side*12*s,hip[1]),knee,foot],hair,22*s)
        line(d,[(hip[0]+side*12*s,hip[1]),knee,foot],pants,15*s)
        ellipse(d,(knee[0]-8*s,knee[1]-8*s,knee[0]+8*s,knee[1]+8*s),jacketlight,None,0)
        poly(d,[(foot[0]-12*s,foot[1]-10*s),(foot[0]+18*s,foot[1]-10*s),(foot[0]+25*s,foot[1]),(foot[0]-15*s,foot[1])],boot,hair,int(2*s))
    # torso tailored jacket with lapels, seam and buttons
    poly(d,[(x-39*s,g-278*s),(x+39*s,g-278*s),(x+54*s,g-128*s),(x+34*s,g-104*s),(x-35*s,g-104*s),(x-54*s,g-128*s)],jacket,hair,int(4*s))
    poly(d,[(x-26*s,g-274*s),(x,g-224*s),(x+25*s,g-274*s),(x+9*s,g-285*s)],(231,218,190),None,0)
    line(d,[(x,g-224*s),(x,g-119*s)],jacketlight,3*s)
    for k in range(3): ellipse(d,(x+7*s,g-(205-k*28)*s,x+13*s,g-(199-k*28)*s),(235,194,117),None,0)
    # arms, elbows and forearms, counter swing or greeting gesture
    for side in (-1,1):
        sx=x+side*43*s; sy=g-259*s
        if action=="wave" and side==1:
            elbow=(sx+side*20*s,sy-42*s); hand=(sx+side*25*s,sy-111*s)
        else:
            swing=stride*30*s*side if walk else 0
            elbow=(sx+side*13*s+swing*.5,sy+65*s)
            hand=(sx+side*20*s+swing,sy+131*s)
        line(d,[(sx,sy),elbow,hand],hair,19*s)
        line(d,[(sx,sy),elbow,hand],jacketlight if side==-1 else jacket,13*s)
        ellipse(d,(hand[0]-9*s,hand[1]-9*s,hand[0]+9*s,hand[1]+9*s),skinlight,None,0)
        if action=="wave" and side==1:
            for k in range(4):
                a=(hand[0]+(k-1.5)*4*s,hand[1]-10*s)
                line(d,[a,(a[0]+(k-1.5)*3*s,a[1]-19*s)],skinlight,3*s)
    # neck and head with hair silhouette, nose, eyes and expression
    ellipse(d,(x-15*s,g-309*s,x+15*s,g-269*s),skin,None,0)
    ellipse(d,(x-38*s,g-390*s,x+38*s,g-300*s),skinlight,hair,int(3*s))
    ellipse(d,(x-41*s,g-398*s,x+40*s,g-344*s),hair,None,0)
    # side hair locks
    poly(d,[(x-38*s,g-376*s),(x-47*s,g-345*s),(x-32*s,g-333*s),(x-26*s,g-370*s)],hair,None,0)
    poly(d,[(x+35*s,g-376*s),(x+44*s,g-348*s),(x+31*s,g-338*s),(x+25*s,g-370*s)],hair,None,0)
    ellipse(d,(x-19*s,g-360*s,x-11*s,g-349*s),(255,250,231),None,0)
    ellipse(d,(x+11*s,g-360*s,x+19*s,g-349*s),(255,250,231),None,0)
    ellipse(d,(x-15*s,g-358*s,x-10*s,g-350*s),hair,None,0)
    ellipse(d,(x+14*s,g-358*s,x+19*s,g-350*s),hair,None,0)
    line(d,[(x-7*s,g-337*s),(x+2*s,g-334*s),(x+8*s,g-337*s)],(126,69,59),2*s)

def shot_for(t):
    if t < 4.0: return "wide"
    if t < 8.0: return "bird_flight"
    return "group_finish"

def render_frame(t):
    shot=shot_for(t); im=background(t,shot)
    # shared stage and distinct camera compositions; characters are redrawn each frame
    if shot=="wide":
        draw_dog(im,285,585,t,0.78,"walk")
        draw_bird(im,680,245+math.sin(t*4)*12,t,0.82,"fly")
        draw_human(im,1010,590,t,0.78,"wave" if t>2.4 else "walk")
        title="THREE ANATOMIES • ONE SCENE"
    elif shot=="bird_flight":
        # camera tracks the bird; the others remain present as contextual actors
        draw_dog(im,175,585,t,0.60,"walk")
        bx=360+(t-4)*120
        draw_bird(im,bx,250+math.sin(t*4)*32,t,1.18,"fly")
        draw_human(im,1080,590,t,0.62,"walk")
        title="AVIAN FLIGHT • WING-DRIVEN MOTION"
    else:
        draw_dog(im,310,585,t,0.78,"walk")
        draw_bird(im,665,270+math.sin(t*4)*10,t,0.82,"fly")
        draw_human(im,1010,590,t,0.78,"wave")
        title="QUADRUPED • AVIAN • BIPED"
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((42,34,650,84),radius=18,fill=(27,49,51))
    label(d,(346,59),title,19,(248,244,226))
    # restrained shot marker
    d.rounded_rectangle((1110,38,1235,78),radius=14,fill=(248,244,226))
    label(d,(1172,58),f"{int(t*FPS):03d} / {int(DURATION*FPS)}",14,(38,57,54))
    return im

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="build/multi-character")
    ap.add_argument("--fps",type=int,default=FPS)
    ap.add_argument("--duration",type=float,default=DURATION)
    args=ap.parse_args()
    global FPS,DURATION
    FPS=args.fps; DURATION=args.duration
    out=Path(args.out); frames=out/"frames"; frames.mkdir(parents=True,exist_ok=True)
    count=round(FPS*DURATION)
    for i in range(count):
        render_frame(i/FPS).save(frames/f"frame_{i:05d}.png",optimize=True)
    (out/"benchmark.json").write_text(json.dumps({
      "status":"rendered","duration_seconds":DURATION,"fps":FPS,"frame_count":count,
      "resolution":[W,H],
      "characters":[
        {"id":"dog_01","species":"dog","anatomy":"quadruped","motion":["alternating_four_leg_gait","tail_wag","head_bob","ear_bounce"]},
        {"id":"bird_01","species":"bird","anatomy":"avian","motion":["shoulder_pivoted_wing_flap","feather_fan","tail_balance","leg_tuck"]},
        {"id":"human_01","species":"human","anatomy":"biped","motion":["alternating_biped_gait","arm_swing","wave_gesture","head_expression"]}
      ],
      "shots":[{"start":0,"end":4,"type":"wide_group"},{"start":4,"end":8,"type":"bird_tracking_emphasis"},{"start":8,"end":DURATION,"type":"wide_group_reprise"}],
      "quality_note":"Deterministic anatomy-specific 2D motion benchmark; not yet a generative AI character pipeline."
    },indent=2),encoding="utf-8")
    mp4=out/"dog_bird_human_benchmark.mp4"
    subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(frames/"frame_%05d.png"),
      "-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",
      "-movflags","+faststart",str(mp4)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    print(json.dumps({"video":str(mp4),"frames":count,"fps":FPS,"duration":DURATION,"report":str(out/"benchmark.json")},indent=2))

if __name__=="__main__": main()
