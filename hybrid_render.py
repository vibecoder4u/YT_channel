#!/usr/bin/env python3
"""Blender-first renderer with guaranteed legacy fallback."""
import argparse, os, shutil, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--script',default='demo/rescue_at_the_river_55s.json')
p.add_argument('--output',default='output/hybrid-rescue.mp4')
a=p.parse_args()
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
blender=shutil.which('blender')
if blender:
 env=os.environ.copy(); env['BLENDER_OUTPUT']=str(out.with_suffix('.blender.mp4').resolve())
 cmd=[blender,'-b','--python','blender/rescue_scene.py']
 print('Trying Blender 3D renderer:', ' '.join(cmd),flush=True)
 result=subprocess.run(cmd,env=env)
 candidate=Path(env['BLENDER_OUTPUT'])
 if result.returncode==0 and candidate.exists() and candidate.stat().st_size>100_000:
  # Keep the Blender output as the main video; the fallback render is retained as a reference artifact.
  candidate.replace(out)
  print('ENGINE_SELECTED=BLENDER')
  sys.exit(0)
 print('Blender unavailable or render failed; switching to cinematic 2D fallback.',flush=True)
else:
 print('Blender executable missing; switching to cinematic 2D fallback.',flush=True)
fallback=out.with_name(out.stem+'-fallback.mp4')
cmd=[sys.executable,'human_render_cinematic.py','--script',a.script,'--output',str(fallback)]
subprocess.run(cmd,check=True)
shutil.copy2(fallback,out)
print('ENGINE_SELECTED=2D_FALLBACK')
