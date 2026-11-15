# Plain-script animation

The plain-text workflow renders kinetic illustrated scenes: atmospheric parallax backgrounds, a presenter with a walk/gesture cycle, animated infographic elements that enter in sequence, camera drift, and narration-synchronized captions.

## Quick start

```bash
pip install -r requirements.txt
# FFmpeg must also be installed and available on PATH.
python script_to_video.py --script my_script.txt --output output/my_video.mp4
```

Separate scenes with a blank line. Without blank lines, the adapter groups up to three sentences per scene. Configure the grouping with `--sentences-per-scene 2`; choose an Edge TTS voice using `--voice en-US-AriaNeural`; save the generated storyboard with `--storyboard output/storyboard.json`.

The plain-text adapter automatically builds a storyboard using deterministic keyword heuristics. It does not call an LLM or image-generation API; it animates its built-in vector illustrations and visual vocabulary. For detailed art direction, use the JSON storyboard format with the original `engine.py` workflow.
