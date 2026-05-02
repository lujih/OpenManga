import os
import yaml
import click
from openai import OpenAI
from datetime import datetime, timezone
from pipeline.config import load_config
from pipeline.manifest import write_manifest


ANGLE_PROMPTS = {
    "front": "front view, facing camera, neutral expression, white background, character reference sheet",
    "side": "side profile, looking left, white background, character reference sheet",
    "quarter": "three-quarter view, looking slightly left, white background, character reference sheet",
    "back": "back view, facing away, white background, character reference sheet",
}


@click.group()
def cli():
    pass


@cli.command()
@click.option("--name", required=True)
@click.option("--appearance", required=True)
@click.option("--angles", default="front,side,quarter,back")
@click.option("--output", required=True)
@click.option("--config", default="config.yaml")
def generate_character(name, appearance, angles, output, config):
    cfg = load_config(config)
    client = OpenAI(api_key=cfg["image_generation"]["api_key"])
    angle_list = [a.strip() for a in angles.split(",")]

    os.makedirs(output, exist_ok=True)
    started_at = datetime.now(timezone.utc)

    image_paths = {}
    for angle in angle_list:
        angle_desc = ANGLE_PROMPTS.get(angle, f"{angle} view")
        prompt = f"{appearance}, {angle_desc}, high quality"
        client.images.generate(
            model=cfg["image_generation"]["model"],
            prompt=prompt,
            n=1,
            size="1024x1024",
        )
        image_path = os.path.join(output, f"{angle}.png")
        image_paths[angle] = image_path

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    manifest = {
        "version": "1.0",
        "step": "character",
        "status": "success",
        "input": {"name": name, "appearance": appearance, "angles": angle_list},
        "output": {"images": image_paths},
        "model": {"provider": cfg["image_generation"]["provider"], "model": cfg["image_generation"]["model"]},
        "timing": {
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        "error": {"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    }
    manifest_path = os.path.join(output, "character.manifest.yaml")
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


@cli.command()
@click.option("--input-file", required=True)
@click.option("--config", default="config.yaml")
def generate_shot(input_file, config):
    cfg = load_config(config)

    with open(input_file) as f:
        brief = yaml.safe_load(f)

    client = OpenAI(api_key=cfg["image_generation"]["api_key"])

    prompt_parts = []
    if brief.get("character_ref"):
        prompt_parts.append("character matching reference image")
    if brief.get("scene_desc"):
        prompt_parts.append(brief["scene_desc"])
    if brief.get("camera"):
        prompt_parts.append(brief["camera"])
    if brief.get("style"):
        prompt_parts.append(brief["style"])
    prompt_parts.append("high quality, cinematic lighting")
    prompt = ", ".join(prompt_parts)

    shot_dir = os.path.dirname(input_file)
    shot_id = brief["shot_id"]
    output_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_keyframe.png")

    started_at = datetime.now(timezone.utc)

    client.images.generate(
        model=cfg["image_generation"]["model"],
        prompt=prompt,
        n=1,
        size="1024x1024",
    )

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    project_dir = os.path.dirname(shot_dir)
    write_manifest(
        project_dir, shot_id, "illustrate",
        status="success",
        input={
            "character": brief.get("character"),
            "character_ref": brief.get("character_ref"),
            "scene_desc": brief.get("scene_desc"),
            "camera": brief.get("camera"),
            "style": brief.get("style"),
        },
        output={"keyframe": output_path},
        model={"provider": cfg["image_generation"]["provider"], "model": cfg["image_generation"]["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )


if __name__ == "__main__":
    cli()
