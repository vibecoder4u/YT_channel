#!/usr/bin/env python3
"""Cinematic 2D character-animation prototype: continuous action, not pose cards."""
import argparse, math
from PIL import Image, ImageDraw
import engine

W,H=1280,720
INK=(42,47,49); SKIN=(225,174,137)
CLOTH={"maya":(35,139,151),"arun":(214,157,62),"leena":(104,132,78)}
def clamp(x): return max(0,min(1,x))
def ease(x):
    x=clamp(x); return x*x*(3-2*x)
def mix(a,b,u): return a+(b-a)*u
def pt(a,b,u): return (mix(a[0],b[0],u),mix(a[1],b[1],u))
def curve(a,b,c,d,u):
    v=1-u
    return (v**3*a[0]+3*v*v*u*b[0]+3*v*u*u*c[0]+u**3*d[0],
            v**3*a[1]+3*v*v*u*b[1]+3*v*u*u*c[1]+u**3*d[1])
def stroke(d, points, fill, width):
    d.line([(int(x),int(y)) for x,y in points],fill=fill,width=max(1,int(width)),joint="curve")
def ellipse(d, box, fill, outline=None, width=2):
    d.ellipse(tuple(int(v) for v in box),fill=fill,outline=outline,width=max(1,int(width)) if outline else 1)
def background(t, camera):
    im=Image.new("RGB",(W,H),(185,214,211)); d=ImageDraw.Draw(im)
    # layered forest ridges with slow parallax
    for layer,(base,col,amp) in enumerate([(300,(119,153,125),55),(390,(83,126,98),42),(470,(61,105,82),30)]):
        pts=[(0,base)]
        for x in range(0,1301,65):
            y=base+math.sin(x*.009+layer*1.7+camera*.001)*amp+math.sin(x*.021+layer)*12
            pts.append((x,y))
        pts += [(1280,520),(0,520)]
        d.polygon(pts,fill=col)
    # sandy riverbank
    d.polygon([(0,485),(370,465),(510,510),(1280,478),(1280,720),(0,720)],fill=(164,143,108))
    # river with curved banks and moving highlights
    d.polygon([(450,470),(600,445),(730,465),(870,440),(1010,466),(1280,440),(1280,720),(360,720)],fill=(55,139,158))
    for i in range(28):
        x=(i*71+int(t*46))%980+300
        y=505+(i%7)*27+math.sin(t*1.8+i)*5
        length=22+(i%4)*17
        stroke(d,[(x,y),(x+length,y-2),(x+length+10,y)],(135,204,205),2+(i%2))
    # rocks and stepping stones
    for x,y,r in [(570,483,34),(690,470,39),(820,479,33),(950,465,42),(1080,475,31),(395,512,40)]:
        ellipse(d,(x-r,y-r*.42,x+r,y+r*.42),(117,119,101),(82,91,81),3)
        stroke(d,[(x-r*.5,y-3),(x,y-r*.25),(x+r*.45,y-1)],(151,151,128),3)
    # foliage silhouettes
    for i in range(18):
        x=(i*97-camera*.12)%1450-60; y=260+(i%4)*28
        ellipse(d,(x-42,y-70,x+42,y+35),(48,93,68),None)
    return im
def pose(kind, action, t, phase):
    """Return normalized articulated joints; pose changes continuously over time."""
    w=math.sin(phase); bob=math.sin(phase*2)*3
    if action=="walk":
        return dict(lean=0, head=(0,-211+bob), shoulder=(0,-169+bob), hip=(0,-77),
          elbows=[(-31,-125+w*8),(34,-125-w*8)], hands=[(-42,-99+w*18),(44,-99-w*18)],
          knees=[(-16+w*17,-39),(16-w*17,-39)], feet=[(-25+w*31,0),(25-w*31,0)])
    if action=="look":
        return dict(lean=0,head=(4,-211),shoulder=(0,-169),hip=(0,-77),
          elbows=[(-36,-137),(38,-143)],hands=[(-49,-112),(55,-118)],
          knees=[(-17,-39),(17,-39)],feet=[(-22,0),(22,0)])
    if action=="point":
        return dict(lean=0,head=(2,-211),shoulder=(0,-169),hip=(0,-77),
          elbows=[(-34,-128),(45,-148)],hands=[(-47,-103),(100,-180)],
          knees=[(-17,-39),(17,-39)],feet=[(-22,0),(22,0)])
    if action=="slip":
        # torso tilts, one leg shoots forward, arms flare; body drops low.
        return dict(lean=math.sin(t*2)*.08,head=(31,-183),shoulder=(20,-143),hip=(-10,-72),
          elbows=[(-45,-176),(73,-187)],hands=[(-82,-213),(116,-225)],
          knees=[(-35,-35),(67,-55)],feet=[(-68,4),(115,-15)])
    if action=="down":
        return dict(lean=0,head=(44,-108),shoulder=(25,-85),hip=(-15,-58),
          elbows=[(-10,-120),(70,-93)],hands=[(-23,-151),(110,-104)],
          knees=[(25,-25),(90,-10)],feet=[(75,0),(135,0)])
    if action=="reach":
        return dict(lean=-.12,head=(9,-211),shoulder=(0,-169),hip=(0,-77),
          elbows=[(-36,-131),(58,-159)],hands=[(-49,-105),(111,-181)],
          knees=[(-17,-39),(17,-39)],feet=[(-22,0),(22,0)])
    if action=="pull":
        return dict(lean=-.18,head=(-5,-207),shoulder=(-7,-165),hip=(0,-77),
          elbows=[(-49,-137),(54,-135)],hands=[(-75,-112),(102,-112)],
          knees=[(-39,-35),(34,-31)],feet=[(-55,0),(52,0)])
    if action=="help":
        return dict(lean=-.1,head=(5,-205),shoulder=(0,-164),hip=(0,-77),
          elbows=[(-38,-130),(54,-152)],hands=[(-50,-102),(86,-176)],
          knees=[(-17,-39),(17,-39)],feet=[(-22,0),(22,0)])
    return pose(kind,"look",t,phase)
