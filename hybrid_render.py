#!/usr/bin/env python3
"""Blender-first renderer with cinematic 2D fallback and narration preservation."""
import argparse, os, shutil, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--script',default='demo/rescue_at_the_river_55s.json')
p.add_argument('--output',default='output/hybrid-rescue.mp4')
a=p.parse_args()
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
fallback=out.with_name(out.stem+'-fallback.mp4')
# Always render the proven pipeline first: it guarantees narration/audio and is the fallback.
subprocess.run([sys.executable,'human_render_cinematic.py','--script',a.script,'--output',str(fallback)],check=True)
blender=shutil.which('blender')
if blender:
 env=os.environ.copy(); env['BLENDER_OUTPUT']=str(out.with_suffix('.blender.mp4').resolve())
 cmd=[blender,'-b','--python','blender/rescue_scene.py']
 print('Trying optional Blender 3D renderer:', ' '.join(cmd),flush=True)
 result=subprocess.run(cmd,env=env)
 candidate=Path(env['BLENDER_OUTPUT'])
 if result.returncode==0 and candidate.exists() and candidate.stat().st_size>100_000:
  # Use Blender visuals and proven narration from fallback; cap audio to Blender duration.
  mux=subprocess.run(['ffmpeg','-y','-i',str(candidate),'-i',str(fallback),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest',str(out)],capture_output=True,text=True)
  if mux.returncode==0 and out.exists() and out.stat().st_size>100_000:
   print('ENGINE_SELECTED=BLENDER_WITH_2D_NARRATION')
   sys.exit(0)
  print('Blender audio mux failed; using complete 2D fallback.',mux.stderr[-1200:],flush=True)
 else:
  print('Blender unavailable or render failed; using complete 2D fallback.',flush=True)
else:
 print('Blender executable missing; using complete 2D fallback.',flush=True)
shutil.copy2(fallback,out)
print('ENGINE_SELECTED=2D_FALLBACK')
