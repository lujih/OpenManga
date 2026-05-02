import os
import json
import yaml
import subprocess
import sys
import click
from pipeline.manifest import manifest_exists, get_manifest_status, read_manifest, manifest_path


STEPS = ["screenplay", "illustrate", "animate", "voice", "foley", "edit"]
PHASE1_STEPS = ["screenplay", "illustrate", "voice", "edit"]


def _python():
    return sys.executable


@click.group()
def cli():
    pass


def prepare_shot(project_dir: str, shot: dict, global_style: str) -> str:
    shot_id = shot["shot_id"]
    shot_dir = os.path.join(project_dir, f"shot_{shot_id:02d}")
    os.makedirs(shot_dir, exist_ok=True)

    character_ref = None
    if shot.get("character"):
        char_dir = os.path.join("assets", "characters", shot["character"])
        front_path = os.path.join(char_dir, "front.png")
        if os.path.exists(front_path):
            character_ref = front_path

    brief = {
        "shot_id": shot_id,
        "character": shot.get("character"),
        "character_ref": character_ref,
        "dialogue": shot.get("dialogue"),
        "emotion": shot.get("emotion"),
        "scene_desc": shot.get("scene_desc"),
        "camera": shot.get("camera"),
        "motion": shot.get("motion"),
        "ambient": shot.get("ambient"),
        "duration_sec": shot.get("duration_sec", 3),
        "style": global_style,
    }

    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    return brief_path


def update_brief_with_keyframe(brief_path: str, project_dir: str, shot_id: int):
    manifest = read_manifest(manifest_path(project_dir, shot_id, "illustrate"))
    with open(brief_path) as f:
        brief = yaml.safe_load(f)
    if manifest["status"] == "success" and manifest.get("output", {}).get("keyframe"):
        brief["keyframe"] = manifest["output"]["keyframe"]
        with open(brief_path, "w") as f:
            yaml.dump(brief, f, allow_unicode=True)


@cli.command()
@click.option("--project", required=True)
@click.option("--config", default="config.yaml")
@click.option("--from-step", default="screenplay")
def run(project, config, from_step):
    project_dir = os.path.join("outputs", project)
    screenplay_path = os.path.join(project_dir, "screenplay.json")

    if not os.path.exists(screenplay_path):
        click.echo(f"Error: {screenplay_path} not found. Run screenwriter first.")
        return

    with open(screenplay_path) as f:
        screenplay = json.load(f)

    global_style = screenplay["meta"]["style"]
    steps = PHASE1_STEPS

    if from_step not in steps:
        click.echo(f"Error: --from-step must be one of {steps}")
        return
    start_index = steps.index(from_step)

    for shot in screenplay["shots"]:
        shot_id = shot["shot_id"]
        brief_path = prepare_shot(project_dir, shot, global_style)

        for step in steps[start_index:]:
            if manifest_exists(project_dir, shot_id, step):
                status = get_manifest_status(project_dir, shot_id, step)
                if status == "success":
                    if step == "illustrate":
                        update_brief_with_keyframe(brief_path, project_dir, shot_id)
                    click.echo(f"  shot_{shot_id:02d}/{step}: already done (success)")
                    continue
                elif status in ("failed", "pending"):
                    click.echo(f"  shot_{shot_id:02d}/{step}: retrying (was {status})")

            click.echo(f"  shot_{shot_id:02d}/{step}: running...")

            if step == "illustrate":
                subprocess.run([
                    _python(), "pipeline/illustrator.py", "generate-shot",
                    "--input-file", brief_path, "--config", config,
                ], check=False)
                update_brief_with_keyframe(brief_path, project_dir, shot_id)

            elif step == "voice":
                subprocess.run([
                    _python(), "pipeline/voice.py", "generate",
                    "--input-file", brief_path, "--config", config,
                ], check=False)

            elif step == "edit":
                final_path = os.path.join(os.path.dirname(brief_path), f"shot_{shot_id:02d}_final.mp4")
                subprocess.run([
                    _python(), "pipeline/editor.py", "generate",
                    "--input-file", brief_path,
                    "--screenplay", screenplay_path,
                    "--output", final_path,
                    "--config", config,
                ], check=False)

    click.echo("Done.")


@cli.command()
@click.option("--project", required=True)
@click.option("--shot-id", required=True, type=int)
def retake(project, shot_id):
    project_dir = os.path.join("outputs", project)
    shot_dir = os.path.join(project_dir, f"shot_{shot_id:02d}")

    if not os.path.exists(shot_dir):
        click.echo(f"Error: {shot_dir} not found.")
        return

    for step in ["illustrate", "animate", "voice", "foley", "edit"]:
        mp = manifest_path(project_dir, shot_id, step)
        if os.path.exists(mp):
            manifest = read_manifest(mp)
            output = manifest.get("output", {})
            for filepath in output.values():
                if filepath and isinstance(filepath, str) and os.path.exists(filepath):
                    os.remove(filepath)
            os.remove(mp)

    click.echo(f"Cleared manifests and outputs for shot_{shot_id:02d}. Run 'run' to regenerate.")


@cli.command()
@click.option("--project", required=True)
def status(project):
    project_dir = project
    screenplay_path = os.path.join(project_dir, "screenplay.json")

    if not os.path.exists(screenplay_path):
        click.echo(f"No screenplay found at {screenplay_path}")
        return

    with open(screenplay_path) as f:
        screenplay = json.load(f)

    steps = PHASE1_STEPS
    col_width = 14

    header = ["Shot"] + steps
    click.echo(" | ".join(f"{h:<{col_width}}" for h in header))
    click.echo("-" * ((len(steps) + 1) * (col_width + 3)))

    for shot in screenplay["shots"]:
        shot_id = shot["shot_id"]
        row = [f"shot_{shot_id:02d}"]
        for step in steps:
            s = get_manifest_status(project_dir, shot_id, step)
            if s is None:
                row.append("-")
            elif s == "success":
                row.append("OK")
            elif s == "skipped":
                row.append("SKIP")
            elif s == "failed":
                row.append("FAIL")
            else:
                row.append(s)
        click.echo(" | ".join(f"{c:<{col_width}}" for c in row))


if __name__ == "__main__":
    cli()
