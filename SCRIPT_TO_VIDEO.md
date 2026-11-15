# Plain-script animation

The existing renderer accepts detailed JSON storyboards. For a simpler workflow, this repository now includes a plain-text adapter: write narration in a `.txt` file, and it will split the copy into scenes, select an infographic style using lightweight keyword heuristics, synthesize narration with Edge TTS, and render an MP4 using the existing animation engine.

## Quick start

```bash
pip install -r requirements.txt
# FFmpeg must also be installed and available on PATH.
python script_to_video.py --script my_script.txt --output output/my_video.mp4
```

Separate scenes with a blank line. If you do not add blank lines, the adapter groups up to three sentences per scene. You can change that with `--sentences-per-scene 2`. Choose an Edge TTS voice with `--voice en-US-AriaNeural`, or set a title with `--title "My video"`.

This is an automatic storyboard adapter, not an AI writing or image-generation service: narration is spoken as written, visual type and labels are selected heuristically, and the renderer draws its built-in diagrams/presenter. For more precise art direction, use the repository's existing JSON story format and `engine.py`.
