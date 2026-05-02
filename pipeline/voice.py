import os
import yaml
import click
from elevenlabs import ElevenLabs
from datetime import datetime, timezone
from pipeline.config import load_config
from pipeline.manifest import write_manifest


@click.group()
def cli():
    pass


@cli.command()
@click.option("--input-file", required=True)
@click.option("--config", default="config.yaml")
def generate(input_file, config):
    cfg = load_config(config)

    with open(input_file) as f:
        brief = yaml.safe_load(f)

    shot_id = brief["shot_id"]
    shot_dir = os.path.dirname(input_file)
    project_dir = os.path.dirname(shot_dir)

    if not brief.get("dialogue"):
        now = datetime.now(timezone.utc).isoformat()
        write_manifest(
            project_dir, shot_id, "voice",
            status="skipped",
            input={"dialogue": None},
            output={"audio": None, "phoneme_alignment": None},
            model={"provider": None, "model": None},
            timing={"started_at": now, "finished_at": now, "duration_sec": 0},
            error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
        )
        return

    client = ElevenLabs(api_key=cfg["tts"]["api_key"])

    output_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_voice.wav")

    started_at = datetime.now(timezone.utc)

    audio = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        output_format="mp3_44100_128",
        text=brief["dialogue"],
        model_id=cfg["tts"]["model"],
    )

    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    write_manifest(
        project_dir, shot_id, "voice",
        status="success",
        input={"dialogue": brief["dialogue"], "emotion": brief.get("emotion")},
        output={"audio": output_path, "phoneme_alignment": None},
        model={"provider": cfg["tts"]["provider"], "model": cfg["tts"]["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )


if __name__ == "__main__":
    cli()
