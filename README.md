# Illustrated Stickman Educational Video Engine

A script-driven 2D educational renderer. It creates original stickman presenters, animated diagrams, timelines, process flows, comparison panels, and captions—without stock footage or manually supplied scene images.

## Long-form improvements
- **Narration-driven scene timing:** each scene length is measured from its generated voiceover, not a fixed timer.
- **Synchronized transitions:** a matching audio reading beat is inserted after each scene, preventing cumulative visual/audio drift.
- **Continuous motion:** presenter breathing, blinking and changing gestures; highlighted flow steps; animated timeline markers; staggered chart-bar reveals.
- **Educational visual vocabulary:** process flows, networks, cycles, timelines, comparisons, concept panels, and simple data charts.
- **Render QA:** automated tests check story structure and verify that frames change during a long scene. The Actions workflow checks H.264 video, AAC audio, and a minimum four-minute output.

## Five-minute demo
The included `demo/story_5min.json` is a 17-scene educational explainer, written for approximately five minutes of narration.

### GitHub Actions render
1. Open the repository's **Actions** tab.
2. Select **Render Educational Stickman Video**.
3. Click **Run workflow**.
4. Keep the default script `demo/story_5min.json` and output name `educational-5min`.
5. When the run completes, download the artifact named `educational-5min`. It contains the MP4 and QA reports.

Workflow: https://github.com/vibecoder4u/YT_channel/actions/workflows/render.yml

## Run locally
Requires Python 3.10+, FFmpeg, and network access for Edge TTS voice generation.

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python engine.py --script demo/story_5min.json --output output/educational-5min.mp4
```

## Script fields
Each scene supports:
- `narration`: spoken explanation; rendered duration follows the generated audio.
- `heading`, `caption`, `takeaway`: on-screen teaching hierarchy.
- `visual`: `concept`, `flow`, `process`, `network`, `timeline`, `compare`, `cycle`, or `stat`.
- `items` and optional `values`: labels/data for the selected visual.
- `action`: presenter pose such as `explain`, `point`, `think`, `walk`, or `celebrate`.
- `accent`: scene color.

## Honest scope
This is a procedural 2D illustrated foundation, not a finished studio-grade character-animation package. Motion is code-driven and intentionally lightweight; it is not skeletal character rigging or phoneme-level lip-sync. The workflow has been configured with automated checks, but a successful GitHub-hosted render is only confirmed after an Actions run completes.