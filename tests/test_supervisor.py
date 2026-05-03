import os
import json
import yaml
from click.testing import CliRunner
from pipeline.supervisor import cli, prepare_shot


def test_prepare_shot_creates_shot_brief(tmp_path):
    project_dir = str(tmp_path / "my_project")
    shot = {
        "shot_id": 1, "character": "主角",
        "dialogue": "你好。", "emotion": "平静",
        "scene_desc": "安静的室内", "camera": "中景",
        "motion": None, "ambient": None,
        "duration_sec": 3, "transition": "硬切",
    }

    brief_path = prepare_shot(project_dir, shot, "写实")
    assert os.path.exists(brief_path)

    with open(brief_path) as f:
        brief = yaml.safe_load(f)
    assert brief["shot_id"] == 1
    assert brief["scene_desc"] == "安静的室内"
    assert brief["style"] == "写实"
    assert brief["character_ref"] is None


def test_prepare_shot_sets_character_ref_when_image_exists(tmp_path):
    project_dir = str(tmp_path / "my_project")
    char_dir = os.path.join("assets", "characters", "配角")
    os.makedirs(char_dir, exist_ok=True)
    with open(os.path.join(char_dir, "front.png"), "w") as f:
        f.write("fake")

    shot = {
        "shot_id": 1, "character": "配角",
        "dialogue": "你好。", "emotion": "平静",
        "scene_desc": "室内", "camera": "中景",
        "motion": None, "ambient": None,
        "duration_sec": 3, "transition": "硬切",
    }

    brief_path = prepare_shot(project_dir, shot, "写实")
    with open(brief_path) as f:
        brief = yaml.safe_load(f)
    assert brief["character_ref"] == os.path.join("assets", "characters", "配角", "front.png")


def test_status_shows_manifest_states(tmp_path, sample_config_path):
    project_dir = str(tmp_path / "my_project")
    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(project_dir, "screenplay.json"), "w") as f:
        json.dump({
            "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
            "characters": {},
            "shots": [
                {"shot_id": 1, "character": "主角", "dialogue": "你好", "emotion": "平静",
                 "scene_desc": "室内", "camera": "中景", "motion": None, "ambient": None,
                 "duration_sec": 3, "transition": "硬切"}
            ]
        }, f)

    from pipeline.manifest import write_manifest
    write_manifest(project_dir, 1, "illustrate", status="success",
        input={}, output={"keyframe": "test.png"},
        model={"provider": "openai", "model": "test"},
        timing={"started_at": "", "finished_at": "", "duration_sec": 0},
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None})

    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--project", project_dir])
    assert result.exit_code == 0
    assert "shot_01" in result.output
    assert "illustrate" in result.output


from unittest.mock import patch


def test_retake_also_regenerates(tmp_path, sample_config_path):
    project_dir = str(tmp_path / "my_project")
    screenplay_path = os.path.join(project_dir, "screenplay.json")

    os.makedirs(os.path.join(project_dir, "shot_01"), exist_ok=True)
    os.makedirs(project_dir, exist_ok=True)
    with open(screenplay_path, "w") as f:
        json.dump({
            "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
            "characters": {},
            "shots": [
                {"shot_id": 1, "character": None, "dialogue": None, "emotion": None,
                 "scene_desc": "室内", "camera": "中景", "motion": None, "ambient": None,
                 "duration_sec": 3, "transition": "硬切"}
            ]
        }, f)

    from pipeline.manifest import write_manifest
    write_manifest(project_dir, 1, "illustrate", status="success",
        input={}, output={"keyframe": "test.png"},
        model={"provider": "openai", "model": "test"},
        timing={"started_at": "", "finished_at": "", "duration_sec": 0},
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None})

    assert os.path.exists(os.path.join(project_dir, "shot_01", "shot_01_illustrate.manifest.yaml"))

    with patch("pipeline.supervisor.subprocess.run") as mock_run:
        runner = CliRunner()
        result = runner.invoke(cli, ["retake", "--project", project_dir, "--shot-id", 1])

    assert result.exit_code == 0
    assert not os.path.exists(os.path.join(project_dir, "shot_01", "shot_01_illustrate.manifest.yaml"))
    assert mock_run.called
