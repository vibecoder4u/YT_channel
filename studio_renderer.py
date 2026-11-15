"""Cinematic short-form rendering built on the repo's illustrated frame engine.

Adds configurable art treatments, chapter cards, and in-scene transitions while
keeping scene duration aligned with narration. This is procedural 2D motion art,
not an AI image-generation service.
"""

from __future__ import annotations

import asyncio
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import engine
from kinetic_renderer import H, W, make_kinetic_frame

STYLES = {"cinematic", "editorial", "neon", "paper", "playful"}
TRANSITIONS = {"fade", "wipe", "zoom", "cut"}


def apply_style(image: Image.Image, style: str) -> Image.Image:
    """Apply a consistent finish to a frame without external assets."""
    if style not in STYLES:
        raise ValueError(f"Unknown visual style {style!r}. Choose from: {', '.join(sorted(STYLES))}")
    out = image.convert("RGB")
    if style == "cinematic":
        out = ImageEnhance.Color(out).enhance(1.13)
        out = ImageEnhance.Contrast(out).enhance(1.09)
        d = ImageDraw.Draw(out, "RGBA")
        d.rectangle((0, 0, W, 26), fill=(7, 16, 29, 180))
        d.rectangle((0, H-26, W, H), fill=(7, 16, 29, 180))
    elif style == "editorial":
        out = ImageEnhance.Color(out).enhance(.82)
        out = ImageEnhance.Contrast(out).enhance(1.04)
        d = ImageDraw.Draw(out, "RGBA")
        for x in range(32, W, 64):
            d.line((x, 0, x, H), fill=(255,255,255,19), width=1)
    elif style == "neon":
        out = ImageEnhance.Color(out).enhance(1.48)
        out = ImageEnhance.Contrast(out).enhance(1.12)
        glow = out.filter(ImageFilter.GaussianBlur(12))
        out = Image.blend(out, glow, .10)
    elif style == "paper":
        out = ImageOps.colorize(ImageOps.grayscale(out), black="#243746", white="#f2e7cb").convert("RGB")
        d = ImageDraw.Draw(out, "RGBA")
        for y in range(14, H, 14):
            d.line((0, y, W, y), fill=(74,66,48,13), width=1)
    elif style == "playful":
        out = ImageEnhance.Color(out).enhance(1.26)
        out = ImageEnhance.Contrast(out).enhance(1.03)
    return out


