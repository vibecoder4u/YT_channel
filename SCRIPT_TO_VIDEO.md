## Try the studio animation with the included sample

The sample narration is in `demo/studio_sample.txt`. From the repository root, render it with:

```bash
python script_to_video.py \
  --script demo/studio_sample.txt \
  --output output/studio_sample.mp4 \
  --style cinematic \
  --transition fade \
  --storyboard output/studio_sample_storyboard.json
```

When rendering finishes, open `output/studio_sample.mp4`. The storyboard and `output/render_report.json` are also written for inspection. Rendering requires FFmpeg on `PATH` and network access for Edge TTS narration. You can try `--style neon`, `--style paper`, or `--transition wipe` to compare presets.
