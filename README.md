# Illustrated Stickman Documentary Engine

A script-driven 2D animation renderer for documentary and educational videos. It draws original stickman characters and scene artwork procedurally—no stock footage and no manually supplied scene images.

## Features
- Expressive poses: typing, thinking, waving, running, pointing and celebrating.
- Themed environments, network diagrams and server illustrations.
- Narration generated with Edge TTS and scene captions rendered into the video.
- 1280x720 H.264 MP4 at 24 fps by default.
- Local rendering and GitHub Actions rendering.

## Run locally
Requires Python 3.10+, FFmpeg and dependencies in requirements.txt.

```bash
pip install -r requirements.txt
python engine.py --script demo/story.json --output output/demo.mp4
```

## Render using GitHub Actions
1. Open the Actions tab.
2. Select **Render Stickman Video**.
3. Click **Run workflow**.
4. Use `demo/story.json` or provide another JSON script path.
5. Download the `stickman-documentary` artifact after the run completes.

## Script format
Each scene supports `duration`, `narration`, `caption`, `character`, `action`, `background`, optional `diagram`, and `accent`. See `demo/story.json` for a complete example.

## Honest scope
This is the first procedural 2D foundation, not a finished studio-grade animation product. It draws characters and scenes with code rather than AI-generated character art. The next quality improvements are reusable character rigs, richer hand-drawn assets, lip-sync, and word-level caption timing.
