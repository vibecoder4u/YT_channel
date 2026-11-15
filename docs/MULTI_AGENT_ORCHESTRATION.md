# Synchronized multi-agent animation pipeline

This is the coordination layer for the animation engine, independent of any one renderer or model provider.

## Agent graph

- **Director** receives the user's script unchanged and produces a visual production brief.
- **Shot planner** converts that brief into timed shots and visual requirements.
- **Character factory** and **asset factory** work in parallel after the shot plan.
- **Camera director** works in parallel from the same shot plan.
- **Animation agent** waits for approved character, asset and camera outputs.
- **Quality agent** validates the animation output and can fail the job.
- **Composer** runs only after quality approval.

The scheduler is dependency-driven. Independent agents can work concurrently; dependent agents cannot start early. A failed branch blocks its dependents while independent branches can finish.

## Shared state

Each run writes output/agent_jobs/<job-id>/job_manifest.json. It records the original script and SHA-256, each task's status/role/attempts/timestamps/errors, successful result objects and artifact paths, plus an event history.

The manifest is updated atomically. Each worker receives an immutable context JSON with the same job ID, original script hash, dependency outputs and shared-manifest path. Results are written to separate task files to avoid agents overwriting each other.

## Worker interface

A worker is an executable command configured per role. The orchestrator invokes:

    WORKER --input CONTEXT.json --output RESULT.json

The worker must write a JSON object with status="ok". It should save its deliverables under the job directory and return their paths, versions and metadata. The command adapter supports Groq-powered Python workers, local open-source models, or deterministic tools without coupling the scheduler to a provider.

Example:

    python agent_orchestrator.py --script my_script.txt \
      --agent-command 'director=python agents/director.py' \
      --agent-command 'shots=python agents/shots.py' \
      --agent-command 'characters=python agents/characters.py' \
      --agent-command 'assets=python agents/assets.py' \
      --agent-command 'camera=python agents/camera.py' \
      --agent-command 'animation=python agents/animation.py' \
      --agent-command 'quality=python agents/quality.py' \
      --agent-command 'composer=python agents/composer.py'

All eight role workers must be configured. Missing workers fail fast; the system does not silently substitute demo workers.

## Verify

    python -m unittest discover -s tests -p 'test_agent_orchestrator.py' -v
    python agent_orchestrator.py --demo --workdir output/agent_jobs

The demo tests parallel scheduling, dependency handoff, manifest synchronization, failure propagation and script preservation. It is not a visual animation demo.

## Implementation boundary

The scheduler and worker contract are implemented. The role-specific production workers are integration points, not yet eight finished AI agents. The existing Rigby2D skeletal prototype remains a separate renderer lane. The next milestone is connecting real role workers to the pinned character rig, asset preparation, shot/camera planning and quality tools, then running a multi-character visual benchmark before calling the engine production-ready.
