import os
import yaml
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipeline.voice import cli


def test_generate_creates_voice_manifest(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {
        "shot_id": 1, "character": "主角",
        "dialogue": "你好。", "emotion": "平静",
        "scene_desc": "室内", "camera": "中景", "style": "写实",
        "motion": None, "ambient": None, "duration_sec": 3,
    }
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with patch("pipeline.voice.ElevenLabs") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.text_to_speech.convert.return_value = [b"fake audio data"]

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--input-file", brief_path,
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    manifest_path = os.path.join(shot_dir, "shot_01_voice.manifest.yaml")
    assert os.path.exists(manifest_path)


def test_generate_skips_when_dialogue_empty(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_02")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {
        "shot_id": 2, "character": None,
        "dialogue": None, "emotion": None,
        "scene_desc": "街道", "camera": "远景", "style": "写实",
        "motion": None, "ambient": None, "duration_sec": 2,
    }
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    runner = CliRunner()
    result = runner.invoke(cli, [
        "generate",
        "--input-file", brief_path,
        "--config", sample_config_path,
    ])

    assert result.exit_code == 0
    manifest_path = os.path.join(shot_dir, "shot_02_voice.manifest.yaml")
    assert os.path.exists(manifest_path)
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)
    assert manifest["status"] == "skipped"


def test_generate_reads_voice_id_from_params(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {"shot_id": 1, "character": "主角", "dialogue": "你好。", "emotion": "平静",
             "scene_desc": "室内", "camera": "中景", "style": "写实",
             "motion": None, "ambient": None, "duration_sec": 3}
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with patch("pipeline.voice.ElevenLabs") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.text_to_speech.convert.return_value = [b"fake audio data"]
        runner = CliRunner()
        runner.invoke(cli, ["generate", "--input-file", brief_path, "--config", sample_config_path])
        call_kwargs = mock_client.text_to_speech.convert.call_args.kwargs
        assert call_kwargs["voice_id"] == "JBFqnCBsd6RMkjVDRZzb"


def test_generate_reads_output_format_from_params(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {"shot_id": 1, "character": "主角", "dialogue": "你好。", "emotion": "平静",
             "scene_desc": "室内", "camera": "中景", "style": "写实",
             "motion": None, "ambient": None, "duration_sec": 3}
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with patch("pipeline.voice.ElevenLabs") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.text_to_speech.convert.return_value = [b"fake audio data"]
        runner = CliRunner()
        runner.invoke(cli, ["generate", "--input-file", brief_path, "--config", sample_config_path])
        call_kwargs = mock_client.text_to_speech.convert.call_args.kwargs
        assert call_kwargs["output_format"] == "mp3_44100_128"


def test_generate_uses_openai_tts(tmp_path):
    import json as _json
    config_dir = str(tmp_path / "cfg")
    os.makedirs(config_dir)
    config_path = os.path.join(config_dir, "config.yaml")
    with open(config_path, "w") as f:
        f.write("tts:\n  provider: openai\n  model: tts-1\n  api_key: test-key\n  api_base: \"\"\n  params:\n    voice: alloy\n    response_format: mp3\n")

    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {"shot_id": 1, "character": "主角", "dialogue": "你好。",
             "scene_desc": "室内", "camera": "中景", "style": "写实",
             "motion": None, "ambient": None, "duration_sec": 3, "emotion": "平静"}
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with patch("pipeline.voice.openai.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--input-file", brief_path, "--config", config_path])
        assert result.exit_code == 0
        assert mock_client.audio.speech.create.called