def draw_person(im,x,ground,kind,action,t,scale=1.0,phase=0):
    d=ImageDraw.Draw(im); p=pose(kind,action,t,phase); s=scale
    def xy(q): return (x+q[0]*s,ground+q[1]*s)
    hip=xy(p["hip"]); sh=xy(p["shoulder"]); head=xy(p["head"])
    # shadow and articulated legs
    ellipse(d,(x-48*s,ground-3*s,x+48*s,ground+9*s),(93,105,91),None)
    for i in range(2):
        knee=xy(p["knees"][i]); foot=xy(p["feet"][i])
        stroke(d,[hip,knee,foot],(48,51,51),13*s)
        ellipse(d,(knee[0]-6*s,knee[1]-6*s,knee[0]+6*s,knee[1]+6*s),(48,51,51),None)
        stroke(d,[foot,(foot[0]+(15 if i else -12)*s,foot[1]+2*s)],(40,43,43),9*s)
    # jacket torso silhouette with collar, seams and waist
    d.polygon([xy((-22,-177)),xy((-31,-158)),xy((-25,-91)),xy((-19,-77)),xy((20,-77)),xy((28,-94)),xy((30,-158)),xy((20,-177)),xy((0,-185))],fill=CLOTH[kind],outline=INK)
    stroke(d,[xy((-18,-157)),xy((-8,-125)),xy((-17,-83))],tuple(max(0,c-18) for c in CLOTH[kind]),3*s)
    stroke(d,[xy((18,-158)),xy((7,-126)),xy((17,-84))],tuple(min(255,c+22) for c in CLOTH[kind]),2*s)
    # neck and head
    ellipse(d,(x-8*s,ground-194*s,x+9*s,ground-172*s),SKIN,None)
    ellipse(d,(head[0]-24*s,head[1]-29*s,head[0]+24*s,head[1]+27*s),SKIN,INK,2*s)
    # hair silhouette unique per character
    if kind=="maya":
        ellipse(d,(head[0]-27*s,head[1]-34*s,head[0]+25*s,head[1]-7*s),(43,43,47),None)
        d.polygon([(head[0]-25*s,head[1]-23*s),(head[0]-17*s,head[1]+7*s),(head[0]-9*s,head[1]-6*s)],fill=(43,43,47))
    elif kind=="arun":
        ellipse(d,(head[0]-24*s,head[1]-34*s,head[0]+24*s,head[1]-14*s),(63,48,42),None)
        for k in range(5):
            ellipse(d,(head[0]+(-19+k*9)*s,head[1]-37*s,head[0]+(-10+k*9)*s,head[1]-24*s),(63,48,42),None)
    else:
        ellipse(d,(head[0]-24*s,head[1]-34*s,head[0]+24*s,head[1]-10*s),(48,45,43),None)
        ellipse(d,(head[0]+16*s,head[1]-25*s,head[0]+34*s,head[1]+18*s),(48,45,43),None)
    # face looking toward the action
    for ex in (-9,8):
        ellipse(d,(head[0]+(ex-2)*s,head[1]-5*s,head[0]+(ex+2)*s,head[1]-1*s),INK,None)
    stroke(d,[(head[0]-4*s,head[1]+12*s),(head[0]+5*s,head[1]+12*s)],(133,74,64),2*s)
    # articulated arms with shoulder/elbow/wrist joints and visible hands
    for i in range(2):
        a=xy([(-20,-163),(20,-163)][i]); e=xy(p["elbows"][i]); hand=xy(p["hands"][i])
        stroke(d,[a,e,hand],CLOTH[kind],14*s)
        ellipse(d,(e[0]-6*s,e[1]-6*s,e[0]+6*s,e[1]+6*s),SKIN,INK,1*s)
        ellipse(d,(hand[0]-7*s,hand[1]-7*s,hand[0]+7*s,hand[1]+7*s),SKIN,INK,1*s)
        for f in range(3):
            stroke(d,[hand,(hand[0]+(f-1)*4*s,hand[1]+10*s)],SKIN,2*s)
    # pack straps on Arun
    if kind=="arun":
        stroke(d,[xy((-20,-169)),xy((0,-111)),xy((17,-169))],(95,69,48),4*s)
    return {"left_hand":xy(p["hands"][0]),"right_hand":xy(p["hands"][1]),"head":head,"hip":hip}
