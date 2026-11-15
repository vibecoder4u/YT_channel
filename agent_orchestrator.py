#!/usr/bin/env python3
"""Dependency-aware multi-agent runner for the animation production pipeline.

Workers exchange versioned JSON artifacts through one atomic job manifest.
Ready agents run concurrently; dependencies cannot start before successful completion.
The model provider is pluggable through role-specific command line workers.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, os, shlex, subprocess, time, uuid, hashlib, threading
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1
ROLES = ("director", "shots", "characters", "assets", "camera", "animation", "quality", "composer")

@dataclass(frozen=True)
class Task:
    id: str
    role: str
    needs: tuple[str, ...] = ()

PIPELINE = (
    Task("director", "director"),
    Task("shots", "shots", ("director",)),
    Task("characters", "characters", ("shots",)),
    Task("assets", "assets", ("shots",)),
    Task("camera", "camera", ("shots",)),
    Task("animation", "animation", ("characters", "assets", "camera")),
    Task("quality", "quality", ("animation",)),
    Task("composer", "composer", ("quality",)),
)

class Manifest:
    """Thread-safe shared state persisted atomically after every task transition."""
    def __init__(self, path: Path, job_id: str, script: str):
        self.path, self.lock = path, threading.RLock()
        self.data = {"schema_version": SCHEMA_VERSION, "job_id": job_id,
                     "created_at": time.time(), "script": script,
                     "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
                     "status": "running", "tasks": {}, "events": []}
        self._save()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def event(self, task_id: str, status: str, **extra):
        with self.lock:
            self.data["tasks"].setdefault(task_id, {}).update(
                status=status, updated_at=time.time(), **extra)
            self.data["events"].append({"task": task_id, "status": status,
                                        "at": time.time(), **extra})
            self._save()

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.data))

class CommandAgent:
    """Worker contract: COMMAND --input context.json --output result.json."""
    def __init__(self, role: str, command: str, timeout: int = 1800):
        self.role, self.command, self.timeout = role, command, timeout

    def run(self, context_path: Path, output_path: Path) -> dict:
        argv = shlex.split(self.command) + ["--input", str(context_path), "--output", str(output_path)]
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=self.timeout)
        if proc.returncode:
            raise RuntimeError(f"{self.role} worker exited {proc.returncode}: {proc.stderr[-4000:]}")
        if not output_path.is_file():
            raise RuntimeError(f"{self.role} worker did not create its result file")
        result = json.loads(output_path.read_text(encoding="utf-8"))
        if not isinstance(result, dict) or result.get("status") != "ok":
            raise RuntimeError(f"{self.role} returned an invalid result contract")
        return result

class DemoAgent:
    """Scheduler test double only; it does not create artwork or animation."""
    def __init__(self, role: str):
        self.role = role

    def run(self, context_path: Path, output_path: Path) -> dict:
        ctx = json.loads(context_path.read_text(encoding="utf-8"))
        result = {"status": "ok", "agent": self.role, "job_id": ctx["job_id"],
                  "script_sha256": ctx["script_sha256"],
                  "consumed": sorted(ctx["dependencies"]),
                  "note": "scheduler-contract-demo-only"}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

class Orchestrator:
    def __init__(self, workdir: Path, agents: dict, workers: int = 4, retries: int = 1):
        self.workdir, self.agents = workdir, agents
        self.workers, self.retries = max(1, workers), max(0, retries)

    def run(self, script: str) -> dict:
        missing = sorted({t.role for t in PIPELINE} - set(self.agents))
        if missing:
            raise ValueError("No worker configured for roles: " + ", ".join(missing))
        job_id = uuid.uuid4().hex[:12]
        job_dir = self.workdir / job_id
        manifest = Manifest(job_dir / "job_manifest.json", job_id, script)
        digest = hashlib.sha256(script.encode()).hexdigest()
        pending, completed, failed, running = {t.id:t for t in PIPELINE}, set(), {}, {}

        def execute(task: Task):
            snap = manifest.snapshot()
            deps = {}
            for dep in task.needs:
                rec = snap["tasks"].get(dep, {})
                if rec.get("status") != "succeeded":
                    raise RuntimeError(f"Dependency {dep} is not successful")
                deps[dep] = rec["result"]
            context = {"schema_version":SCHEMA_VERSION, "job_id":job_id,
                       "task_id":task.id, "role":task.role, "script":script,
                       "script_sha256":digest, "dependencies":deps,
                       "shared_manifest":str(job_dir / "job_manifest.json")}
            ctx_path = job_dir / "contexts" / f"{task.id}.json"
            out_path = job_dir / "results" / f"{task.id}.json"
            ctx_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            ctx_path.write_text(json.dumps(context, indent=2), encoding="utf-8")
            last_error = None
            for attempt in range(self.retries + 1):
                manifest.event(task.id, "running", role=task.role, attempt=attempt+1)
                try:
                    result = self.agents[task.role].run(ctx_path, out_path)
                    return result, str(out_path), attempt+1
                except Exception as exc:
                    last_error = str(exc)
                    manifest.event(task.id, "retrying" if attempt < self.retries else "failed",
                                   role=task.role, attempt=attempt+1, error=last_error)
            raise RuntimeError(last_error or "unknown worker error")

        with cf.ThreadPoolExecutor(max_workers=self.workers) as pool:
            while pending or running:
                ready = [t for t in pending.values() if set(t.needs) <= completed]
                while ready and len(running) < self.workers:
                    task = ready.pop(0)
                    pending.pop(task.id)
                    running[pool.submit(execute, task)] = task
                if not running:
                    if pending:
                        for task_id in pending:
                            failed[task_id] = "blocked by failed dependency"
                            manifest.event(task_id, "blocked", error=failed[task_id])
                        pending.clear()
                    continue
                done, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
                for future in done:
                    task = running.pop(future)
                    try:
                        result, artifact, attempts = future.result()
                        manifest.event(task.id, "succeeded", role=task.role, result=result,
                                       artifact=artifact, attempts=attempts)
                        completed.add(task.id)
                    except Exception as exc:
                        failed[task.id] = str(exc)
                        manifest.event(task.id, "failed", role=task.role, error=str(exc))
        status = "succeeded" if not failed and len(completed) == len(PIPELINE) else "failed"
        with manifest.lock:
            manifest.data["status"] = status
            manifest.data["finished_at"] = time.time()
            manifest.data["failed"] = failed
            manifest._save()
        return manifest.snapshot()

def main():
    ap = argparse.ArgumentParser(description="Run synchronized animation production agents")
    ap.add_argument("--script", help="Path to user-provided script (passed through unchanged)")
    ap.add_argument("--workdir", default="output/agent_jobs")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--demo", action="store_true", help="Test scheduling only; no animation is generated")
    ap.add_argument("--agent-command", action="append", default=[], metavar="ROLE=COMMAND")
    args = ap.parse_args()
    if args.demo:
        script = "DEMO ONLY: unchanged sample input for scheduler validation."
        agents = {role:DemoAgent(role) for role in ROLES}
    else:
        if not args.script:
            ap.error("--script is required unless --demo is used")
        script = Path(args.script).read_text(encoding="utf-8")
        agents = {}
        for item in args.agent_command:
            if "=" not in item:
                ap.error("--agent-command must be ROLE=COMMAND")
            role, command = item.split("=", 1)
            if role not in ROLES:
                ap.error(f"Unknown role {role!r}")
            agents[role] = CommandAgent(role, command)
    result = Orchestrator(Path(args.workdir), agents, args.workers, args.retries).run(script)
    print(json.dumps({k:result[k] for k in ("job_id","status","tasks","failed")}, indent=2))
    if result["status"] != "succeeded":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
