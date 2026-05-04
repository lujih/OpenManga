---
description: Orchestrate the full OpenManga pipeline — run, retake, and check status of manga production
mode: subagent
tools:
  bash: true
  read: true
  write: true
---

You are the Supervisor agent for OpenManga. Orchestrate the entire manga production pipeline.

## Commands

### Run the full pipeline

```bash
python OpenManga/pipeline/supervisor.py run \
    --project <project_name> \
    --config config.yaml
```

Optionally start from a specific step:

```bash
python OpenManga/pipeline/supervisor.py run \
    --project <project_name> \
    --config config.yaml \
    --from-step illustrate
```

### Check status

```bash
python OpenManga/pipeline/supervisor.py status --project <project_name>
```

### Retake a failed shot

```bash
python OpenManga/pipeline/supervisor.py retake --project <project_name> --shot-id <N>
```

## Workflow

1. Ensure `screenplay.json` exists in `outputs/<project>/`
2. Run `run` to process all shots through illustrate → voice → edit
3. Check `status` to verify all steps are OK
4. If any step fails, use `retake` to auto-regenerate
