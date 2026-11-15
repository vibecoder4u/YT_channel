#!/usr/bin/env python3
"""Encode the Rigby2D PNG sequence and create a visual contact sheet."""
from pathlib import Path
import json
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) < 3:
    raise SystemExit("usage: encode_reel.py FRAME_FOLDER OUTPUT_MP4 [POSTER_PNG]")
folder = Path(sys.argv[1])
output = Path(sys.argv[2])
poster = Path(sys.argv[3]) if len(sys.argv) > 3 else output.with_name("maya-animation-contact-sheet.png")
frames = sorted(folder.glob("*.png"))
if len(frames) < 60:
    raise SystemExit(f"Expected at least 60 rendered PNG frames; found {len(frames)}")
output.parent.mkdir(parents=True, exist_ok=True)
pattern = str(folder / "*.png")
cmd = [
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-framerate", "30", "-pattern_type", "glob", "-i", pattern,
    "-c:v", "libx264", "-preset", "slow", "-crf", "17",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
]
subprocess.run(cmd, check=True)

# One frame per second, arranged as a compact action storyboard.
chosen = []
for sec in range(0, 13):
    index = min(len(frames)-1, sec*30)
    chosen.append((sec, Image.open(frames[index]).convert("RGB")))
thumb_w, thumb_h = 320, 180
cols, rows = 4, 4
sheet = Image.new("RGB", (cols*thumb_w, rows*(thumb_h+28)), "#182634")
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default()
for i, (sec, im) in enumerate(chosen):
    im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    x, y = (i % cols)*thumb_w, (i // cols)*(thumb_h+28)
    sheet.paste(im, (x, y))
    draw.text((x+10, y+thumb_h+7), f"{sec:02d}s", fill="#f3e4c5", font=font)
sheet.save(poster, quality=92)
report = {
    "png_frames": len(frames),
    "fps": 30,
    "duration_seconds": round(len(frames)/30, 3),
    "video": str(output),
    "storyboard": str(poster),
}
output.with_suffix(".render.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
