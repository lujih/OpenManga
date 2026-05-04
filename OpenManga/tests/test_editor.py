import os
import json
import yaml
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipeline.editor import cli


def test_generate_creates_edit_manifest(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)

    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    keyframe_path = os.path.join(shot_dir, "shot_01_keyframe.png")
    brief = {
        "shot_id": 1, "character": "\u4e3b\u89d2",
        "dialogue": "\u4f60\u597d\u3002", "emotion": "\u5e73\u9759",
        "scene_desc": "\u5ba4\u5185", "camera": "\u4e2d\u666f", "style": "\u5199\u5b9e",
        "motion": None, "ambient": None, "duration_sec": 3,
        "keyframe": keyframe_path,
    }
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with open(keyframe_path, "w") as f:
        f.write("fake image data")

    project_dir = str(tmp_path / "my_project")
    screenplay_path = os.path.join(project_dir, "screenplay.json")
    with open(screenplay_path, "w") as f:
        json.dump({
            "meta": {"title": "Test", "style": "\u5199\u5b9e", "total_duration_est": 10},
            "characters": {},
            "shots": [
                {"shot_id": 1, "dialogue": "\u4f60\u597d\u3002", "duration_sec": 3}
            ]
        }, f)

    mock_video = MagicMock()
    mock_video.duration = 3

    with patch("pipeline.editor.ImageClip") as mock_image_clip, \
         patch("pipeline.editor.CompositeVideoClip") as mock_composite, \
         patch("pipeline.editor.whisper.load_model") as mock_whisper:

        mock_image_clip.return_value = mock_video
        mock_composite.return_value = MagicMock()
        mock_whisper_model = MagicMock()
        mock_whisper_model.transcribe.return_value = {"segments": []}
        mock_whisper.return_value = mock_whisper_model

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--input-file", brief_path,
            "--screenplay", screenplay_path,
            "--output", os.path.join(shot_dir, "shot_01_final.mp4"),
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    manifest_path = os.path.join(shot_dir, "shot_01_edit.manifest.yaml")
    assert os.path.exists(manifest_path)


def test_editor_reads_params_from_config(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)

    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    keyframe_path = os.path.join(shot_dir, "shot_01_keyframe.png")
    brief = {"shot_id": 1, "character": "主角", "dialogue": "你好。", "emotion": "平静",
             "scene_desc": "室内", "camera": "中景", "style": "写实",
             "motion": None, "ambient": None, "duration_sec": 3, "keyframe": keyframe_path}
    with open(brief_path, "w") as f:
        yaml.dump(brief, f, allow_unicode=True)

    with open(keyframe_path, "w") as f:
        f.write("fake image data")

    project_dir = str(tmp_path / "my_project")
    screenplay_path = os.path.join(project_dir, "screenplay.json")
    with open(screenplay_path, "w") as f:
        json.dump({"meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
                    "characters": {}, "shots": [{"shot_id": 1, "dialogue": "你好。", "duration_sec": 3}]}, f)

    mock_video = MagicMock()
    mock_video.duration = 3

    with patch("pipeline.editor.ImageClip") as mock_image_clip, \
         patch("pipeline.editor.CompositeVideoClip") as mock_composite, \
         patch("pipeline.editor.whisper.load_model") as mock_whisper:
        mock_image_clip.return_value = mock_video
        mock_composite.return_value = MagicMock()
        mock_whisper_model = MagicMock()
        mock_whisper_model.transcribe.return_value = {"segments": []}
        mock_whisper.return_value = mock_whisper_model

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate", "--input-file", brief_path,
            "--screenplay", screenplay_path,
            "--output", os.path.join(shot_dir, "shot_01_final.mp4"),
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    manifest_path = os.path.join(shot_dir, "shot_01_edit.manifest.yaml")
    assert os.path.exists(manifest_path)
