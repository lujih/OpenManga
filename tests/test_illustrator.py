import os
import yaml
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipeline.illustrator import cli


def test_generate_character_creates_manifest(tmp_path, sample_config_path):
    output_dir = str(tmp_path / "characters" / "主角")

    with patch("pipeline.illustrator.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_image = MagicMock()
        mock_image.data = [MagicMock()]
        mock_image.data[0].url = "http://example.com/test.png"
        mock_client.images.generate.return_value = mock_image

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate-character",
            "--name", "主角",
            "--appearance", "年轻男子，黑色短发",
            "--angles", "front,side",
            "--output", output_dir,
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "character.manifest.yaml"))


def test_generate_character_calls_api_for_each_angle(tmp_path, sample_config_path):
    output_dir = str(tmp_path / "characters" / "主角")

    with patch("pipeline.illustrator.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_image = MagicMock()
        mock_image.data = [MagicMock()]
        mock_image.data[0].url = "http://example.com/test.png"
        mock_client.images.generate.return_value = mock_image

        runner = CliRunner()
        runner.invoke(cli, [
            "generate-character",
            "--name", "主角",
            "--appearance", "年轻男子",
            "--angles", "front,side,back",
            "--output", output_dir,
            "--config", sample_config_path,
        ])

        assert mock_client.images.generate.call_count == 3


def test_generate_shot_creates_manifest(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {
        "shot_id": 1, "character": "主角",
        "character_ref": "assets/characters/主角/standard.png",
        "scene_desc": "安静的室内", "camera": "中景",
        "style": "写实", "dialogue": "你好。", "emotion": "平静",
        "motion": None, "ambient": None, "duration_sec": 3,
    }
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with patch("pipeline.illustrator.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_image = MagicMock()
        mock_image.data = [MagicMock()]
        mock_image.data[0].url = "http://example.com/test.png"
        mock_client.images.generate.return_value = mock_image

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate-shot",
            "--input-file", brief_path,
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    manifest_path = os.path.join(shot_dir, "shot_01_illustrate.manifest.yaml")
    assert os.path.exists(manifest_path)


def test_generate_character_reads_params(tmp_path, sample_config_path):
    output_dir = str(tmp_path / "characters" / "主角")

    with patch("pipeline.illustrator.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_image = MagicMock()
        mock_image.data = [MagicMock()]
        mock_image.data[0].url = "http://example.com/test.png"
        mock_client.images.generate.return_value = mock_image

        runner = CliRunner()
        runner.invoke(cli, [
            "generate-character",
            "--name", "主角",
            "--appearance", "年轻男子",
            "--angles", "front",
            "--output", output_dir,
            "--config", sample_config_path,
        ])

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["n"] == 1
        assert call_kwargs["size"] == "1024x1024"


def test_generate_shot_reads_params(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)
    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    brief = {"shot_id": 1, "scene_desc": "test", "camera": "中景", "style": "写实"}
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with patch("pipeline.illustrator.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_image = MagicMock()
        mock_image.data = [MagicMock()]
        mock_image.data[0].url = "http://example.com/test.png"
        mock_client.images.generate.return_value = mock_image

        runner = CliRunner()
        runner.invoke(cli, [
            "generate-shot",
            "--input-file", brief_path,
            "--config", sample_config_path,
        ])

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["n"] == 1
        assert call_kwargs["size"] == "1024x1024"


def test_illustrator_passes_api_base(tmp_path, sample_config_path):
    output_dir = str(tmp_path / "characters" / "主角")

    with patch("pipeline.illustrator.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_image = MagicMock()
        mock_image.data = [MagicMock()]
        mock_image.data[0].url = "http://example.com/test.png"
        mock_client.images.generate.return_value = mock_image

        runner = CliRunner()
        runner.invoke(cli, [
            "generate-character",
            "--name", "主角",
            "--appearance", "young man",
            "--angles", "front",
            "--output", output_dir,
            "--config", sample_config_path,
        ])

        call_kwargs = mock_client_class.call_args.kwargs
        assert "api_key" in call_kwargs
