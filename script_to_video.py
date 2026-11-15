#!/usr/bin/env python3
"""Render a plain-text script as a kinetic illustrated 2D narrated video."""

import argparse
import json
from pathlib import Path

from script_to_story import script_file_to_story
from kinetic_renderer import render_story


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a narrated 2D animation from plain script text")
    parser.add_argument("--script", required=True, help="Path to a .txt script (blank lines separate scenes)")
    parser.add_argument("--output", default="output/animation.mp4", help="Output MP4 path")
    parser.add_argument("--voice", default="en-US-GuyNeural", help="Edge TTS voice, e.g. en-US-AriaNeural")
    parser.add_argument("--title", help="Video title (defaults to script filename)")
    parser.add_argument("--sentences-per-scene", type=int, default=3, help="Group this many sentences into each scene")
    parser.add_argument("--storyboard", help="Optionally save the generated storyboard JSON")
    args = parser.parse_args()

    story = script_file_to_story(
        args.script,
        title=args.title or Path(args.script).stem.replace("_", " ").title(),
        voice=args.voice,
        max_sentences=args.sentences_per_scene,
    )
    if args.storyboard:
        Path(args.storyboard).parent.mkdir(parents=True, exist_ok=True)
        Path(args.storyboard).write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_story(story, args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
