#!/usr/bin/env python3
"""Prepare an AutoRigged character for animation.

Rigby AutoRig creates IK on arms and legs by default. This action-reel prototype
uses keyframed arm arcs and keeps only leg IK so foot contacts can be solved.
"""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import json
import sys
import tempfile
import os

if len(sys.argv) != 2:
    raise SystemExit("usage: prepare_rig.py CHARACTER.rigby")
path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(f"Rig file not found: {path}")
with ZipFile(path, "r") as src:
    names = src.namelist()
    if "project.json" not in names:
        raise SystemExit("Invalid .rigby project: project.json missing")
    project = json.loads(src.read("project.json"))
    before = list(project.get("ik", []))
    project["ik"] = [c for c in before if not c.get("name", "").startswith("ik_hand_")]
    removed = sorted(c["name"] for c in before if c.get("name", "").startswith("ik_hand_"))
    if len(removed) != 2:
        raise SystemExit(f"Expected two arm IK constraints, removed {removed}")
    fd, tmp_name = tempfile.mkstemp(suffix=".rigby", dir=path.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with ZipFile(tmp, "w", ZIP_DEFLATED) as dst:
            for name in names:
                data = json.dumps(project, separators=(",", ":")).encode() if name == "project.json" else src.read(name)
                dst.writestr(name, data)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
print(json.dumps({
    "file": str(path),
    "removed_arm_ik": removed,
    "remaining_ik": [c["name"] for c in project.get("ik", [])],
    "bone_count": len(project.get("bones", [])),
    "slot_count": len(project.get("slots", [])),
}, indent=2))
