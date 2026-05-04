import os
import yaml
from pipeline.manifest import write_manifest, read_manifest, manifest_exists, manifest_path, get_manifest_status


def test_write_and_read_manifest(tmp_path):
    project_dir = str(tmp_path / "my_project")
    write_manifest(project_dir, 1, "illustrate",
        status="success",
        input={"character": "男主"},
        output={"keyframe": "keyframe.png"},
        model={"provider": "openai", "model": "gpt-image-2"},
        timing={"started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:10Z", "duration_sec": 10},
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None}
    )
    path = manifest_path(project_dir, 1, "illustrate")
    assert os.path.exists(path)

    data = read_manifest(path)
    assert data["version"] == "1.0"
    assert data["step"] == "illustrate"
    assert data["shot_id"] == 1
    assert data["status"] == "success"
    assert data["output"]["keyframe"] == "keyframe.png"


def test_manifest_exists(tmp_path):
    project_dir = str(tmp_path / "my_project")
    assert not manifest_exists(project_dir, 1, "illustrate")
    write_manifest(project_dir, 1, "illustrate", status="success")
    assert manifest_exists(project_dir, 1, "illustrate")


def test_manifest_path_format():
    path = manifest_path("/some/project", 3, "animate")
    assert path.endswith("shot_03/shot_03_animate.manifest.yaml")


def test_manifest_path_two_digit_zero_padding():
    path = manifest_path("/some/project", 1, "voice")
    assert "shot_01" in path
    assert "shot_01_voice.manifest.yaml" in path


def test_manifest_defaults_to_success(tmp_path):
    project_dir = str(tmp_path / "my_project")
    write_manifest(project_dir, 1, "test")
    data = read_manifest(manifest_path(project_dir, 1, "test"))
    assert data["status"] == "success"


def test_manifest_overrides_default(tmp_path):
    project_dir = str(tmp_path / "my_project")
    write_manifest(project_dir, 1, "test", status="failed",
        error={"type": "api_timeout", "message": "timeout", "retry_count": 1, "recoverable": True, "occurred_at": "2026-01-01T00:00:00Z"})
    data = read_manifest(manifest_path(project_dir, 1, "test"))
    assert data["status"] == "failed"
    assert data["error"]["type"] == "api_timeout"


def test_get_manifest_status(tmp_path):
    project_dir = str(tmp_path / "my_project")
    assert get_manifest_status(project_dir, 1, "illustrate") is None
    write_manifest(project_dir, 1, "illustrate", status="success")
    assert get_manifest_status(project_dir, 1, "illustrate") == "success"


def test_get_manifest_status_failed(tmp_path):
    project_dir = str(tmp_path / "my_project")
    write_manifest(project_dir, 1, "illustrate", status="failed")
    assert get_manifest_status(project_dir, 1, "illustrate") == "failed"


def test_manifest_creates_parent_dirs(tmp_path):
    project_dir = str(tmp_path / "deeply" / "nested" / "project")
    write_manifest(project_dir, 5, "voice", status="success")
    path = manifest_path(project_dir, 5, "voice")
    assert os.path.exists(path)
