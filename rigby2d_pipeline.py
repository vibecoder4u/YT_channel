#!/usr/bin/env python3
"""Assemble Rigby2D transparent PNG action exports into a timed character-test reel.

Expected layout:
assets/rigby2d/hero/
  manifest.json
  front_intro/*.png
  turn_threequarter/*.png
  turn_profile/*.png
  walk/*.png
  stop_momentum/*.png
  look_back/*.png
  run/*.png
  jump/*.png
  land/*.png
  front_expression/*.png

Each folder contains sequential transparent PNG frames exported from Rigby2D.
No substitute stick-figure renderer is used: missing action exports fail the quality gate.
"""
from __future__ import annotations
import argparse, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

W, H, FPS = 1280, 720, 30
ROOT = Path("assets/rigby2d/hero")
ACTIONS = [
    ("front_intro", 1.2, "FRONT INTRO"),
    ("turn_threequarter", 0.8, "THREE-QUARTER TURN"),
    ("turn_profile", 0.8, "SIDE PROFILE"),
    ("walk", 2.0, "FAST WALK"),
    ("stop_momentum", 0.7, "STOP / FOLLOW-THROUGH"),
    ("look_back", 0.8, "LOOK BEHIND"),
    ("run", 1.5, "RUN"),
    ("jump", 0.8, "JUMP"),
    ("land", 0.8, "LAND / RECOVER"),
    ("front_expression", 1.0, "FRONT EXPRESSION"),
]

def load_manifest():
    p = ROOT / "manifest.json"
    if not p.exists():
        raise SystemExit(f"Missing {p}. Follow docs/RIGBY2D_PIPELINE.md to export the rig.")
    data = json.loads(p.read_text())
    if data.get("source") != "Rigby2D" or not data.get("character_name"):
        raise SystemExit("manifest.json must identify source=Rigby2D and character_name.")
    return data

def action_frames(name):
    folder = ROOT / name
    frames = sorted(folder.glob("*.png")) if folder.exists() else []
    if len(frames) < 8:
        raise SystemExit(f"QUALITY GATE: {name} needs at least 8 PNG frames; found {len(frames)}.")
    return frames

def make_background(index, label, t):
    im = Image.new("RGBA", (W, H), (17, 27, 39, 255))
    d = ImageDraw.Draw(im)
    # cinematic layered studio environment and moving light bands
    for y in range(H):
        q = y / H
        col = (int(20+18*q), int(35+24*q), int(51+27*q), 255)
        d.line((0,y,W,y), fill=col)
    for i in range(12):
        x = int((i*143 + t*48) % (W+240))-120
        d.ellipse((x-110, 120+i%4*90, x+110, 340+i%4*90), fill=(39,70,83,48))
    d.rectangle((0, 620, W, H), fill=(13,22,30,255))
    d.line((0,620,W,620), fill=(76,125,139,255), width=2)
    d.rounded_rectangle((34,28,1246,92), radius=16, fill=(8,16,25,210), outline=(96,155,165,255), width=2)
    d.text((62,60), label, fill=(238,244,238,255), anchor="lm")
    d.text((1215,60), f"{t:05.2f}s", fill=(150,202,204,255), anchor="rm")
    return im

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", default="output/rigby2d-character-test.mp4")
    ap.add_argument("--frames-dir", default="output/rigby2d-composite")
    args=ap.parse_args()
    manifest=load_manifest()
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    frame_dir=Path(args.frames_dir); frame_dir.mkdir(parents=True,exist_ok=True)
    # Validate all action exports before rendering any output.
    clips={name:action_frames(name) for name,_,_ in ACTIONS}
    total=round(sum(duration for _,duration,_ in ACTIONS)*FPS)
    canvas=(W,H)
    index=0; elapsed=0.0
    for name,duration,label in ACTIONS:
        src=clips[name]; count=round(duration*FPS)
        for n in range(count):
            # sample every source frame, then hold only when the authored clip is shorter
            k=min(len(src)-1, int(n*len(src)/count))
            fg=Image.open(src[k]).convert("RGBA")
            if fg.getbbox() is None:
                raise SystemExit(f"Empty transparent frame: {src[k]}")
            # fit character while preserving aspect ratio; exported art remains detailed
            max_w,max_h=430,540
            scale=min(max_w/fg.width,max_h/fg.height)
            fg=fg.resize((max(1,int(fg.width*scale)),max(1,int(fg.height*scale))),Image.Resampling.LANCZOS)
            t=elapsed+n/FPS
            bg=make_background(index,label,t)
            # small camera push during run and jump; stable foot baseline otherwise
            motion=1.0 + (0.07*math.sin(math.pi*n/max(1,count-1)) if name in ("run","jump") else 0)
            if motion != 1.0:
                fg=fg.resize((int(fg.width*motion),int(fg.height*motion)),Image.Resampling.LANCZOS)
            x=(W-fg.width)//2
            y=620-fg.height
            bg.alpha_composite(fg,(x,y))
            bg.convert("RGB").save(frame_dir/f"frame_{index:05d}.png",quality=95)
            index+=1
        elapsed+=duration
    if index != total:
        raise SystemExit(f"Frame count mismatch: expected {total}, got {index}")
    cmd=["ffmpeg","-y","-framerate",str(FPS),"-i",str(frame_dir/"frame_%05d.png"),
         "-c:v","libx264","-pix_fmt","yuv420p","-preset","medium","-crf","17",
         "-movflags","+faststart",str(out)]
    subprocess.run(cmd,check=True)
    report={"character":manifest["character_name"],"source":"Rigby2D",
            "fps":FPS,"frames":index,"duration_seconds":round(index/FPS,3),
            "resolution":f"{W}x{H}","actions":[{"name":n,"frames":len(clips[n])} for n,_,_ in ACTIONS],
            "output":str(out)}
    (out.parent/"rigby2d-report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
