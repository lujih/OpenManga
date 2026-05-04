import pytest


@pytest.fixture
def sample_config_path(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
image_generation:
  provider: "openai"
  model: "gpt-image-2"
  api_key: "test-img-key"

tts:
  provider: "elevenlabs"
  model: "eleven_turbo_v2"
  api_key: "test-tts-key"

llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key: "test-llm-key"
""")
    return str(config_file)


@pytest.fixture
def sample_project_dir(tmp_path):
    project_dir = tmp_path / "outputs" / "my_project"
    project_dir.mkdir(parents=True)
    return str(project_dir)
