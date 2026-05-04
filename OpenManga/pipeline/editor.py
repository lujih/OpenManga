import os
import yaml
import json
import click
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
import whisper
from datetime import datetime, timezone
from pipeline.config import load_config
from pipeline.manifest import write_manifest


@click.group()
def cli():
    pass


@cli.command()
@click.option("--input-file", required=True)
@click.option("--screenplay", required=True)
@click.option("--output", required=True)
@click.option("--config", default="config.yaml")
def generate(input_file, screenplay, output, config):
    cfg = load_config(config)

    editor_params = cfg.get("editor", {}).get("params", {})
    video_size = tuple(editor_params.get("video_size", [1024, 1024]))
    fps_val = editor_params.get("fps", 24)
    codec_val = editor_params.get("codec", "libx264")
    audio_codec_val = editor_params.get("audio_codec", "aac")
    font_size_val = editor_params.get("font_size", 48)

    with open(input_file) as f:
        brief = yaml.safe_load(f)

    shot_id = brief["shot_id"]
    shot_dir = os.path.dirname(input_file)
    project_dir = os.path.dirname(shot_dir)

    started_at = datetime.now(timezone.utc)

    keyframe_path = brief.get("keyframe")
    voice_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_voice.wav")
    duration = brief.get("duration_sec", 3)

    clips = []

    if keyframe_path and os.path.exists(keyframe_path):
        image_clip = ImageClip(keyframe_path, duration=duration)
        clips.append(image_clip)

    subtitle_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_sub.srt")

    if os.path.exists(voice_path) and clips:
        audio_clip = AudioFileClip(voice_path)
        clips[0] = clips[0].with_audio(audio_clip)

        model = whisper.load_model("base")
        result = model.transcribe(voice_path)
        segments = result.get("segments", [])
        with open(subtitle_path, "w") as f:
            for i, seg in enumerate(segments):
                start = seg["start"]
                end = seg["end"]
                text = seg["text"].strip()
                f.write(f"{i+1}\n")
                f.write(f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n")
                f.write(f"{text}\n\n")

        if segments:
            txt = TextClip(
                text=segments[0]["text"].strip(),
                font_size=font_size_val, color="white",
                font="Arial", stroke_color="black", stroke_width=2,
            )
            txt = txt.with_position(("center", "center")).with_duration(duration)
            clips.append(txt)

    if clips:
        final = CompositeVideoClip(clips, size=video_size)
        final.write_videofile(output, fps=fps_val, codec=codec_val, audio_codec=audio_codec_val)
    else:
        with open(output, "w") as f:
            f.write("placeholder")

    finished_at = datetime.now(timezone.utc)
    elapsed = (finished_at - started_at).total_seconds()

    write_manifest(
        project_dir, shot_id, "edit",
        status="success",
        input={"keyframe": keyframe_path, "voice": voice_path},
        output={"final_shot": output, "subtitle": subtitle_path},
        model={"provider": "local", "model": "moviepy+whisper"},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": elapsed,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )


def _format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


if __name__ == "__main__":
    cli()
