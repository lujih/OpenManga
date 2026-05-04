import os
import yaml


def manifest_path(project_dir: str, shot_id: int, step: str) -> str:
    return os.path.join(project_dir, f"shot_{shot_id:02d}", f"shot_{shot_id:02d}_{step}.manifest.yaml")


def write_manifest(project_dir: str, shot_id: int, step: str, **fields) -> str:
    path = manifest_path(project_dir, shot_id, step)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    defaults = {"version": "1.0", "step": step, "shot_id": shot_id, "status": "success"}
    manifest = {**defaults, **fields}
    with open(path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return path


def read_manifest(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def manifest_exists(project_dir: str, shot_id: int, step: str) -> bool:
    return os.path.exists(manifest_path(project_dir, shot_id, step))


def get_manifest_status(project_dir: str, shot_id: int, step: str) -> str | None:
    path = manifest_path(project_dir, shot_id, step)
    if not os.path.exists(path):
        return None
    return read_manifest(path).get("status")
