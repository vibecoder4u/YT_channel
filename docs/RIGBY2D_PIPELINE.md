# Rigby2D character pipeline

This is the character-animation lane for the video engine. The workflow now generates an original, layered SVG character rig and ten articulated action sequences in CI, renders transparent PNG frames, then assembles them into a timed MP4. Rigby2D exports remain supported as an alternate input. Blender remains an optional separate lane. The old PIL renderer remains a fallback for existing projects, but it is **not** accepted as a substitute in this character quality test.

## 1. Create the character in Rigby2D

1. Install/open Rigby2D: https://github.com/jaisurya-dev-art/rigby2d (MIT/Apache-2.0 source; check licenses for any imported art).
2. Create an original character design with layered SVG/PSD artwork. Do not reuse Rigby2D's demo mascots or artwork as our production character.
3. Import the layered artwork, AutoRig it, refine bone weights and IK, and create face controls.
4. Create separate authored animations for the action names below. Use distinct head/face artwork for front, three-quarter and profile; do not rotate a front-facing face to fake a profile.
5. In the Film workspace, export each animation as a transparent PNG sequence at 30 FPS. Use consistent canvas size, character scale, pivot and foot baseline for every clip.
6. Copy the exported frames into the matching folders under `assets/rigby2d/hero/`.

## 2. Required export contract

```text
assets/rigby2d/hero/
  manifest.json
  front_intro/*.png
  turn_threequarter/*.png
  turn_profile/*.png
  walk/*.png
  stop_momentum/*.png
  look_back/*.png
  run/*.png
  jump/*.png
  land/*.png
  front_expression/*.png
```

Example `manifest.json`:

```json
{
  "source": "Rigby2D",
  "character_name": "Maya",
  "authoring_fps": 30,
  "views": ["front", "threequarter", "profile"],
  "transparent_background": true
}
```

Each action must contain at least 8 sequential PNG frames. Keep the character fully inside the transparent canvas. All clips must use the same scale and ground/pivot convention.

## 3. Build locally

```bash
pip install Pillow
python rigby2d_pipeline.py --output output/rigby2d-character-test.mp4
```

FFmpeg must be installed and on PATH. The generator produces a 12.2-second 1280x720 30-FPS action reel with distinct front, three-quarter and profile facial construction, animated limbs, walk/run cycles, stop follow-through, jump and landing poses. It is a procedural 2D vector rig—not a hand-drawn frame-by-frame animation or a production-grade commercial rig. Inspect the MP4 for visual quality before using it.

## 4. GitHub Actions

Run **Rigby2D Character Pipeline** with `workflow_dispatch`, or push changes to this workflow, adapter, docs, or the exported character assets. It validates the complete export contract, renders the MP4, checks duration/resolution/frame rate, and uploads the video plus report.

## 5. Quality gate

The workflow generates and validates all ten action folders in CI, then fails if any action folder is missing, has fewer than 8 frames, or contains empty frames. Human review must confirm:
- recognisable designed character, consistent across views;
- genuine side-profile facial anatomy;
- alternating walk/run foot contacts and no foot sliding;
- visible stop inertia and follow-through;
- head turn is independent from torso;
- readable jump arc, anticipation, landing compression and recovery.

A green workflow means the export contract and video render passed. It does not certify artistic quality; inspect the MP4 before approving the character for documentary production.
