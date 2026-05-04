import os
import pytest
from pipeline.config import load_config


def test_load_config_resolves_env_vars(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("image_generation:\n  api_key: \"${TEST_CONFIG_KEY}\"\n")
    os.environ["TEST_CONFIG_KEY"] = "secret123"
    try:
        config = load_config(str(config_file))
        assert config["image_generation"]["api_key"] == "secret123"
    finally:
        del os.environ["TEST_CONFIG_KEY"]


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")


def test_load_config_returns_dict(sample_config_path):
    config = load_config(sample_config_path)
    assert isinstance(config, dict)
    assert "image_generation" in config
    assert "tts" in config
    assert "llm" in config


def test_load_config_unset_env_var(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: \"${UNDEFINED_VAR}\"\n")
    config = load_config(str(config_file))
    assert config["key"] == ""