def transition_frame(previous: Image.Image, current: Image.Image, progress: float, transition: str) -> Image.Image:
    """Compose one frame of an incoming-scene transition."""
    p = max(0.0, min(1.0, progress))
    if transition not in TRANSITIONS:
        raise ValueError(f"Unknown transition {transition!r}. Choose from: {', '.join(sorted(TRANSITIONS))}")
    if transition == "cut" or p >= 1:
        return current
    if transition == "fade":
        return Image.blend(previous, current, p)
    if transition == "wipe":
        result = previous.copy()
        x = int(result.width * p)
        if x:
            result.paste(current.crop((0, 0, x, result.height)), (0, 0))
        return result
    # Zoom-like reveal: scale the incoming image from the center and dissolve edges.
    scale = .94 + .06 * p
    resized = current.resize((max(1, int(current.width*scale)), max(1, int(current.height*scale))), Image.Resampling.BICUBIC)
    layer = Image.new("RGB", current.size, (0,0,0))
    layer.paste(resized, ((current.width-resized.width)//2, (current.height-resized.height)//2))
    return Image.blend(previous, layer, p)


def _draw_title_card(frame: Image.Image, title: str, chapter: str, style: str, opening: bool) -> Image.Image:
    image = frame.convert("RGBA")
    d = ImageDraw.Draw(image, "RGBA")
    if opening:
        d.rectangle((0,0,W,H), fill=(8,19,32,115))
        d.rounded_rectangle((94,180,1186,514), radius=34, fill=(9,24,41,220), outline=(255,255,255,95), width=2)
        d.rectangle((142,232,153,462), fill=(255,195,91,255))
        d.text((190,265), "A SHORT EXPLAINER", font=engine.font(19, True), fill=(255,204,115,255))
        title_lines = engine.wrap(title, 35)[:3]
        for index, line in enumerate(title_lines):
            d.text((190,320+index*59), line, font=engine.font(43, True), fill=(255,255,255,255))
        d.text((190,466), "THE IDEA • THE MECHANISM • THE TAKEAWAY", font=engine.font(16, True), fill=(205,218,229,255))
    elif chapter:
        d.rounded_rectangle((70,88,465,145), radius=18, fill=(9,24,41,190), outline=(255,255,255,80), width=1)
        d.text((94,103), "CHAPTER  ·  " + chapter[:30].upper(), font=engine.font(17, True), fill=(255,255,255,255))
    return image.convert("RGB")


def prepare_story(story: dict[str, Any], chapter_every: int = 2) -> list[dict[str, Any]]:
    """Assign readable chapter boundaries where scripts have no chapter markup."""
    if chapter_every < 1:
        raise ValueError("chapter_every must be at least one scene")
    scenes = story["scenes"]
    current_chapter = ""
    for index, scene in enumerate(scenes):
        if scene.get("chapter"):
            current_chapter = str(scene["chapter"])
        elif index % chapter_every == 0:
            current_chapter = str(scene.get("heading") or f"Part {index // chapter_every + 1}")
            scene["chapter"] = current_chapter
        scene["_chapter_start"] = index == 0 or bool(scene.get("chapter")) and (index == 0 or scenes[index-1].get("chapter") != scene.get("chapter"))
    return scenes


def render_story(
    story: dict[str, Any],
    output: str | Path,
    *,
    style: str = "cinematic",
    transition: str = "fade",
    transition_seconds: float = .55,
    chapter_every: int = 2,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Synthesize narration and render a chaptered, styled explainer MP4."""
    engine.validate_story(story)
    if style not in STYLES:
        raise ValueError(f"Unknown style {style!r}. Choose from: {', '.join(sorted(STYLES))}")
    if transition not in TRANSITIONS:
        raise ValueError(f"Unknown transition {transition!r}. Choose from: {', '.join(sorted(TRANSITIONS))}")
    if transition_seconds < 0:
        raise ValueError("transition_seconds cannot be negative")
    fps = int(story.get("fps", 24))
    size = (int(story.get("width", W)), int(story.get("height", H)))
    if size != (W, H):
        raise ValueError(f"Studio renderer currently requires {W}x{H} output; received {size[0]}x{size[1]}")

    scenes = prepare_story(story, chapter_every)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(work_dir) if work_dir else output.parent / (output.stem + "_work")
    audio_dir = work / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    beat = max(0.0, float(story.get("reading_beat", .35)))
    audio_paths: list[Path] = []
    durations: list[float] = []
    voice = story.get("voice", "en-US-GuyNeural")
    rate = story.get("rate", "+0%")

    print(f"[studio] Preparing narration for {len(scenes)} scenes", flush=True)
    for index, scene in enumerate(scenes):
        audio = audio_dir / f"scene_{index:04d}.mp3"
        print(f"[studio] TTS scene {index + 1}/{len(scenes)}: {scene.get('heading', 'Untitled')[:64]}", flush=True)
        boundaries = asyncio.run(engine.synthesize(scene["narration"], voice, audio, rate))
        duration = engine.probe_duration(audio)
        durations.append(duration)
        scene["_render_duration"] = duration + beat
        scene["_caption_cues"] = engine.build_caption_cues(boundaries, scene["narration"], duration)
        padded = audio_dir / f"padded_{index:04d}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), "-af", f"apad=pad_dur={beat}", "-c:a", "libmp3lame", str(padded)], check=True)
        audio_paths.append(padded)
        print(f"[studio] Audio ready {index + 1}/{len(scenes)} ({duration:.1f}s)", flush=True)

    total_frames = sum(max(1, math.ceil((duration + beat) * fps)) for duration in durations)
    print(f"[studio] Starting frame render: {total_frames} frames at {fps} fps across {len(scenes)} scenes", flush=True)
    raw = work / "studio_video.mp4"
    command = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", str(raw)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    chapters: list[dict[str, Any]] = []
    elapsed = 0.0
    previous_last: Image.Image | None = None
    try:
        for scene_index, (scene, narration_duration) in enumerate(zip(scenes, durations)):
            seconds = narration_duration + beat
            count = max(1, math.ceil(seconds * fps))
            transition_frames = min(count // 3, max(0, round(transition_seconds * fps))) if scene_index and transition != "cut" else 0
            if scene.get("_chapter_start"):
                chapters.append({"title": scene.get("chapter", scene.get("heading", "Chapter")), "start_seconds": round(elapsed, 2), "scene": scene_index + 1})
            print(f"[studio] Rendering scene {scene_index + 1}/{len(scenes)} ({count} frames)", flush=True)
            progress_interval = max(1, count // 4)
            for frame_index in range(count):
                if frame_index % progress_interval == 0:
                    print(f"[studio] Scene {scene_index + 1}/{len(scenes)}: frame {frame_index + 1}/{count}", flush=True)
                rendered = make_kinetic_frame(scene, frame_index, count, scene_index+1, len(scenes), story.get("title", "A Story, Illustrated"))
                rendered = apply_style(rendered, style)
                local_time = frame_index / fps
                if scene_index == 0 and local_time < 1.65:
                    rendered = _draw_title_card(rendered, story.get("title", "A Story, Illustrated"), "", style, opening=True)
                elif scene.get("_chapter_start") and local_time < 1.15:
                    rendered = _draw_title_card(rendered, "", str(scene.get("chapter", "")), style, opening=False)
                if previous_last is not None and frame_index < transition_frames:
                    rendered = transition_frame(previous_last, rendered, (frame_index+1)/transition_frames, transition)
                process.stdin.write(rendered.tobytes())
            previous_last = apply_style(make_kinetic_frame(scene, count-1, count, scene_index+1, len(scenes), story.get("title", "A Story, Illustrated")), style)
            elapsed += seconds
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg failed while encoding the studio animation")
    print("[studio] Video frames encoded; assembling narration audio", flush=True)

    concat = work / "audio.txt"
    concat.write_text("".join(f"file '{path.resolve()}'\n" for path in audio_paths), encoding="utf-8")
    voice_file = work / "voiceover.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "libmp3lame", str(voice_file)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-i", str(voice_file), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output)], check=True)

    report = {
        "title": story.get("title", ""),
        "scenes": len(scenes),
        "chapters": chapters,
        "narration_seconds": round(sum(durations), 2),
        "video_seconds": round(engine.probe_duration(output), 2),
        "fps": fps,
        "resolution": f"{W}x{H}",
        "renderer": "studio-2d",
        "style": style,
        "transition": transition,
    }
    (output.parent / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
