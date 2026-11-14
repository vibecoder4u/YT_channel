#!/usr/bin/env python3
"""Handwriting animation layer for the educational stickman renderer.

Keeps the existing presenter and diagrams, while adding a moving hand that
writes a scene takeaway onto a clean whiteboard one word at a time.
"""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import engine

def _hand_font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return engine.font(size)

def _layout_words(draw, text, fnt, max_width):
    words = str(text).split()
    lines, current, width = [], [], 0
    for word in words:
        word_width = draw.textlength(word, font=fnt)
        space = draw.textlength(" ", font=fnt) if current else 0
        if current and width + space + word_width > max_width:
            lines.append(current)
            current, width = [], 0
            space = 0
        current.append((word, width + space))
        width += space + word_width
    if current:
        lines.append(current)
    return words, lines

def _draw_writing_hand(draw, x, y, phase):
    """Draw a visible sleeve, palm, fingers and a pencil angled to the page."""
    wobble = math.sin(phase * 8.0) * 2.2
    x, y = int(x + wobble), int(y)
    # Forearm and cuff
    draw.line((x + 94, y + 83, x + 30, y + 34), fill=(53, 116, 158), width=34)
    draw.line((x + 94, y + 83, x + 30, y + 34), fill=(31, 74, 104), width=2)
    draw.line((x + 49, y + 48, x + 24, y + 27), fill=(230, 238, 239), width=5)
    # Palm and curled fingers
    draw.ellipse((x + 7, y + 15, x + 43, y + 52), fill=(244, 199, 163), outline=(74, 54, 47), width=2)
    for offset in (0, 8, 16):
        draw.arc((x + 12 + offset, y + 20, x + 31 + offset, y + 43), 190, 330, fill=(167, 112, 87), width=2)
    # Pencil points at the word currently being written.
    draw.line((x + 24, y + 29, x - 2, y - 12), fill=(219, 164, 74), width=7)
    draw.line((x + 24, y + 29, x - 2, y - 12), fill=(92, 68, 45), width=2)
    draw.polygon([(x - 2, y - 12), (x - 7, y - 21), (x + 4, y - 15)], fill=(49, 48, 45))
    draw.line((x + 18, y + 19, x + 27, y + 13), fill=(255, 255, 255), width=2)

def _overlay_handwriting(frame, scene, frame_index, frame_count):
    w, h = frame.size
    draw = ImageDraw.Draw(frame)
    # Keep the presenter visible on the left; use the right side as a writing board.
    panel = (int(w * .355), int(h * .175), int(w * .945), int(h * .665))
    x0, y0, x1, y1 = panel
    draw.rounded_rectangle((x0 + 5, y0 + 8, x1 + 5, y1 + 8), radius=24, fill=(225, 229, 226))
    draw.rounded_rectangle(panel, radius=24, fill=(255, 254, 248), outline=(205, 214, 211), width=3)
    draw.text((x0 + 30, y0 + 22), "KEY IDEA", font=engine.font(16, True), fill=(42, 137, 124))
    draw.line((x0 + 30, y0 + 54, x1 - 30, y0 + 54), fill=(224, 229, 222), width=2)

    message = scene.get("write_text") or scene.get("takeaway") or scene.get("caption") or scene.get("heading", "")
    fnt = _hand_font(29)
    max_width = x1 - x0 - 78
    words, lines = _layout_words(draw, message, fnt, max_width)
    line_gap = 66
    first_y = y0 + 112
    positions = []
    for li, line in enumerate(lines[:3]):
        baseline = first_y + li * line_gap
        for word, offset in line:
            positions.append((word, x0 + 38 + offset, baseline))
    # Reveal one word at a time. Once the sentence is complete, hold it on screen.
    elapsed = frame_index / max(1, frame_count - 1) * float(scene.get("duration", 5))
    count = min(len(positions), int(elapsed * float(scene.get("write_speed", 1.05))) + 1)
    for word, x, baseline in positions[:count]:
        draw.text((x, baseline), word, font=fnt, fill=(38, 58, 78))
        # Slight handwritten baseline strokes make the text feel drawn, not typed.
        ww = draw.textlength(word, font=fnt)
        draw.arc((x, baseline + 29, x + ww, baseline + 35), 5, 170, fill=(73, 119, 150), width=1)

    if positions and count < len(positions):
        word, wx, wy = positions[count - 1]
        ww = draw.textlength(word, font=fnt)
        cursor_x = wx + ww
        cursor_y = wy + 22
        _draw_writing_hand(draw, cursor_x - 20, cursor_y + 2, elapsed)
    elif positions:
        word, wx, wy = positions[-1]
        _draw_writing_hand(draw, wx + draw.textlength(word, font=fnt) - 16, wy + 24, elapsed)

    # Small live-writing indicator
    draw.ellipse((x1 - 35, y0 + 25, x1 - 23, y0 + 37), fill=(42, 163, 145))
    draw.text((x1 - 47, y0 + 44), "LIVE", font=engine.font(10, True), fill=(103, 117, 132), anchor="ra")
    return frame

_original_make_frame = engine.make_frame

def make_frame(scene, frame, frames, size, scene_number, scene_count, title):
    # engine.py previously animated against the JSON placeholder duration (1s),
    # even when narration made the rendered scene 15–25s long. Derive the real
    # scene duration from its rendered frame count so gestures and handwriting
    # continue throughout the spoken explanation instead of freezing early.
    timed_scene = dict(scene)
    timed_scene["duration"] = frames / 24.0  # current five-minute story is 24 fps
    image = _original_make_frame(timed_scene, frame, frames, size, scene_number, scene_count, title)
    # Give concept beats a clear hand-written teaching moment.
    if scene.get("handwrite", scene.get("visual") == "concept"):
        image = _overlay_handwriting(image, timed_scene, frame, frames)
    return image

engine.make_frame = make_frame

def run(story_path, output):
    engine.run(story_path, output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render educational video with animated handwriting")
    parser.add_argument("--script", default="demo/story_5min.json")
    parser.add_argument("--output", default="output/educational-5min.mp4")
    args = parser.parse_args()
    run(args.script, args.output)
