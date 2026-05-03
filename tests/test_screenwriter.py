import json
import os
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipeline.screenwriter import cli


def test_generate_creates_screenplay_json(tmp_path, sample_config_path):
    output = str(tmp_path / "my_project" / "screenplay.json")

    fake_response = MagicMock()
    fake_response.content = [MagicMock()]
    fake_response.content[0].text = json.dumps({
        "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
        "characters": {},
        "shots": []
    }, ensure_ascii=False)

    with patch("pipeline.screenwriter.anthropic.Anthropic") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.messages.create.return_value = fake_response

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--idea", "一个测试故事",
            "--style", "写实",
            "--output", output,
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    assert os.path.exists(output)

    with open(output) as f:
        data = json.load(f)
    assert data["meta"]["title"] == "Test"

    manifest_path = os.path.join(os.path.dirname(output), "shot_00", "shot_00_screenplay.manifest.yaml")
    assert os.path.exists(manifest_path)


def test_generate_passes_idea_and_style_to_llm(tmp_path, sample_config_path):
    output = str(tmp_path / "my_project" / "screenplay.json")

    fake_response = MagicMock()
    fake_response.content = [MagicMock()]
    fake_response.content[0].text = json.dumps({
        "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
        "characters": {},
        "shots": []
    })

    with patch("pipeline.screenwriter.anthropic.Anthropic") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.messages.create.return_value = fake_response

        runner = CliRunner()
        runner.invoke(cli, [
            "generate",
            "--idea", "一个雨天故事",
            "--style", "电影感",
            "--output", output,
            "--config", sample_config_path,
        ])

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        prompt_text = messages[0]["content"]
        assert "雨天故事" in prompt_text
        assert "电影感" in prompt_text


def test_generate_uses_openai_when_provider_is_not_anthropic(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
llm:
  provider: "openai"
  model: "gpt-4o"
  api_key: "test-key"
  params:
    max_tokens: 4096
""")
    output = str(tmp_path / "my_project" / "screenplay.json")

    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = json.dumps({
        "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
        "characters": {},
        "shots": []
    }, ensure_ascii=False)

    with patch("pipeline.screenwriter.openai.OpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.chat.completions.create.return_value = fake_response

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--idea", "test",
            "--style", "写实",
            "--output", output,
            "--config", str(config_file),
        ])

    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(output), "shot_00", "shot_00_screenplay.manifest.yaml"))


def test_generate_reads_max_tokens_from_params(tmp_path, sample_config_path):
    output = str(tmp_path / "my_project" / "screenplay.json")

    fake_response = MagicMock()
    fake_response.content = [MagicMock()]
    fake_response.content[0].text = json.dumps({
        "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
        "characters": {},
        "shots": []
    })

    with patch("pipeline.screenwriter.anthropic.Anthropic") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.messages.create.return_value = fake_response

        runner = CliRunner()
        runner.invoke(cli, [
            "generate",
            "--idea", "test", "--style", "写实",
            "--output", output,
            "--config", sample_config_path,
        ])

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["max_tokens"] == 4096
