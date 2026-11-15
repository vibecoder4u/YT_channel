# Legacy PNG character compositor

**This is the previous prototype, not the current animation engine.** It consumes already-rendered transparent PNG frames and composites them onto a stage. It does not create a skeletal character rig, solve IK, deform weighted meshes or evaluate bone animation.

Its outputs were useful for checking the video assembly path, but the Maya reel looked like a sequence of flat cutout poses. Do not extend this renderer as the main character-animation system.

Use the new [Rigby2D skeletal animation engine](RIGBY2D_ENGINE.md) instead. The new workflow imports layered artwork, AutoRigs a reusable skeleton with mesh deformation and IK, creates keyframes on bones/IK targets and renders those evaluated poses with the Rigby2D runtime.

The old workflow remains in this experimental branch as a baseline for comparing video assembly and visual quality. A green result from this legacy workflow is not an animation-quality approval.
