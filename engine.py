#!/usr/bin/env python3
"""Long-form illustrated educational video renderer.

Each scene's visual duration is derived from its generated narration audio, so
the animation never advances on an unrelated fixed timer.
"""
import argparse
import asyncio
import json
import math
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
BG = (247, 248, 244)
INK = (27, 38, 53)
MUTED = (103, 117, 132)
PALETTE = [(42, 163, 145), (244, 180, 62), (80, 135, 211), (226, 112, 92)]


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rounded(draw, xy, radius=18, fill=(255, 255, 255), outline=None, width=2):
    draw.rounded_rectangle(tuple(int(v) for v in xy), radius=radius, fill=fill, outline=outline, width=width)


def stroke(draw, points, fill=INK, width=7):
    draw.line(points, fill=fill, width=width, joint="curve")


def accent_rgb(value):
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid accent color: {value}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def wrap(text, width=34):
    return textwrap.wrap(str(text), width=width) or [""]


def arrow(draw, start, end, color, width=6):
    stroke(draw, [start, end], color, width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 17
    p1 = (end[0] - size * math.cos(angle - .55), end[1] - size * math.sin(angle - .55))
    p2 = (end[0] - size * math.cos(angle + .55), end[1] - size * math.sin(angle + .55))
    draw.polygon([end, p1, p2], fill=color)


def draw_character(draw, action, x, y, t, scale=1.0, color=INK):
    s = scale
    bob = math.sin(t * 4.5) * 4 * s
    x, y = int(x), int(y + bob)
    sw = max(4, int(8 * s))
    r = int(31 * s)
    hy = y - int(132 * s)
    draw.ellipse((x-r, hy-r, x+r, hy+r), fill=(255,255,255), outline=color, width=sw)
    draw.ellipse((x-int(10*s), hy-int(4*s), x-int(5*s), hy+int(2*s)), fill=color)
    draw.ellipse((x+int(6*s), hy-int(4*s), x+int(11*s), hy+int(2*s)), fill=color)
    draw.arc((x-int(12*s),hy+int(3*s),x+int(12*s),hy+int(19*s)), 5, 175, fill=color, width=max(2,sw//2))
    shoulder=(x,y-int(70*s)); hip=(x+int(math.sin(t*1.7)*4*s),y)
    stroke(draw, [(x,hy+r),shoulder,hip], color, sw)
    # Natural breathing and blink keep long explanatory shots alive.
    blink = (t % 4.7) < 0.13
    if blink:
        draw.line((x-int(13*s),hy,x-int(3*s),hy),fill=color,width=max(2,sw//2))
        draw.line((x+int(3*s),hy,x+int(13*s),hy),fill=color,width=max(2,sw//2))
    if action == "think":
        arms=[(shoulder,(x-int(48*s),y-int(20*s))),(shoulder,(x+int(32*s),hy+int(14*s)))]
    elif action == "point":
        arms=[(shoulder,(x-int(45*s),y-int(18*s))),(shoulder,(x+int(105*s),y-int(100*s)))]
    elif action == "celebrate":
        arms=[(shoulder,(x-int(62*s),y-int(120*s))),(shoulder,(x+int(62*s),y-int(120*s)))]
    elif action == "walk":
        swing=math.sin(t*5)*28*s
        arms=[(shoulder,(x-int(52*s),y-int(38*s)+int(swing))),(shoulder,(x+int(52*s),y-int(38*s)-int(swing)))]
    elif action == "type":
        arms=[(shoulder,(x-int(48*s),y-int(12*s))),(shoulder,(x+int(48*s),y-int(12*s)))]
    else:
        wave=math.sin(t*6)*12*s
        arms=[(shoulder,(x-int(48*s),y-int(18*s))),(shoulder,(x+int(60*s),y-int(104*s)+int(wave)))]
    for a,b in arms: stroke(draw,[a,b],color,sw)
    if action == "walk":
        swing=math.sin(t*5)*35*s
        legs=[(hip,(x-int(42*s)+int(swing),y+int(76*s))),(hip,(x+int(42*s)-int(swing),y+int(76*s)))]
    else:
        legs=[(hip,(x-int(38*s),y+int(80*s))),(hip,(x+int(38*s),y+int(80*s)))]
    for a,b in legs:
        stroke(draw,[a,b],color,sw)
        stroke(draw,[b,(b[0]+int(18*s),b[1])],color,sw)


def draw_flow(draw, items, x0, y, width, color, t):
    items = items[:5]
    if not items: return
    gap = 18
    boxw = min(190, (width - gap*(len(items)-1)) // len(items))
    total = boxw*len(items)+gap*(len(items)-1)
    x = x0 + (width-total)//2
    for i, label in enumerate(items):
        cx=x+boxw//2
        active = (int(t * 0.85) % len(items)) == i
        rounded(draw,(x,y-43,x+boxw,y+43),16,(235,247,244) if active else (255,255,255),color if active else (205,215,218),4 if active else 2)
        lines=wrap(label,15)[:2]
        for j,txt in enumerate(lines):
            draw.text((cx,y+(j-(len(lines)-1)/2)*25),txt,font=font(18,True),fill=INK,anchor="mm")
        if i < len(items)-1:
            arrow(draw,(x+boxw+3,y),(x+boxw+gap-3,y),color,4)
        if active:
            draw.ellipse((cx-7,y+54,cx+7,y+68),fill=color)
        x += boxw+gap


def draw_timeline(draw, items, x0, y, width, color, t):
    items=items[:5]
    if not items: return
    left=x0+35; right=x0+width-35
    if len(items)>1: arrow(draw,(left,y),(right,y),color,5)
    for i,label in enumerate(items):
        x=left if len(items)==1 else left+(right-left)*i/(len(items)-1)
        draw.ellipse((x-12,y-12,x+12,y+12),fill=color,outline=INK,width=2)
        lines=wrap(label,15)[:2]
        yy=y+35 if i%2==0 else y-58
        for j,txt in enumerate(lines):
            draw.text((x,yy+j*22),txt,font=font(16,True),fill=INK,anchor="mm")


def draw_visual(draw, scene, t, w, h, color):
    kind=scene.get("visual","concept")
    area=(int(w*.36),int(h*.18),int(w*.94),int(h*.65))
    x0,y0,x1,y1=area
    rounded(draw,area,24,(255,255,255),(226,231,234),2)
    if kind in ("flow","process"):
        draw_flow(draw,scene.get("items",[]),x0+12,(y0+y1)//2,x1-x0-24,color,t)
    elif kind=="timeline":
        draw_timeline(draw,scene.get("items",[]),x0+8,(y0+y1)//2,x1-x0-16,color,t)
    elif kind=="compare":
        cols=scene.get("items",["Before","After"])[:2]
        for i,label in enumerate(cols):
            xx=x0+int((i+.5)*(x1-x0)/2)
            rounded(draw,(xx-125,y0+55,xx+125,y1-35),18,(247,249,250),color,3)
            draw.text((xx,(y0+y1)//2),label,font=font(23,True),fill=INK,anchor="mm")
    elif kind=="cycle":
        labels=scene.get("items",["Notice","Connect","Practice","Recall"])[:4]
        cx=(x0+x1)//2; cy=(y0+y1)//2
        positions=[]
        for i,label in enumerate(labels):
            a=-math.pi/2+i*2*math.pi/len(labels)
            positions.append((int(cx+145*math.cos(a)),int(cy+105*math.sin(a))))
        for i,p in enumerate(positions):
            q=positions[(i+1)%len(positions)]
            arrow(draw,p,q,color,4)
        for p,label in zip(positions,labels):
            rounded(draw,(p[0]-75,p[1]-27,p[0]+75,p[1]+27),14,(255,255,255),color,3)
            draw.text(p,label,font=font(17,True),fill=INK,anchor="mm")
    elif kind=="stat":
        vals=scene.get("values",[35,65,90,55])[:5]
        labels=scene.get("items",["A","B","C","D"])[:len(vals)]
        base=y1-65; maxv=max(vals) or 1
        bw=min(68,(x1-x0-70)//max(1,len(vals)))
        reveal=min(1.0,max(0.0,t/2.5))
        for i,v in enumerate(vals):
            xx=x0+48+i*(bw+22)
            stagger=max(0.0,min(1.0,(t-i*0.32)/1.1))
            bh=int((y1-y0-145)*v/maxv*min(reveal,stagger))
            rounded(draw,(xx,base-bh,xx+bw,base),10,color)
            draw.text((xx+bw//2,base+22),labels[i] if i<len(labels) else str(i+1),font=font(15,True),fill=INK,anchor="mm")
    elif kind=="network":
        nodes=scene.get("items",["Input","Signal","Response","Feedback"])[:5]
        draw_flow(draw,nodes,x0+8,(y0+y1)//2,x1-x0-16,color,t)
    else:
        title=scene.get("visual_title",scene.get("caption","A useful idea"))
        draw.text(((x0+x1)//2,(y0+y1)//2),title,font=font(28,True),fill=INK,anchor="mm")


def make_frame(scene, frame, frames, size, scene_number, scene_count, title):
    w,h=size
    im=Image.new("RGB",size,BG)
    d=ImageDraw.Draw(im)
    color=accent_rgb(scene.get("accent","#2AA391"))
    d.rectangle((0,0,w,13),fill=color)
    # subtle editorial grid
    for xx in range(40,w,80):
        d.ellipse((xx,h-28,xx+3,h-25),fill=(222,227,225))
    d.text((int(w*.055),int(h*.085)),title[:58],font=font(21,True),fill=MUTED)
    d.text((int(w*.94),int(h*.085)),f"{scene_number:02d} / {scene_count:02d}",font=font(18,True),fill=MUTED,anchor="ra")
    headline=scene.get("heading",scene.get("caption",""))
    for i,txt in enumerate(wrap(headline,26)[:2]):
        d.text((int(w*.055),int(h*.25)+i*52),txt,font=font(36,True),fill=INK)
    t=frame/max(1,frames-1)*float(scene.get("duration",5))
    draw_visual(d,scene,t,w,h,color)
    action=scene.get("action","explain")
    # Educational presenter changes gesture periodically rather than holding
    # one frozen pose for the entire narration paragraph.
    if action == "explain":
        action = ("explain","point","think","explain")[int(t/3.8)%4]
    draw_character(d,action,int(w*.19),int(h*.80),t,1.0)
    # takeaway strip
    rounded(d,(int(w*.055),int(h*.76),int(w*.94),int(h*.94)),20,(255,255,255),(226,231,234),2)
    takeaway=scene.get("takeaway",scene.get("caption",""))
    for i,txt in enumerate(wrap(takeaway,76)[:2]):
        d.text((int(w*.50),int(h*.815)+i*34),txt,font=font(22,True),fill=INK,anchor="mm")
    # continuous chapter progress
    prog=((scene_number-1)+frame/max(1,frames))/max(1,scene_count)
    d.rounded_rectangle((int(w*.055),int(h*.965),int(w*.94),int(h*.978)),radius=6,fill=(222,227,225))
    d.rounded_rectangle((int(w*.055),int(h*.965),int(w*(.055+.885*prog)),int(h*.978)),radius=6,fill=color)
    return im


async def synthesize(text, voice, path, rate):
    await edge_tts.Communicate(text, voice, rate=rate).save(str(path))


def probe_duration(path):
    result=subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],
        check=True,capture_output=True,text=True
    )
    return float(result.stdout.strip())


def validate_story(story):
    if not isinstance(story.get("scenes"),list) or not story["scenes"]:
        raise ValueError("Story must contain a non-empty scenes array")
    for i,scene in enumerate(story["scenes"],1):
        if not scene.get("narration","").strip():
            raise ValueError(f"Scene {i} has no narration")
        if not scene.get("caption") and not scene.get("heading"):
            raise ValueError(f"Scene {i} needs a caption or heading")
        if float(scene.get("duration",0)) < 0:
            raise ValueError(f"Scene {i} has a negative duration")


def run(story_path, output):
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    validate_story(story)
    fps=int(story.get("fps",24))
    size=(int(story.get("width",1280)),int(story.get("height",720)))
    voice=story.get("voice","en-US-GuyNeural")
    rate=story.get("rate","+0%")
    OUT.mkdir(exist_ok=True)
    audio_dir=OUT/"audio"
    audio_dir.mkdir(exist_ok=True)
    audio_files=[]
    durations=[]
    print(f"Preparing narration for {len(story['scenes'])} scenes...")
    for i,scene in enumerate(story["scenes"]):
        path=audio_dir/f"scene_{i:03}.mp3"
        asyncio.run(synthesize(scene["narration"],voice,path,rate))
        audio_files.append(path)
        durations.append(probe_duration(path))
    total_audio=sum(durations)
    print(f"Narration duration: {total_audio/60:.2f} minutes")
    raw=OUT/"silent.mp4"
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s",f"{size[0]}x{size[1]}","-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(raw)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i,(scene,duration) in enumerate(zip(story["scenes"],durations),1):
            # Hold the scene for the full generated speech plus a short reading beat.
            scene_duration=max(float(scene.get("duration",0)),duration+float(story.get("reading_beat",0.35)))
            count=max(1,math.ceil(scene_duration*fps))
            for frame in range(count):
                proc.stdin.write(make_frame(scene,frame,count,size,i,len(story["scenes"]),story.get("title","Learning, illustrated")).tobytes())
            print(f"Rendered scene {i}/{len(story['scenes'])}: {scene_duration:.1f}s")
    finally:
        proc.stdin.close()
    if proc.wait()!=0:
        raise RuntimeError("Video frame encoding failed")
    concat=OUT/"audio.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in audio_files),encoding="utf-8")
    voice_file=OUT/"voiceover.mp3"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c:a","libmp3lame",str(voice_file)],check=True)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(voice_file),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(output)],check=True)
    video_duration=probe_duration(output)
    if video_duration+1 < total_audio:
        raise RuntimeError(f"Output ({video_duration:.1f}s) is shorter than narration ({total_audio:.1f}s)")
    report={"title":story.get("title",""),"scenes":len(story["scenes"]),"narration_seconds":round(total_audio,2),"video_seconds":round(video_duration,2),"fps":fps,"resolution":f"{size[0]}x{size[1]}","output":str(output)}
    (output.parent/"render_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Long-form illustrated educational video renderer")
    parser.add_argument("--script",default="demo/learning.json")
    parser.add_argument("--output",default="output/educational-5min.mp4")
    args=parser.parse_args()
    run(args.script,args.output)
