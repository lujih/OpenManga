import os
import json
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


def test_app_loads():
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception


def test_dashboard_requires_project():
    at = AppTest.from_file("pages/03_dashboard.py")
    at.run()
    assert at.exception


def test_dashboard_shows_screenplay_warning(tmp_path):
    project_dir = os.path.join("outputs", "test_proj")
    screenplay_path = os.path.join(project_dir, "screenplay.json")
    if os.path.exists(screenplay_path):
        os.remove(screenplay_path)

    at = AppTest.from_file("pages/03_dashboard.py")
    at.session_state["project"] = "test_proj"
    at.run()
    assert not at.exception
    assert any(
        "剧本" in w.value or "screenplay" in w.value.lower()
        for w in at.warning
    )


def test_dashboard_loads_with_screenplay(tmp_path):
    project_dir = os.path.join("outputs", "test_proj")
    os.makedirs(os.path.join(project_dir, "shot_01"), exist_ok=True)
    screenplay = {
        "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
        "characters": {},
        "shots": [{"shot_id": 1, "character": None, "dialogue": None, "emotion": None,
                    "scene_desc": "内景", "camera": "中景", "motion": None, "ambient": None,
                    "duration_sec": 3, "transition": "硬切"}]
    }
    os.makedirs(project_dir, exist_ok=True)
    with open(os.path.join(project_dir, "screenplay.json"), "w") as f:
        json.dump(screenplay, f)

    at = AppTest.from_file("pages/03_dashboard.py")
    at.session_state["project"] = "test_proj"
    at.run()
    assert not at.exception
