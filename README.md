# YT_channel: script-to-video animation engine

Turn a plain-text script or a topic outline into a narrated 2D explainer. The renderer uses procedural illustrations, animated diagrams, a presenter, captions, chapter cards, scene transitions, and configurable visual treatments. It uses Edge TTS for speech and FFmpeg for video; install FFmpeg separately and ensure it is available on `PATH`.

## Quick start

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python script_to_video.py --script my_script.txt --output output/my_video.mp4
```

Separate script sections with blank lines. Without blank lines, sentences are grouped into scenes. Structured JSON storyboards remain supported.

## Studio options

```bash
python script_to_video.py \
  --script my_script.txt \
  --output output/my_video.mp4 \
  --style cinematic \
  --transition wipe \
  --transition-seconds 0.6 \
  --chapter-every 2 \
  --storyboard output/storyboard.json
```

Styles: `cinematic`, `editorial`, `neon`, `paper`, `playful`. Transitions: `fade`, `wipe`, `zoom`, `cut`. Explicit `chapter` labels in a JSON scene are respected; otherwise a chapter is started every two scenes by default. Chapter boundaries and render details are saved to `output/render_report.json`.

## Topic outline mode

```bash
python script_to_video.py --topic "How do solar panels work?" --output output/solar.mp4
```

Topic mode generates a structured research outline with hook, definition, mechanism, comparison, evidence, and takeaway scenes. It intentionally inserts prompts for research rather than inventing facts or presenting generic claims as factual narration. Review and replace those prompts with sourced narration before publishing. Use `--storyboard` to save and edit the outline.

## Narration and scope

Narration is synthesized with the selected Edge TTS voice (`--voice en-US-AriaNeural`). Visual timing follows generated speech, with a configurable reading beat between scenes. This is a procedural 2D illustration system: visual style selection and icon drawing are local heuristics, not AI-generated images or a full 3D/rigged-character package.
