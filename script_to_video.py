#!/usr/bin/env python3
"""Render a plain-text script as an illustrated 2D narrated video."""

import argparse
import json
import tempfile
from pathlib import Path

import engine
from script_to_story import script_file_to_story


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a narrated 2D animation from plain script text")
    parser.add_argument("--script", required=True, help="Path to a .txt script (blank lines separate scenes)")
    parser.add_argument("--output", default="output/animation.mp4", help="Output MP4 path")
    parser.add_argument("--voice", default="en-US-GuyNeural", help="Edge TTS voice, e.g. en-US-AriaNeural")
    parser.add_argument("--title", help="Video title (defaults to the script filename)")
    parser.add_argument("--sentences-per-scene", type=int, default=3, help="Group this many sentences into each scene")
    args = parser.parse_args()

    story = script_file_to_story(
        args.script,
        title=args.title or Path(args.script).stem.replace("_", " ").title(),
        voice=args.voice,
        max_sentences=args.sentences_per_scene,
    )
    # Use a temporary JSON storyboard so the established engine can render the
    # generated scenes without changing or duplicating its audio/video pipeline.
    with tempfile.TemporaryDirectory(prefix="yt-channel-story-") as temp_dir:
        storyboard = Path(temp_dir) / "story.json"
        storyboard.write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
        engine.run(storyboard, args.output)


if __name__ == "__main__":
    main()
