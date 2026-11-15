# Professional 2D Explainer Pilot

This branch adds a self-contained 30-second, 1920x1080, 24fps illustrated explainer render to the existing YT_channel repository.

## Run locally (Windows)

1. Install Python 3.11+.
2. Install FFmpeg and add it to PATH.
3. Install dependencies: `pip install pillow cairosvg`
4. Run: `python pro_2d_pilot.py --output output/brain-sleep-30s.mp4`

## GitHub Actions

Push changes to `feature/pro-2d-explainer` or manually run **Render professional 2D explainer pilot** from Actions. The MP4 and QA report are uploaded as an artifact.

## Production approach

- Python/CairoSVG renders reusable vector artwork at each frame.
- The presenter is a consistent layered vector character with animated body bounce, head tilt, and gesturing arms.
- Scene panels animate different educational visuals.
- FFmpeg encodes the rendered frame sequence.

This is a first automation prototype, not a finished studio-grade character rig. Next upgrade: replace procedural character geometry with a reusable Synfig rig authored once, then render the rig from the CLI and composite it with generated SVG scene layers. Synfig supports vector tweening, cutout animation, bones and command-line rendering; see https://www.synfig.org/ and https://wiki.synfig.org/Doc:Overview.
