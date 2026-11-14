#!/usr/bin/env python3
"""Procedural illustrated stickman documentary video engine."""
import argparse, asyncio, json, math, os, subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
WHITE = (247, 247, 242)
INK = (25, 32, 43)
MUTED = (120, 132, 148)

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def line(d, pts, fill=INK, width=9):
    d.line(pts, fill=fill, width=width, joint="curve")

def rounded(d, xy, radius, fill, outline=None, width=2):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def wrap_words(text, max_chars=38):
    return textwrap.wrap(text, width=max_chars) or [""]

def draw_character(im, name, action, accent, t, x, y, scale=1.0):
    d = ImageDraw.Draw(im)
    sw = max(5, int(8 * scale))
    bob = math.sin(t * 5) * 5 * scale
    x, y = int(x), int(y + bob)
    head_r = int(35 * scale)
    head_y = y - int(135 * scale)
    # expressive face and head
    d.ellipse((x-head_r, head_y-head_r, x+head_r, head_y+head_r), fill=(255,255,255), outline=INK, width=sw)
    d.ellipse((x-int(12*scale), head_y-int(5*scale), x-int(6*scale), head_y+int(1*scale)), fill=INK)
    d.ellipse((x+int(7*scale), head_y-int(5*scale), x+int(13*scale), head_y+int(1*scale)), fill=INK)
    if action in ("celebrate", "wave"):
        d.arc((x-int(13*scale), head_y, x+int(14*scale), head_y+int(20*scale)), 5, 175, fill=INK, width=max(2,sw//2))
    else:
        d.arc((x-int(12*scale), head_y+int(5*scale), x+int(12*scale), head_y+int(20*scale)), 190, 350, fill=INK, width=max(2,sw//2))
    neck = (x, head_y + head_r)
    hip = (x + int(math.sin(t*2)*5*scale), y)
    shoulder = (x, y-int(70*scale))
    line(d, [neck, shoulder, hip], INK, sw)
    # arms animate by named action
    if action == "wave":
        arms = [(shoulder, (x-int(48*scale), y-int(30*scale))), (shoulder, (x+int(65*scale), y-int(120*scale)+int(math.sin(t*7)*12*scale)))]
    elif action == "think":
        arms = [(shoulder, (x-int(48*scale), y-int(25*scale))), (shoulder, (x+int(40*scale), head_y+int(12*scale)))]
    elif action == "type":
        arms = [(shoulder, (x-int(48*scale), y-int(15*scale))), (shoulder, (x+int(50*scale), y-int(15*scale)))]
    elif action == "celebrate":
        arms = [(shoulder, (x-int(62*scale), y-int(125*scale))), (shoulder, (x+int(62*scale), y-int(125*scale)))]
    elif action == "point":
        arms = [(shoulder, (x-int(48*scale), y-int(20*scale))), (shoulder, (x+int(105*scale), y-int(100*scale)))]
    elif action == "run":
        swing = math.sin(t*9)*42*scale
        arms = [(shoulder, (x-int(55*scale), y-int(60*scale)+int(swing))), (shoulder, (x+int(55*scale), y-int(60*scale)-int(swing)))]
    else:
        arms = [(shoulder, (x-int(55*scale), y-int(20*scale))), (shoulder, (x+int(55*scale), y-int(20*scale)))]
    for a,b in arms: line(d, [a,b], INK, sw)
    if action == "run":
        swing = math.sin(t*9)*38*scale
        legs = [(hip, (x-int(45*scale)+int(swing), y+int(75*scale))), (hip, (x+int(45*scale)-int(swing), y+int(75*scale)))]
    else:
        legs = [(hip, (x-int(42*scale), y+int(85*scale))), (hip, (x+int(42*scale), y+int(85*scale)))]
    for a,b in legs:
        line(d, [a,b], INK, sw)
        line(d, [b, (b[0]+int(20*scale), b[1])], INK, sw)
    # simple colored shirt/body accent makes character readable
    d.ellipse((x-int(10*scale), y-int(65*scale), x+int(10*scale), y-int(45*scale)), fill=accent)

def background(im, kind, accent, t):
    d=ImageDraw.Draw(im); w,h=im.size
    d.rectangle((0,0,w,h), fill=WHITE)
    d.rectangle((0,0,w,14), fill=accent)
    if kind == "desk":
        rounded(d,(w*.59,h*.28,w*.91,h*.73),24,(230,236,241))
        rounded(d,(w*.64,h*.34,w*.86,h*.61),12,(35,48,66))
        d.rectangle((w*.73,h*.61,w*.77,h*.68),fill=(90,105,120))
        d.rectangle((w*.68,h*.68,w*.82,h*.71),fill=(90,105,120))
        rounded(d,(w*.08,h*.73,w*.92,h*.77),10,(205,211,217))
    elif kind == "server":
        for i in range(3):
            yy=h*.22+i*h*.18
            rounded(d,(w*.64,yy,w*.9,yy+h*.13),14,(45,59,78))
            for j in range(4):
                d.ellipse((w*.68+j*22,yy+18,w*.68+j*22+9,yy+27),fill=accent)
    else:
        for i in range(7):
            xx=80+i*175
            d.ellipse((xx-8,130,xx+8,146),fill=accent)
            if i<6: line(d,[(xx+8,138),(xx+167,138)],(205,213,221),3)
        for i in range(5):
            yy=260+i*75
            d.arc((80,yy,1180,yy+110),180,350,fill=(225,229,234),width=3)

def diagram(d, kind, accent, t, w, h):
    if kind == "dns":
        boxes=[("Browser",.52),("DNS",.70),("IP address",.88)]
        for label,x in boxes:
            cx=int(w*x); cy=int(h*.30)
            rounded(d,(cx-75,cy-35,cx+75,cy+35),14,(255,255,255),accent,3)
            d.text((cx,cy),label,font=font(20,True),fill=INK,anchor="mm")
        for x in (.61,.79):
            xx=int(w*x); line(d,[(xx-10,int(h*.30)),(xx+10,int(h*.30))],accent,5)
            d.polygon([(xx+10,int(h*.30)),(xx-4,int(h*.30)-8),(xx-4,int(h*.30)+8)],fill=accent)
    elif kind == "route":
        points=[(int(w*.55),int(h*.26)),(int(w*.70),int(h*.18)),(int(w*.82),int(h*.30)),(int(w*.92),int(h*.20))]
        line(d,points,(160,175,190),5)
        for i,(x,y) in enumerate(points):
            r=18
            d.ellipse((x-r,y-r,x+r,y+r),fill=accent if i==int((t*2)%4) else (255,255,255),outline=INK,width=3)

def make_frame(scene, index, total, size):
    w,h=size; im=Image.new("RGB",size,WHITE)
    accent=scene.get("accent","#42B7A5")
    accent_rgb=tuple(int(accent.lstrip("#")[i:i+2],16) for i in (0,2,4))
    t=index/max(1,total-1)*scene["duration"]
    background(im,scene.get("background","network"),accent_rgb,t)
    d=ImageDraw.Draw(im)
    if scene.get("diagram"): diagram(d,scene["diagram"],accent_rgb,t,w,h)
    # Character glides into frame, then settles
    progress=index/max(1,total-1)
    cx=int(w*(.22+.08*min(1,progress*2)))
    cy=int(h*.79)
    draw_character(im,scene.get("character","Guide"),scene.get("action","talk"),accent_rgb,t,cx,cy,1.05)
    # Name tag
    rounded(d,(cx-76,cy+95,cx+76,cy+132),12,(255,255,255),accent_rgb,2)
    d.text((cx,cy+113),scene.get("character","Guide"),font=font(17,True),fill=INK,anchor="mm")
    # Caption panel
    rounded(d,(int(w*.36),int(h*.73),int(w*.94),int(h*.91)),22,(255,255,255),(222,226,231),2)
    caption=scene.get("caption","")
    lines=wrap_words(caption,42)
    for j,s in enumerate(lines[:2]):
        d.text((int(w*.65),int(h*.79)+j*38),s,font=font(27,True),fill=INK,anchor="mm")
    # Small scene progress indicator
    d.rounded_rectangle((int(w*.36),int(h*.925),int(w*.94),int(h*.938)),radius=6,fill=(225,229,234))
    d.rounded_rectangle((int(w*.36),int(h*.925),int(w*(.36+.58*progress)),int(h*.938)),radius=6,fill=accent_rgb)
    return im

async def synthesize(scene, voice, path):
    await edge_tts.Communicate(scene["narration"], voice).save(str(path))

def run(story_path, output):
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    fps=int(story.get("fps",24)); size=(int(story.get("width",1280)),int(story.get("height",720)))
    OUT.mkdir(exist_ok=True); audio_dir=OUT/"audio"; audio_dir.mkdir(exist_ok=True)
    voice=story.get("voice","en-US-GuyNeural")
    for i,scene in enumerate(story["scenes"]):
        asyncio.run(synthesize(scene,voice,audio_dir/f"scene_{i:03}.mp3"))
    # Create silent video frames, then mux narration segments in sequence.
    raw=OUT/"silent.mp4"
    cmd=["ffmpeg","-y","-f","rawvideo","-vcodec","rawvideo","-pix_fmt","rgb24","-s",f"{size[0]}x{size[1]}","-r",str(fps),"-i","-","-an","-c:v","libx264","-pix_fmt","yuv420p",str(raw)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for scene in story["scenes"]:
            count=max(1,int(float(scene.get("duration",4))*fps))
            for frame in range(count):
                proc.stdin.write(make_frame(scene,frame,count,size).tobytes())
    finally:
        proc.stdin.close()
    if proc.wait()!=0: raise RuntimeError("Video frame encoding failed")
    concat=OUT/"audio.txt"
    concat.write_text("".join(f"file '{(audio_dir/f'scene_{i:03}.mp3').resolve()}'\n" for i in range(len(story["scenes"]))))
    voice_file=OUT/"voiceover.mp3"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c:a","libmp3lame",str(voice_file)],check=True)
    # Pad the picture track if speech runs longer; shortest=video keeps narration intact.
    subprocess.run(["ffmpeg","-y","-i",str(raw),"-i",str(voice_file),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",str(output)],check=True)
    print(f"Created: {output}")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Illustrated stickman video maker")
    parser.add_argument("--script",default="demo/story.json")
    parser.add_argument("--output",default="output/stickman-documentary.mp4")
    args=parser.parse_args()
    run(args.script,args.output)