def draw_rope(d,a,b,t):
    # animated sagging rope curve with traveling wave
    mid=((a[0]+b[0])/2,(a[1]+b[1])/2+26+math.sin(t*4)*7)
    pts=[]
    for i in range(25):
        u=i/24
        pts.append((mix(mix(a[0],mid[0],u),mix(mid[0],b[0],u),u),
                    mix(mix(a[1],mid[1],u),mix(mid[1],b[1],u),u)))
    stroke(d,pts,(120,83,48),7); stroke(d,[(x,y-2) for x,y in pts],(225,184,112),2)
def frame(scene,frame,frames,size,scene_number,scene_count,title):
    w,h=size; dur=float(scene.get("_render_duration",scene.get("duration",8))); t=frame/max(1,frames-1)*dur
    im=background(t,scene_number*40); d=ImageDraw.Draw(im)
    # camera drift and deliberate character blocking
    if scene_number==1:
        progress=ease(t/dur); xs=[mix(170,360,progress),mix(65,535,progress),mix(-45,710,progress)]
        acts=["walk","walk","walk"]; grounds=[604,602,600]
    elif scene_number==2:
        xs=[350,565,790]; acts=["point","look","point"]; grounds=[602,600,600]
    elif scene_number==3:
        u=clamp(t/dur); xs=[355,610,835]
        acts=["reach","slip","reach"] if u<.46 else ["reach","down","reach"]
        grounds=[600, mix(598,657,ease((u-.12)/.42)),600]
    elif scene_number==4:
        u=clamp(t/dur); xs=[360,650,515]
        acts=["pull","down","pull"]
        grounds=[600,mix(655,602,ease(u)),600]
    else:
        u=ease(t/dur); xs=[mix(350,520,u),mix(565,700,u),mix(790,865,u)]
        acts=["walk","walk","walk"]; grounds=[600,600,600]
    chars={}
    # far-to-near drawing order
    for idx in (2,1,0):
        kind=("maya","arun","leena")[idx]
        chars[kind]=draw_person(im,xs[idx],grounds[idx],kind,acts[idx],t,1.0,t*5+idx*2.1)
    d=ImageDraw.Draw(im)
    # Rope visibly links Leena's hand to Arun, then Maya braces the line.
    if scene_number==4:
        draw_rope(d,chars["leena"]["right_hand"],chars["arun"]["left_hand"],t)
        draw_rope(d,chars["maya"]["right_hand"],chars["leena"]["left_hand"],t+.4)
        for k in range(8):
            x=430+k*48; y=540+math.sin(t*5+k)*4
            stroke(d,[(x,y),(x+18,y-2)],(166,220,218),2)
    # dust, leaves and foreground grass add depth and continuous environmental motion
    for k in range(16):
        x=(k*91+int(t*19))%1320; y=180+(k*53)%360+math.sin(t*1.5+k)*9
        ellipse(d,(x,y,x+4,y+4),(213,222,186),None)
    for x in range(0,1280,38):
        stroke(d,[(x,620),(x-5+math.sin(t+x)*4,600+(x%5)*3)],(78,105,70),2)
    # editorial title treatment
    d.rounded_rectangle((38,28,1242,91),radius=16,fill=(249,244,226),outline=(91,103,84),width=2)
    d.text((66,59),scene.get("heading",title),font=engine.font(25,True),fill=(38,47,43),anchor="lm")
    d.rounded_rectangle((45,635,1235,690),radius=14,fill=(248,244,229),outline=(91,103,84),width=2)
    d.text((640,662),scene.get("caption",""),font=engine.font(19,True),fill=(43,52,47),anchor="mm")
    progress=((scene_number-1)+frame/max(1,frames))/scene_count
    d.rounded_rectangle((45,704,1235,711),radius=3,fill=(202,197,175))
    d.rounded_rectangle((45,704,45+int(1190*progress),711),radius=3,fill=(35,132,126))
    return im
engine.make_frame=frame
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--script",default="demo/rescue_at_the_river_55s.json")
    p.add_argument("--output",default="output/rescue-at-the-river-cinematic.mp4")
    a=p.parse_args(); engine.run(a.script,a.output)
