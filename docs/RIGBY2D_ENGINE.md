# Rigby2D skeletal animation engine

This is the new character-animation engine lane. It replaces the old PNG-pose generator for new character work. The old compositor remains available only as a baseline; it is not the animation engine.

## Architecture

1. **Original layered character artwork** — animation_engine/generate_character_art.py draws an original expedition character as separate transparent body-part images. The PSD preserves the layers and their positions.
2. **Real character rig** — the build imports that PSD into Rigby2D and runs AutoRig. The resulting .rigby project contains an editable skeleton and weighted deforming meshes. We remove AutoRig's fixed hand-target IK constraints so keyed shoulder/elbow arcs can animate freely, while retaining the two foot IK constraints for grounded locomotion. The workflow records and validates these controls.
3. **Motion authoring** — animation_engine/build_character_project.mjs creates one 12.2-second timeline with bone keyframes, foot-target keys, ease/settle beats and explicit front / three-quarter / profile / look-back artwork swaps.
4. **Native skeletal render** — the pinned Rigby2D CLI evaluates the .rigby animation and renders a PNG sequence through its editor renderer in headless Chromium. FFmpeg only encodes those evaluated frames to H.264; it does not animate or move the character.
5. **Validation and review** — CI checks rig controls, animation duration/keyed channels, frame count, output dimensions and frame rate. The storyboard contact sheet and the .rigby source are included in the artifact so the actual rig can be inspected.

## Engine dependency

The workflow pins Rigby2D to:

- Repository: https://github.com/jaisurya-dev-art/rigby2d
- Commit: cbc19079c5dd499c70f9b0e69fc04265f0346dc4
- Upstream package version at that commit: 0.5.1

The CLI/windowless rendering integration at this commit is from upstream develop, not a released package tag. It is deliberately pinned and tested in CI. Upgrade only after a successful compatibility test; do not follow the moving develop branch in production.

Rigby2D is an open-source 2D skeletal-animation tool. Its own documentation describes layered PSD/SVG import, AutoRig, bones, weighted meshes, IK, retargeting, face controls, Film output and PNG/WebM/MP4 rendering. The channel's character artwork is original; do not copy the upstream demo mascots or branded art.

## Character and motion test

The current Maya asset is a pipeline test character, not final production character art. The second engineering pass also adds a compositing stage, with a perspective floor and contact shadow that stays on the ground while the character jumps. The action reel is designed to test:

- front introduction and breathing;
- switch to a separately drawn three-quarter head;
- switch to a separately drawn profile head and profile torso/pelvis artwork;
- a walk cycle with alternating leg motion and IK foot-target contacts;
- stop deceleration and upper-body follow-through;
- a separate over-the-shoulder head illustration;
- a faster run cycle with a larger flight phase;
- jump anticipation, takeoff, airborne tuck, landing compression and recovery;
- return to front-facing artwork.

The animation is one editable skeletal timeline rather than a sequence of unrelated images. Motion is sampled at multiple points and interpolated by Rigby2D. Foot IK targets are animated to make contact and swing arcs explicit.

## Important limitations

This is a **2D skeletal puppet engine**, not a 3D character renderer or a frame-by-frame hand-drawn studio. A convincing side turn still requires well-designed alternate drawings; rotating the front face is not an acceptable substitute. The first prototype's alternate views are explicit artwork swaps, and its side body is still a simplified view treatment.

The test character does not yet have a complete facial-control library, detailed finger poses, production skinning/weight cleanup, secondary cloth/hair physics, lip-sync, or a large reusable motion library. Those are subsequent engine milestones after this core rig/render path passes visual inspection.

A successful action run proves the rig could be built, keyed and rendered. It does **not** prove the character animation is publishable. Review the actual MP4 and storyboard before approving it for a full documentary.

## Run locally

The workflow installs the pinned upstream source and its CLI dependencies. In the same environment:

    python -m pip install cairosvg pillow
    python animation_engine/generate_character_art.py
    node animation_engine/build_character_project.mjs
    node vendor/rigby2d/bin/rigby.js render build/maya-character.rigby --animation character_showcase --out build/rigby-frames/ --format png --engine chromium --allow-software --fps 30 --width 1280 --height 720
    python animation_engine/encode_reel.py build/rigby-frames build/maya-character-animation-engine-test.mp4

The GitHub Actions workflow is **Rigby2D Skeletal Animation Engine Prototype**. It uploads the MP4, storyboard, PSD artwork, editable .rigby project, rig report, animation report and validation data.
