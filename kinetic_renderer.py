"""Kinetic 2D renderer for script-generated stories.

The original renderer is a static infographic layout with small looping effects.
This renderer gives each scene a composed, animated frame: colorful atmospheric
backgrounds, staged infographic entrances, camera drift, animated presenter poses,
and narration-synchronized captions. It deliberately uses only Pillow/CairoSVG and
FFmpeg, keeping generated art local and reproducible.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
import math
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

import engine

W, H = 1280, 720
INK = (24, 36, 54)
WHITE = (255, 255, 255)
PALETTES = [
    ((26, 132, 156), (75, 204, 173), (255, 205, 103)),
    ((77, 83, 171), (130, 113, 227), (255, 157, 127)),
    ((27, 119, 106), (92, 176, 120), (252, 205, 107)),
    ((170, 83, 87), (231, 139, 106), (255, 218, 135)),
]


def _font(size: int, bold: bool = False):
    return engine.font(size, bold)


def _ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(tuple(int(v) for v in box), radius=int(radius), fill=fill, outline=outline, width=width)


def _card(image: Image.Image, box, radius=22, fill=(255, 255, 255, 245), shadow=18):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = [int(v) for v in box]
    d.rounded_rectangle((x0+2, y0+shadow, x1+2, y1+shadow), radius=radius, fill=(15, 29, 49, 48))
    d.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill)
    image.alpha_composite(layer)


@lru_cache(maxsize=16)
def _gradient(seed: int) -> Image.Image:
    top, bottom, _ = PALETTES[seed % len(PALETTES)]
    image = Image.new("RGB", (W, H))
    pixels = image.load()
    for y in range(H):
        p = y / (H - 1)
        p = p * p * (3 - 2 * p)
        c = tuple(round(top[i] * (1 - p) + bottom[i] * p) for i in range(3))
        for x in range(W):
            glow = max(0, 1 - math.sqrt(((x - W*.72)/(W*.9))**2 + ((y-H*.05)/(H*.8))**2))
            pixels[x, y] = tuple(min(255, int(v + 20*glow)) for v in c)
    return image.convert("RGBA")


def _background(seed: int, t: float) -> Image.Image:
    image = _gradient(seed).copy()
    d = ImageDraw.Draw(image, "RGBA")
    # Slow parallax orbs, atmospheric horizon and distant rolling hills.
    for i in range(9):
        x = int((i * 181 + t * (8 + i % 4)) % (W + 180)) - 90
        y = 55 + (i * 73) % 310 + int(math.sin(t*.55 + i)*10)
        r = 15 + i % 4 * 8
        d.ellipse((x-r, y-r, x+r, y+r), fill=(255,255,255,22))
    d.ellipse((875, 55, 1115, 295), fill=(255,255,255,30))
    d.polygon([(0, 475), (170, 405), (345, 470), (535, 380), (770, 477), (1000, 390), (1280, 467), (1280, 720), (0, 720)], fill=(12,39,61,34))
    d.polygon([(0, 555), (210, 495), (390, 548), (620, 468), (850, 555), (1070, 485), (1280, 540), (1280, 720), (0, 720)], fill=(10,34,52,52))
    return image


def _draw_presenter(image: Image.Image, t: float, action: str, accent, x=145, ground=600, scale=1.0):
    """Draw a softly shaded, animated full-body presenter with articulated limbs."""
    d = ImageDraw.Draw(image, "RGBA")
    bob = math.sin(t * 2.4) * 5
    x = int(x + math.sin(t * .55) * 7)
    y = int(ground + bob)
    s = scale
    skin = (255, 221, 190, 255)
    dark = (28, 43, 61, 255)
    # grounding shadow
    d.ellipse((x-76*s, y+1, x+76*s, y+20), fill=(7,24,39,55))
    # legs and shoes, with a proper walk cycle
    phase = t * 5.3
    stride = math.sin(phase) * 23 if action in ("walk", "run") else math.sin(phase)*3
    hip = (x, y-105*s)
    knees = [(x-17*s+stride*.35, y-51*s), (x+17*s-stride*.35, y-51*s)]
    feet = [(x-24*s+stride, y), (x+24*s-stride, y)]
    for knee, foot in zip(knees, feet):
        d.line((hip, knee, foot), fill=dark, width=max(7, int(11*s)), joint="curve")
        d.ellipse((knee[0]-5*s,knee[1]-5*s,knee[0]+5*s,knee[1]+5*s),fill=skin)
        d.line((foot[0]-2*s,foot[1],foot[0]+21*s,foot[1]),fill=dark,width=max(8,int(12*s)))
    # jacket body and neck
    d.rounded_rectangle((x-38*s,y-224*s,x+38*s,y-98*s),radius=int(22*s),fill=(*accent,255),outline=dark,width=max(2,int(3*s)))
    d.rectangle((x-8*s,y-232*s,x+8*s,y-215*s), fill=skin)
    # arms swing or gesture; upper arm/elbow/forearm are separate joints
    if action in ("point", "demonstrate"):
        arms = [((x-34*s,y-205*s),(x-58*s,y-155*s),(x-70*s,y-125*s)), ((x+34*s,y-205*s),(x+77*s,y-242*s),(x+135*s,y-250*s))]
    elif action == "celebrate":
        arms = [((x-32*s,y-205*s),(x-75*s,y-258*s),(x-90*s,y-300*s)), ((x+32*s,y-205*s),(x+75*s,y-258*s),(x+90*s,y-300*s))]
    elif action == "think":
        arms = [((x-34*s,y-205*s),(x-60*s,y-155*s),(x-58*s,y-118*s)), ((x+34*s,y-205*s),(x+62*s,y-242*s),(x+30*s,y-258*s))]
    else:
        swing = math.sin(phase) * 17*s if action in ("walk", "run") else math.sin(t*2.8)*7*s
        arms = [((x-34*s,y-205*s),(x-59*s,y-163*s-swing),(x-45*s,y-122*s-swing)), ((x+34*s,y-205*s),(x+60*s,y-163*s+swing),(x+47*s,y-122*s+swing))]
    for shoulder, elbow, hand in arms:
        d.line((shoulder, elbow, hand), fill=dark, width=max(7,int(11*s)), joint="curve")
        d.ellipse((elbow[0]-6*s,elbow[1]-6*s,elbow[0]+6*s,elbow[1]+6*s),fill=skin,outline=dark,width=2)
        d.ellipse((hand[0]-8*s,hand[1]-8*s,hand[0]+8*s,hand[1]+8*s),fill=skin,outline=dark,width=2)
    # head, hair, eyes, blink, and speaking mouth
    head_y = y - 264*s + bob*.35
    d.ellipse((x-38*s,head_y-42*s,x+38*s,head_y+42*s),fill=skin,outline=dark,width=max(2,int(3*s)))
    d.pieslice((x-40*s,head_y-47*s,x+40*s,head_y+25*s),180,360,fill=(32,39,53,255))
    blink = (t % 4.1) < .13
    for eye_x in (x-14*s,x+14*s):
        if blink:
            d.line((eye_x-4*s,head_y,eye_x+4*s,head_y),fill=dark,width=2)
        else:
            d.ellipse((eye_x-3*s,head_y-2*s,eye_x+3*s,head_y+5*s),fill=dark)
    mouth_open = int(2 + 5 * max(0, math.sin(t*9)))
    d.ellipse((x-6*s,head_y+17*s-mouth_open/2,x+6*s,head_y+19*s+mouth_open/2),fill=(132,57,60,255))


def _draw_icon(draw, center, label, accent, t, scale=1.0):
    x, y = center
    pulse = 1 + .055 * math.sin(t * 3.2)
    r = 39 * pulse * scale
    draw.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,255),outline=(255,255,255,230),width=4)
    # Distinct geometric pictograms, not just text inside generic boxes.
    key = label.lower()
    if any(v in key for v in ("sun", "light", "energy", "star")):
        for i in range(8):
            a = i * math.pi/4 + t*.25
            draw.line((x+math.cos(a)*r*.58,y+math.sin(a)*r*.58,x+math.cos(a)*r*.83,y+math.sin(a)*r*.83),fill=WHITE,width=4)
        draw.ellipse((x-r*.36,y-r*.36,x+r*.36,y+r*.36),fill=WHITE)
    elif any(v in key for v in ("water", "rain", "river", "ocean")):
        draw.arc((x-r*.5,y-r*.25,x+r*.5,y+r*.47),0,180,fill=WHITE,width=7)
        draw.arc((x-r*.5,y-r*.05,x+r*.5,y+r*.67),0,180,fill=WHITE,width=7)
    elif any(v in key for v in ("person", "people", "human", "brain", "you")):
        draw.ellipse((x-10,y-r*.55,x+10,y-r*.15),fill=WHITE)
        draw.arc((x-r*.42,y-r*.05,x+r*.42,y+r*.78),180,360,fill=WHITE,width=8)
    elif any(v in key for v in ("grow", "plant", "forest", "tree", "seed")):
        draw.line((x,y+r*.45,x,y-r*.18),fill=WHITE,width=6)
        draw.ellipse((x-r*.42,y-r*.52,x,y),fill=WHITE)
        draw.ellipse((x,y-r*.48,x+r*.42,y-r*.02),fill=WHITE)
    else:
        draw.rounded_rectangle((x-r*.37,y-r*.28,x+r*.37,y+r*.28),radius=8,outline=WHITE,width=5)
        draw.ellipse((x-5,y-5,x+5,y+5),fill=WHITE)


def _draw_visual(image: Image.Image, scene: dict[str, Any], t: float, accent, progress: float):
    d = ImageDraw.Draw(image, "RGBA")
    kind = scene.get("visual", "concept")
    items = [str(x) for x in scene.get("items", [])[:5]] or [scene.get("visual_title", "The key idea"), "Why it matters"]
    # Large central translucent stage gives typography and diagrams space.
    _card(image, (355, 160, 1190, 526), radius=30, fill=(250,252,255,237), shadow=17)
    d = ImageDraw.Draw(image, "RGBA")
    d.text((395,184),str(scene.get("diagram_title", scene.get("heading", "The big idea")))[:43],font=_font(23,True),fill=(57,75,94,255))
    d.line((395,225,1148,225),fill=(220,230,237,255),width=2)
    n = len(items)
    # Nodes enter sequentially with overshoot/easing, synchronized to narration.
    reveal_time = max(1.2, min(3.2, 8.0 / max(1,n)))
    for i,label in enumerate(items):
        appear = _ease((t - i*0.42) / reveal_time)
        if appear <= 0:
            continue
        y = 352 + int((1-appear)*55) + int(math.sin(t*2+i)*4)
        if kind == "compare" and n >= 2:
            cx = 585 if i == 0 else 965
            box = (cx-145, 258, cx+145, 456)
            _card(image,box,radius=24,fill=(239,246,251,255),shadow=10)
            d = ImageDraw.Draw(image,"RGBA")
            _draw_icon(d,(cx,318),label,accent,t+i,0.65)
            d.text((cx,407),label[:22],font=_font(21,True),fill=INK,anchor="mm")
            if i == 0:
                d.text((775,354),"→",font=_font(48,True),fill=(*accent,255),anchor="mm")
        elif kind == "stat":
            values = scene.get("values", [38,62,82,56,74])
            value = max(1, float(values[i % len(values)]))
            x = 440 + i*137
            base = 456
            bar_h = 145 * value / max(float(v) for v in values) * appear
            _rounded(d,(x,base-bar_h,x+74,base),15,(*accent,230))
            d.ellipse((x+25,base-bar_h-11,x+49,base-bar_h+13),fill=(*accent,255))
            d.text((x+37,480),label[:13],font=_font(15,True),fill=(55,71,87,255),anchor="mm")
        elif kind == "cycle" and n >= 3:
            cx,cy=775,360
            radius=112
            angle=-math.pi/2+i*2*math.pi/n
            px=cx+math.cos(angle)*radius
            py=cy+math.sin(angle)*radius
            d.ellipse((cx-38,cy-38,cx+38,cy+38),fill=(255,255,255,210),outline=(*accent,160),width=3)
            _draw_icon(d,(int(px),int(py)),label,accent,t+i,.67*appear)
            d.text((px,py+55),label[:14],font=_font(14,True),fill=(48,62,79,255),anchor="mm")
            if i < n:
                next_angle=-math.pi/2+(i+1)*2*math.pi/n
                qx=cx+math.cos(next_angle)*radius
                qy=cy+math.sin(next_angle)*radius
                d.line((px,py,qx,qy),fill=(*accent,105),width=4)
        else:
            gap = min(170, 690/max(1,n))
            cx = 775 + (i-(n-1)/2)*gap
            if kind in ("flow","process","network","timeline") and i < n-1:
                x1=cx+48; x2=cx+gap-48
                d.line((x1,352,x2,352),fill=(*accent,160),width=5)
                d.polygon([(x2,352),(x2-13,344),(x2-13,360)],fill=(*accent,220))
            _draw_icon(d,(int(cx),int(y)),label,accent,t+i,appear)
            label_lines=engine.wrap(label,14)[:2]
            for j,line in enumerate(label_lines):
                d.text((cx,420+j*21),line,font=_font(15,True),fill=(45,62,80,255),anchor="mm")
    # Scene-progress streak sweeps across the stage instead of looping randomly.
    d.rounded_rectangle((395,499,1148,506),radius=3,fill=(220,230,237,255))
    d.rounded_rectangle((395,499,395+int(753*max(.04,progress)),506),radius=3,fill=(*accent,255))


def make_kinetic_frame(scene: dict[str, Any], frame: int, frames: int, scene_number: int, scene_count: int, title: str) -> Image.Image:
    duration = max(.01, float(scene.get("_render_duration", 5)))
    t = frame / max(1, frames-1) * duration
    progress = frame / max(1, frames-1)
    seed = int(scene_number) + sum(ord(ch) for ch in str(scene.get("heading", "")))
    image = _background(seed, t)
    accent = PALETTES[seed % len(PALETTES)][2]
    # Camera drift makes the shot feel alive while keeping the reading area stable.
    zoom = 1.015 + .018 * progress
    image = image.resize((int(W*zoom), int(H*zoom)), Image.Resampling.BICUBIC)
    ox, oy = int((image.width-W)*.55), int((image.height-H)*.5)
    image = image.crop((ox,oy,ox+W,oy+H))
    # Header with strong type hierarchy.
    d = ImageDraw.Draw(image,"RGBA")
    d.rounded_rectangle((0,0,W,12),radius=0,fill=(*accent,255))
    d.text((55,42),title[:48],font=_font(18,True),fill=(255,255,255,220))
    d.text((1205,42),f"{scene_number:02d} / {scene_count:02d}",font=_font(18,True),fill=(255,255,255,220),anchor="ra")
    headline = str(scene.get("heading",scene.get("caption","")))
    lines=engine.wrap(headline,21)[:3]
    for i,line in enumerate(lines):
        d.text((63,135+i*53),line,font=_font(34,True),fill=(255,255,255,255),stroke_width=1,stroke_fill=(25,45,63,70))
    kicker = str(scene.get("takeaway", "A closer look"))
    for i,line in enumerate(engine.wrap(kicker,24)[:3]):
        d.text((65,305+i*26),line,font=_font(17),fill=(255,255,255,225))
    _draw_visual(image,scene,t,accent,progress)
    action = scene.get("action", "explain")
    if action == "explain":
        action = ("explain","point","walk","think","demonstrate")[int(t/4.5)%5]
    _draw_presenter(image,t,action,accent)
    # Captions use real TTS timing when available; fallback timings are generated by engine.
    d = ImageDraw.Draw(image,"RGBA")
    d.rounded_rectangle((355,570,1190,664),radius=19,fill=(13,29,47,218),outline=(255,255,255,95),width=1)
    cues=scene.get("_caption_cues",[])
    active=next((cue for cue in cues if cue["start"] <= t < cue["end"]),None)
    if active is None and cues and t >= cues[-1]["end"]:
        active=cues[-1]
    caption = (active or {}).get("text", scene.get("caption", ""))
    for i,line in enumerate(engine.wrap(caption,52)[:2]):
        d.text((772,617+(i-.5)*25),line,font=_font(19,True),fill=WHITE,anchor="mm")
    # Video-wide timeline position.
    overall = ((scene_number-1)+progress)/max(scene_count,1)
    d.rounded_rectangle((57,686,1221,695),radius=5,fill=(255,255,255,105))
    d.rounded_rectangle((57,686,57+int(1164*overall),695),radius=5,fill=(*accent,255))
    return image.convert("RGB")


def render_story(story: dict[str, Any], output: str | Path, work_dir: str | Path | None = None) -> dict[str, Any]:
    """Generate narration and render a synchronized MP4 from a storyboard."""
    engine.validate_story(story)
    fps = int(story.get("fps", 24))
    size = (int(story.get("width", W)), int(story.get("height", H)))
    if size != (W,H):
        raise ValueError(f"Kinetic renderer currently requires {W}x{H} output; received {size[0]}x{size[1]}")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(work_dir) if work_dir else output.parent / (output.stem + "_work")
    audio_dir = work / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    voice = story.get("voice", "en-US-GuyNeural")
    rate = story.get("rate", "+0%")
    beat = max(0.0, float(story.get("reading_beat", .35)))
    audio_paths, durations = [], []
    for i, scene in enumerate(story["scenes"]):
        audio = audio_dir / f"scene_{i:04d}.mp3"
        boundaries = asyncio.run(engine.synthesize(scene["narration"], voice, audio, rate))
        duration = engine.probe_duration(audio)
        durations.append(duration)
        scene["_render_duration"] = duration + beat
        scene["_caption_cues"] = engine.build_caption_cues(boundaries, scene["narration"], duration)
        padded = audio_dir / f"padded_{i:04d}.mp3"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(audio),"-af",f"apad=pad_dur={beat}","-c:a","libmp3lame",str(padded)],check=True)
        audio_paths.append(padded)

    raw = work / "silent.mp4"
    command=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(fps),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(raw)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i,(scene,duration) in enumerate(zip(story["scenes"],durations),1):
            seconds=duration+beat
            count=max(1,math.ceil(seconds*fps))
            for frame in range(count):
                process.stdin.write(make_kinetic_frame(scene,frame,count,i,len(story["scenes"]),story.get("title","A Story, Illustrated")).tobytes())
    finally:
        process.stdin.close()
    if process.wait()!=0:
        raise RuntimeError("FFmpeg failed while encoding the animation frames")

    concat=work/"audio.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\n" for p in audio_paths),encoding="utf-8")
    voice_file=work/"voiceover.mp3"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c:a","libmp3lame",str(voice_file)],check=True)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-i",str(voice_file),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(output)],check=True)
    report={"title":story.get("title",""),"scenes":len(story["scenes"]),"narration_seconds":round(sum(durations),2),"video_seconds":round(engine.probe_duration(output),2),"fps":fps,"resolution":f"{W}x{H}","renderer":"kinetic-2d"}
    (output.parent/"render_report.json").write_text(__import__("json").dumps(report,indent=2),encoding="utf-8")
    return report
