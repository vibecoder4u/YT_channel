#!/usr/bin/env python3
"""Composite transparent Rigby2D renders into a small cinematic character test stage."""
from pathlib import Path
import json
import subprocess
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1280, 720, 30
LABELS = [
    "FRONT INTRO", "BREATH / EXPRESSION", "THREE-QUARTER TURN",
    "PROFILE TURN", "WALK CYCLE", "WALK CYCLE", "STOP / FOLLOW-THROUGH",
    "LOOK BACK", "RUN CYCLE", "JUMP / TAKEOFF", "AIRBORNE / LAND",
    "RECOVERY", "FRONT RETURN",
]

def make_stage(index, ground_y):
    t = index / FPS
    # Vertical cinematic gradient.
    top = (11, 25, 42)
    bottom = (31, 60, 74)
    bg = Image.new("RGB", (W, H))
    pix = bg.load()
    for y in range(H):
        q = y / (H - 1)
        # Slightly brighter around the horizon, darker at the edges.
        v = q ** 1.45
        c = tuple(round(top[k]*(1-v) + bottom[k]*v) for k in range(3))
        for x in range(W):
            edge = abs(x-W/2)/(W/2)
            shade = 1 - 0.13*edge
            pix[x,y] = tuple(round(z*shade) for z in c)
    # Moving atmospheric pools / soft light, composited quietly.
    glow = Image.new("RGBA", (W,H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gx = int(W*0.52 + math.sin(t*0.24)*120)
    gd.ellipse((gx-420, ground_y-520, gx+420, ground_y+130), fill=(71,177,171,34))
    gd.ellipse((gx-180, ground_y-430, gx+180, ground_y+45), fill=(224,177,109,20))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    bg = Image.alpha_composite(bg.convert("RGBA"), glow)
    d = ImageDraw.Draw(bg, "RGBA")

    # Distant abstract pillars create depth and slow parallax.
    for i in range(9):
        x = int((i*190 - (t*14)%190) - 80)
        width = 64 + (i%3)*18
        height = 95 + (i%4)*31
        y0 = ground_y - height
        d.rounded_rectangle((x,y0,x+width,ground_y+8), radius=22,
                            fill=(53,102,117,22), outline=(122,180,177,24), width=2)
        d.line((x+width//2,y0+18,x+width//2,ground_y-8), fill=(174,202,185,15), width=2)

    # Ground plane and perspective guides.
    d.polygon([(0,ground_y-1),(W,ground_y-1),(W,H),(0,H)], fill=(18,39,51,170))
    d.line((0,ground_y,W,ground_y), fill=(150,205,192,115), width=2)
    vanishing = (W//2, ground_y-8)
    for x in range(-W, W*2, 180):
        d.line((vanishing[0],vanishing[1],x,H), fill=(126,177,174,26), width=2)
    for n in range(1,7):
        q = n/6
        y = int(ground_y + (H-ground_y)*q*q)
        d.line((0,y,W,y), fill=(126,177,174,18+int(12*q)), width=2)
    # Slow horizontal floor glints.
    shift = int((t*22) % 240)
    for x in range(-240+shift, W+240, 240):
        d.line((x,ground_y+26,x+100,ground_y+26), fill=(204,184,139,38), width=3)
    return bg

def composite_frame(src, idx, ground_y, out):
    char = Image.open(src).convert("RGBA")
    if char.size != (W,H):
        raise SystemExit(f"Unexpected Rigby frame size {char.size}: {src}")
    alpha = char.getchannel("A")
    bbox = alpha.getbbox()
    stage = make_stage(idx, ground_y)
    if bbox:
        x0,y0,x1,y1 = bbox
        cx = (x0+x1)/2
        bottom = y1
        lift = max(0, ground_y-bottom)
        # A separate contact shadow remains attached to the ground while the character rises.
        opacity = max(0.06, min(0.64, 0.58 - lift/430))
        rx = max(58, min(175, (x1-x0)*0.34 + lift*0.08))
        ry = max(9, 18 - lift*0.025)
        shadow = Image.new("RGBA", (W,H), (0,0,0,0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse((cx-rx,ground_y-ry,cx+rx,ground_y+ry),
                   fill=(3,10,18,int(255*opacity)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(13 + lift*0.045))
        stage = Image.alpha_composite(stage, shadow)
    stage = Image.alpha_composite(stage, char)
    d = ImageDraw.Draw(stage, "RGBA")
    # Small screen-space timecode and scene marker for test review.
    label = LABELS[min(len(LABELS)-1, idx//FPS)]
    d.rounded_rectangle((42,34,340,79), radius=13, fill=(4,15,27,150),
                        outline=(137,189,178,85), width=1)
    d.text((60,48), label, fill=(224,236,223,235), font=ImageFont.load_default())
    d.text((W-110,48), f"{idx/FPS:04.1f}s", fill=(218,225,212,185), font=ImageFont.load_default())
    stage.convert("RGB").save(out, quality=95)

def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: encode_reel.py FRAME_FOLDER OUTPUT_MP4 [POSTER_PNG]")
    folder = Path(sys.argv[1])
    output = Path(sys.argv[2])
    poster = Path(sys.argv[3]) if len(sys.argv) > 3 else output.with_name("maya-animation-contact-sheet.png")
    frames = sorted(folder.glob("*.png"))
    if len(frames) < 300:
        raise SystemExit(f"Expected at least 300 transparent Rigby frames; found {len(frames)}")
    # Estimate floor-contact baseline from the opening idle frames; jump shadow stays on that line.
    bottoms = []
    for frame in frames[:min(60,len(frames))]:
        im = Image.open(frame).convert("RGBA")
        box = im.getchannel("A").getbbox()
        if box:
            bottoms.append(box[3])
    if not bottoms:
        raise SystemExit("Rigby2D PNGs contain no character alpha")
    ground_y = round(sorted(bottoms)[len(bottoms)//2])
    stage_dir = output.parent / "composited-frames"
    stage_dir.mkdir(parents=True, exist_ok=True)
    for old in stage_dir.glob("frame_*.png"):
        old.unlink()
    contact_frames = []
    for i, src in enumerate(frames):
        out = stage_dir / f"frame_{i:06d}.png"
        composite_frame(src, i, ground_y, out)
        if i % FPS == 0:
            contact_frames.append(out)

    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(FPS), "-i", str(stage_dir / "frame_%06d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    subprocess.run(cmd, check=True)

    # The storyboard uses the exact composited frames, rather than the raw rig render.
    thumbs = []
    for sec, frame in enumerate(contact_frames[:13]):
        im = Image.open(frame).convert("RGB")
        im.thumbnail((320,180), Image.Resampling.LANCZOS)
        thumbs.append((sec,im))
    cols, rows, tw, th = 4, 4, 320, 180
    sheet = Image.new("RGB", (cols*tw, rows*(th+28)), "#12263a")
    draw = ImageDraw.Draw(sheet)
    for i,(sec,im) in enumerate(thumbs):
        x,y=(i%cols)*tw,(i//cols)*(th+28)
        sheet.paste(im,(x,y))
        draw.text((x+10,y+th+7),f"{sec:02d}s",fill="#f3e4c5",font=ImageFont.load_default())
    sheet.save(poster)
    report = {
        "png_frames": len(frames),
        "fps": FPS,
        "duration_seconds": round(len(frames)/FPS,3),
        "ground_y": ground_y,
        "compositor": "animated cinematic stage with perspective floor and ground-contact shadow",
        "video": str(output),
        "storyboard": str(poster),
    }
    output.with_suffix(".render.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    main()
