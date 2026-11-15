#!/usr/bin/env python3
"""Create a studio-style narrated explainer from a script or topic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from script_to_story import generate_explainer_story, script_file_to_story
from studio_renderer import STYLES, TRANSITIONS, render_story


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a chaptered 2D explainer from a script or topic")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--script", help="Path to a .txt script or structured .json storyboard")
    source.add_argument("--topic", help="Topic prompt for a generic short-form explainer outline")
    parser.add_argument("--output", default="output/explainer.mp4", help="Output MP4")
    parser.add_argument("--voice", default="en-US-GuyNeural", help="Edge TTS voice")
    parser.add_argument("--title", help="Optional video title")
    parser.add_argument("--style", choices=sorted(STYLES), default="cinematic")
    parser.add_argument("--transition", choices=sorted(TRANSITIONS), default="fade")
    parser.add_argument("--transition-seconds", type=float, default=.55)
    parser.add_argument("--chapter-every", type=int, default=2, help="Start a new chapter every N scenes if none is supplied")
    parser.add_argument("--sentences-per-scene", type=int, default=3)
    parser.add_argument("--storyboard", help="Save the generated storyboard JSON")
    args = parser.parse_args()

    if args.topic:
        story = generate_explainer_story(args.topic, title=args.title, voice=args.voice)
    else:
        story = script_file_to_story(
            args.script,
            title=args.title or Path(args.script).stem.replace("_", " ").title(),
            voice=args.voice,
            max_sentences=args.sentences_per_scene,
        )
    if args.storyboard:
        path = Path(args.storyboard)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_story(
        story,
        args.output,
        style=args.style,
        transition=args.transition,
        transition_seconds=args.transition_seconds,
        chapter_every=args.chapter_every,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
