#!/usr/bin/env python3
"""Script-first documentary director: validate a narrative, build a shot plan, render it."""
import argparse, json, subprocess, sys
from pathlib import Path

ACTIONS={"approach","walk","lower","drink","lift","patrol","mark","listen","roar","rest"}
SHOT_TYPES={"establishing","tracking","character_closeup","action","reaction","wide_exit"}

def build_plan(source):
    story=json.loads(Path(source).read_text(encoding="utf-8"))
    scenes=story.get("scenes",[])
    if len(scenes)<5: raise ValueError("A documentary needs at least five distinct scenes")
    if story.get("fps",24)!=24: raise ValueError("Prototype renderer is locked to 24 fps")
    plan=[]
    for i,s in enumerate(scenes):
        narration=s.get("narration","").strip()
        action=s.get("animal_action","walk")
        if len(narration.split())<18: raise ValueError(f"Scene {i+1} narration is too short")
        if action not in ACTIONS: raise ValueError(f"Unsupported action in scene {i+1}: {action}")
        shot=s.get("shot_type",["establishing","tracking","character_closeup","action","reaction","wide_exit"][i%6])
        if shot not in SHOT_TYPES: raise ValueError(f"Unsupported shot type: {shot}")
        plan.append({
            "scene":i+1,"heading":s["heading"],"shot_type":shot,
            "environment":s.get("environment","savanna"),
            "cast":s.get("cast",["adult_male_lion"]),
            "primary_action":action,"camera_move":s.get("camera_move","slow_dolly"),
            "narration_words":len(narration.split()),
            "visual_beat":s.get("visual_beat",s.get("caption","")),
            "backend":"lion_render_v2"
        })
    if len({p["shot_type"] for p in plan})<4:
        raise ValueError("Shot plan lacks visual variety")
    return story,plan

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--script",required=True)
    p.add_argument("--output",default="output/documentary-prototype.mp4")
    a=p.parse_args()
    story,plan=build_plan(a.script)
    Path("output").mkdir(exist_ok=True)
    Path("output/director_plan.json").write_text(json.dumps({"title":story["title"],"fps":24,"shots":plan},indent=2))
    print("DIRECTOR PLAN:",len(plan),"shots |",len({x["shot_type"] for x in plan}),"shot types")
    # Keep narration, timing, and animation synchronized in the existing renderer.
    subprocess.run([sys.executable,"lion_render_v2.py","--script",a.script,"--output",a.output],check=True)
    print("Rendered:",a.output)

if __name__=="__main__": main()
