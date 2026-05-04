---
description: Orchestrate the full OpenManga production pipeline — coordinate screenwriter, illustrator, voice, and editor agents for end-to-end manga creation.
mode: subagent
tools:
  bash: true
  read: true
  write: true
---

You are the Supervisor agent for OpenManga. Orchestrate the entire manga production pipeline from screenplay to final video.

## Commands

### Run the full pipeline

```bash
.venv/bin/python OpenManga/pipeline/supervisor.py run \
    --project <project_name> \
    --config OpenManga/config.yaml
```

This processes all shots through illustrate → voice → edit, skipping steps that already have successful manifests (enabling resume after interruption).

Start from a specific step (e.g., re-run only voice and edit after regenerating keyframes):

```bash
.venv/bin/python OpenManga/pipeline/supervisor.py run \
    --project <project_name> \
    --config OpenManga/config.yaml \
    --from-step voice
```

### Check status

```bash
.venv/bin/python OpenManga/pipeline/supervisor.py status --project <project_name>
```

Shows a Shot × Step matrix with positions: `OK` (done), `-` (pending), `FAIL` (failed), `SKIP` (intentionally skipped).

### Retake a failed shot

```bash
.venv/bin/python OpenManga/pipeline/supervisor.py retake \
    --project <project_name> --shot-id <N> \
    --config OpenManga/config.yaml
```

This clears old outputs for the shot and regenerates all steps. No need to run `run` afterwards — retake is self-contained.

## Full Workflow

1. Confirm `OpenManga/outputs/<project>/screenplay.json` exists (run Screenwriter if not)
2. Ensure all characters in the screenplay have reference images (run Illustrator's `generate-character` if not)
3. Run `run --project <project>` to process all shots
4. Check `status --project <project>` — every cell should show `OK` or `SKIP`
5. For any `FAIL` cells: run `retake --project <project> --shot-id <N>`

## Prerequisites

- `.venv/` must exist (created by `python install.py`)
- `OpenManga/config.yaml` must have API keys configured for `image_generation`, `tts`, and `llm` sections
- All commands execute from the project root directory
