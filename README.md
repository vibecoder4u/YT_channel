#!/usr/bin/env python3
"""Render a narrated explainer from either a script file or a plain topic prompt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kinetic_renderer import render_story
from script_to_story import generate_explainer_story, script_file_to_story


def main() -> None:
    parser = argparse.ArgumentParser(description="Make a polished short-form explainer video from a script or prompt")
    parser.add_argument("--script", help="Path to a .txt or .json story file")
    parser.add_argument("--topic", help="One-line topic prompt to auto-build a polished explainer story")
    parser.add_argument("--output", default="output/explainer.mp4", help="Output MP4 path")
    parser.add_argument("--voice", default="en-US-GuyNeural", help="Edge TTS voice")
    parser.add_argument("--title", help="Optional title override")
    parser.add_argument("--sentences-per-scene", type=int, default=3, help="Sentence grouping for plain text scripts")
    parser.add_argument("--storyboard", help="Optional path to save the generated storyboard JSON")
    args = parser.parse_args()

    if args.topic:
        story = generate_explainer_story(args.topic, title=args.title, voice=args.voice)
    elif args.script:
        story = script_file_to_story(
            args.script,
            title=args.title or Path(args.script).stem.replace("_", " ").title(),
            voice=args.voice,
            max_sentences=args.sentences_per_scene,
        )
    else:
        raise SystemExit("Provide either --script or --topic.")

    if args.storyboard:
        Path(args.storyboard).parent.mkdir(parents=True, exist_ok=True)
        Path(args.storyboard).write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_story(story, args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
