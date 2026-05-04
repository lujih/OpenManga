import os
import yaml
import click
import openai
from elevenlabs import ElevenLabs
from datetime import datetime, timezone
from pipeline.config import load_config
from pipeline.manifest import write_manifest


def _create_tts_client(cfg):
    provider = cfg.get("provider", "")
    api_base = cfg.get("api_base") or None
    if provider == "elevenlabs":
        return "elevenlabs", ElevenLabs(
            api_key=cfg["api_key"],
            base_url=api_base,
        )
    else:
        return "openai", openai.OpenAI(
            api_key=cfg["api_key"],
            base_url=api_base,
        )


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

    tts_cfg = cfg["tts"]
    params = tts_cfg.get("params", {})
    provider_kind, client = _create_tts_client(tts_cfg)

    output_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_voice.wav")

    started_at = datetime.now(timezone.utc)

    if provider_kind == "elevenlabs":
        voice_id = params.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
        output_format = params.get("output_format", "mp3_44100_128")
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format=output_format,
            text=brief["dialogue"],
            model_id=tts_cfg["model"],
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    else:
        voice = params.get("voice", "alloy")
        response_format = params.get("response_format", "mp3")
        response = client.audio.speech.create(
            model=tts_cfg["model"],
            voice=voice,
            input=brief["dialogue"],
            response_format=response_format,
        )
        response.stream_to_file(output_path)

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    write_manifest(
        project_dir, shot_id, "voice",
        status="success",
        input={"dialogue": brief["dialogue"], "emotion": brief.get("emotion")},
        output={"audio": output_path, "phoneme_alignment": None},
        model={"provider": tts_cfg["provider"], "model": tts_cfg["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )


if __name__ == "__main__":
    cli()
