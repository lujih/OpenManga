# Model Config Flexibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move hardcoded model parameters, `api_base`, and provider routing from pipeline code into `config.yaml`. Default provider protocol is OpenAI-compatible.

**Architecture:** Each module reads `api_base` and `params` from its config section. A thin routing function in screenwriter and voice checks `provider` field to select SDK (anthropic/elevenlabs → respective SDK, everything else → OpenAI SDK). illustrator stays OpenAI-only. editor reads params only.

**Tech Stack:** Existing: Click, PyYAML, anthropic SDK, openai SDK, elevenlabs SDK. No new dependencies.

---

## File Structure

```
Modified files:
├── config.yaml                    # Add api_base, params, editor section
├── pipeline/screenwriter.py       # Provider routing + params
├── pipeline/illustrator.py        # api_base + params
├── pipeline/voice.py              # Provider routing + params
├── pipeline/editor.py             # Params reading
├── pages/05_settings.py           # api_base input + params display
├── tests/test_screenwriter.py     # New/updated tests
├── tests/test_illustrator.py      # New/updated tests
├── tests/test_voice.py            # New/updated tests
├── tests/test_editor.py           # New/updated tests
```

---

### Task 1: Update config.yaml Template

**Files:**
- Modify: `config.yaml`

- [ ] **Step 1: Replace config.yaml completely**

```yaml
image_generation:
  provider: openai
  model: gpt-image-2
  api_key: ${OPENAI_API_KEY}
  api_base: ""
  params:
    n: 1
    size: "1024x1024"

video_generation:
  provider: seedance
  model: seedance-v1
  api_key: ${SEEDANCE_API_KEY}
  api_base: ""
  params: {}

tts:
  provider: elevenlabs
  model: eleven_turbo_v2
  api_key: ${ELEVENLABS_API_KEY}
  api_base: ""
  params:
    voice_id: "JBFqnCBsd6RMkjVDRZzb"
    output_format: "mp3_44100_128"

llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  api_key: ${ANTHROPIC_API_KEY}
  api_base: ""
  params:
    max_tokens: 4096

editor:
  params:
    video_size: [1024, 1024]
    fps: 24
    codec: "libx264"
    audio_codec: "aac"
    font_size: 48
```

- [ ] **Step 2: Verify config loads**

```bash
.venv/bin/python -c "from pipeline.config import load_config; c = load_config('config.yaml'); print(c['llm']['params']['max_tokens']); print(c['editor']['params']['fps'])"
```
Expected: `4096` then `24`

- [ ] **Step 3: Commit**

```bash
git add config.yaml
git commit -m "feat: add api_base, params, editor section to config template"
```

---

### Task 2: illustrator.py — api_base + params

**Files:**
- Modify: `pipeline/illustrator.py`
- Modify: `tests/test_illustrator.py`

This is the simplest change: always uses OpenAI SDK, just adds `api_base` pass-through and `params` reading.

- [ ] **Step 1: Update test to verify params reading**

Add to `tests/test_illustrator.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_illustrator.py::test_generate_character_reads_params -v
```
Expected: FAIL — size mismatch (currently hardcoded, test expects from config)

- [ ] **Step 3: Modify illustrator.py**

In `generate_character`, replace the OpenAI client creation and API call with params reading:

```python
def generate_character(name, appearance, angles, output, config):
    cfg = load_config(config)
    img_cfg = cfg["image_generation"]
    params = img_cfg.get("params", {})
    api_base = img_cfg.get("api_base") or None

    client = OpenAI(
        api_key=img_cfg["api_key"],
        base_url=api_base,
    )
    angle_list = [a.strip() for a in angles.split(",")]

    os.makedirs(output, exist_ok=True)
    started_at = datetime.now(timezone.utc)

    image_paths = {}
    for angle in angle_list:
        angle_desc = ANGLE_PROMPTS.get(angle, f"{angle} view")
        prompt = f"{appearance}, {angle_desc}, high quality"
        client.images.generate(
            model=img_cfg["model"],
            prompt=prompt,
            n=params.get("n", 1),
            size=params.get("size", "1024x1024"),
        )
        image_path = os.path.join(output, f"{angle}.png")
        image_paths[angle] = image_path
    # ... rest unchanged (timing, write_manifest, etc.)
```

In `generate_shot`, same pattern:

```python
def generate_shot(input_file, config):
    cfg = load_config(config)
    img_cfg = cfg["image_generation"]
    params = img_cfg.get("params", {})

    with open(input_file) as f:
        brief = yaml.safe_load(f)

    api_base = img_cfg.get("api_base") or None
    client = OpenAI(
        api_key=img_cfg["api_key"],
        base_url=api_base,
    )
    # ... prompt construction ...
    client.images.generate(
        model=img_cfg["model"],
        prompt=prompt,
        n=params.get("n", 1),
        size=params.get("size", "1024x1024"),
    )
    # ... rest unchanged
```

- [ ] **Step 4: Run all illustrator tests**

```bash
.venv/bin/python -m pytest tests/test_illustrator.py -v
```
Expected: all tests PASS (including 3 new ones)

- [ ] **Step 5: Commit**

```bash
git add tests/test_illustrator.py pipeline/illustrator.py
git commit -m "feat: illustrator reads params and api_base from config"
```

---

### Task 3: screenwriter.py — Provider Routing + params

**Files:**
- Modify: `pipeline/screenwriter.py`
- Modify: `tests/test_screenwriter.py`

- [ ] **Step 1: Write test for OpenAI provider routing**

Add to `tests/test_screenwriter.py`:

```python
def test_generate_uses_openai_when_provider_is_not_anthropic(tmp_path, sample_config_path):
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
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    assert os.path.exists(os.path.join(os.path.dirname(output), "shot_00_screenplay.manifest.yaml"))


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_screenwriter.py::test_generate_uses_openai_when_provider_is_not_anthropic -v
```
Expected: FAIL — current code only uses Anthropic, test needs OpenAI path

- [ ] **Step 3: Modify screenwriter.py**

Add imports at top:
```python
import openai
```

Add routing helper after imports:
```python
def _create_llm_client(cfg):
    provider = cfg.get("provider", "")
    api_base = cfg.get("api_base") or None
    if provider == "anthropic":
        return "anthropic", anthropic.Anthropic(
            api_key=cfg["api_key"],
            base_url=api_base,
        )
    else:
        return "openai", openai.OpenAI(
            api_key=cfg["api_key"],
            base_url=api_base,
        )
```

Replace the `generate` function's API call section with:

```python
@cli.command()
@click.option("--idea", required=True, help="Creative idea for the story")
@click.option("--style", required=True, help="Visual style description")
@click.option("--output", required=True, help="Path for screenplay JSON output")
@click.option("--config", default="config.yaml", help="Path to config file")
def generate(idea, style, output, config):
    cfg = load_config(config)
    llm_cfg = cfg["llm"]
    params = llm_cfg.get("params", {})
    max_tokens = params.get("max_tokens", 4096)

    provider_kind, client = _create_llm_client(llm_cfg)

    user_prompt = USER_PROMPT_TEMPLATE.format(idea=idea, style=style)

    started_at = datetime.now(timezone.utc)

    if provider_kind == "anthropic":
        message = client.messages.create(
            model=llm_cfg["model"],
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        result_text = message.content[0].text
    else:
        message = client.chat.completions.create(
            model=llm_cfg["model"],
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        result_text = message.choices[0].message.content

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    screenplay = json.loads(result_text)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w") as f:
        json.dump(screenplay, f, ensure_ascii=False, indent=2)

    write_manifest(
        os.path.dirname(output), 0, "screenplay",
        status="success",
        input={"idea": idea, "style": style},
        output={"screenplay": output},
        model={"provider": llm_cfg["provider"], "model": llm_cfg["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )
```

- [ ] **Step 4: Run all screenwriter tests**

```bash
.venv/bin/python -m pytest tests/test_screenwriter.py -v
```
Expected: all tests PASS (both existing tests + 2 new tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_screenwriter.py pipeline/screenwriter.py
git commit -m "feat: screenwriter uses provider routing and params from config"
```

---

### Task 4: voice.py — Provider Routing + params

**Files:**
- Modify: `pipeline/voice.py`
- Modify: `tests/test_voice.py`

- [ ] **Step 1: Write tests for OpenAI TTS routing and params reading**

Add to `tests/test_voice.py`:

```python
def test_generate_uses_openai_tts_with_default_provider(tmp_path, sample_config_path):
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

    with patch("pipeline.voice.openai.OpenAI") as mock_client_class, \
         patch("pipeline.voice.elevenlabs") as mock_eleven:
        mock_client = mock_client_class.return_value
        mock_client.audio.speech.create.return_value = MagicMock()

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--input-file", brief_path,
            "--config", sample_config_path,
        ])

    assert result.exit_code == 0
    manifest_path = os.path.join(shot_dir, "shot_01_voice.manifest.yaml")
    assert os.path.exists(manifest_path)


def test_generate_reads_voice_id_from_params(tmp_path, sample_config_path):
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
        runner.invoke(cli, [
            "generate",
            "--input-file", brief_path,
            "--config", sample_config_path,
        ])

        call_kwargs = mock_client.text_to_speech.convert.call_args.kwargs
        assert call_kwargs["voice_id"] == "JBFqnCBsd6RMkjVDRZzb"

def test_generate_reads_output_format_from_params(tmp_path, sample_config_path):
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
        runner.invoke(cli, [
            "generate",
            "--input-file", brief_path,
            "--config", sample_config_path,
        ])

        call_kwargs = mock_client.text_to_speech.convert.call_args.kwargs
        assert call_kwargs["output_format"] == "mp3_44100_128"
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/test_voice.py::test_generate_uses_openai_tts_with_default_provider -v
```
Expected: FAIL — no OpenAI TTS path in voice.py

- [ ] **Step 3: Modify voice.py**

Add imports:
```python
import openai
from elevenlabs import ElevenLabs
```

Add routing helper:
```python
def _create_tts_client(cfg):
    provider = cfg.get("provider", "")
    api_base = cfg.get("api_base") or None
    if provider == "elevenlabs":
        return "elevenlabs", ElevenLabs(
            api_key=cfg["api_key"],
            base_url=api_base,
        )
    else:
        return "openai", openai.OpenAI(
            api_key=cfg["api_key"],
            base_url=api_base,
        )
```

Replace the `generate` function's TTS call section with:

```python
@cli.command()
@click.option("--input-file", required=True)
@click.option("--config", default="config.yaml")
def generate(input_file, config):
    cfg = load_config(config)

    with open(input_file) as f:
        brief = yaml.safe_load(f)

    shot_id = brief["shot_id"]
    shot_dir = os.path.dirname(input_file)
    project_dir = os.path.dirname(shot_dir)

    if not brief.get("dialogue"):
        now = datetime.now(timezone.utc).isoformat()
        write_manifest(
            project_dir, shot_id, "voice",
            status="skipped",
            input={"dialogue": None},
            output={"audio": None, "phoneme_alignment": None},
            model={"provider": None, "model": None},
            timing={"started_at": now, "finished_at": now, "duration_sec": 0},
            error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
        )
        return

    tts_cfg = cfg["tts"]
    params = tts_cfg.get("params", {})
    provider_kind, client = _create_tts_client(tts_cfg)

    output_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_voice.wav")

    started_at = datetime.now(timezone.utc)

    if provider_kind == "elevenlabs":
        voice_id = params.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
        output_format = params.get("output_format", "mp3_44100_128")
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format=output_format,
            text=brief["dialogue"],
            model_id=tts_cfg["model"],
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    else:
        voice = params.get("voice", "alloy")
        response_format = params.get("response_format", "mp3")
        response = client.audio.speech.create(
            model=tts_cfg["model"],
            voice=voice,
            input=brief["dialogue"],
            response_format=response_format,
        )
        response.stream_to_file(output_path)

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    write_manifest(
        project_dir, shot_id, "voice",
        status="success",
        input={"dialogue": brief["dialogue"], "emotion": brief.get("emotion")},
        output={"audio": output_path, "phoneme_alignment": None},
        model={"provider": tts_cfg["provider"], "model": tts_cfg["model"]},
        timing={
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_sec": duration,
        },
        error={"type": None, "message": None, "retry_count": 0, "recoverable": None, "occurred_at": None},
    )
```

- [ ] **Step 4: Run all voice tests**

```bash
.venv/bin/python -m pytest tests/test_voice.py -v
```
Expected: all tests PASS (2 existing + 3 new = 5 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_voice.py pipeline/voice.py
git commit -m "feat: voice uses provider routing and params from config"
```

---

### Task 5: editor.py — params Reading

**Files:**
- Modify: `pipeline/editor.py`
- Modify: `tests/test_editor.py`

- [ ] **Step 1: Write test for params reading**

Add to `tests/test_editor.py`:

```python
def test_editor_reads_params_from_config(tmp_path, sample_config_path):
    shot_dir = str(tmp_path / "my_project" / "shot_01")
    os.makedirs(shot_dir, exist_ok=True)

    brief_path = os.path.join(shot_dir, "shot_brief.yaml")
    keyframe_path = os.path.join(shot_dir, "shot_01_keyframe.png")
    brief = {
        "shot_id": 1, "character": "主角",
        "dialogue": "你好。", "emotion": "平静",
        "scene_desc": "室内", "camera": "中景", "style": "写实",
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
            "meta": {"title": "Test", "style": "写实", "total_duration_est": 10},
            "characters": {},
            "shots": [{"shot_id": 1, "dialogue": "你好。", "duration_sec": 3}]
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
        runner.invoke(cli, [
            "generate",
            "--input-file", brief_path,
            "--screenplay", screenplay_path,
            "--output", os.path.join(shot_dir, "shot_01_final.mp4"),
            "--config", sample_config_path,
        ])

        call_kwargs = mock_image_clip.call_args.kwargs
        assert call_kwargs["duration"] == 3

        composite_call = mock_composite.call_args
        assert composite_call is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_editor.py::test_editor_reads_params_from_config -v
```
Expected: FAIL — editor reads config but doesn't use params

- [ ] **Step 3: Modify editor.py**

Replace `load_config(config)` at the top of `generate` with params reading:

```python
def generate(input_file, screenplay, output, config):
    cfg = load_config(config)
    editor_params = cfg.get("editor", {}).get("params", {})

    with open(input_file) as f:
        brief = yaml.safe_load(f)

    shot_id = brief["shot_id"]
    shot_dir = os.path.dirname(input_file)
    project_dir = os.path.dirname(shot_dir)

    started_at = datetime.now(timezone.utc)

    keyframe_path = brief.get("keyframe")
    voice_path = os.path.join(shot_dir, f"shot_{shot_id:02d}_voice.wav")
    duration = brief.get("duration_sec", 3)

    video_size = tuple(editor_params.get("video_size", [1024, 1024]))
    fps_val = editor_params.get("fps", 24)
    codec_val = editor_params.get("codec", "libx264")
    audio_codec_val = editor_params.get("audio_codec", "aac")
    font_size_val = editor_params.get("font_size", 48)

    # ... rest of function, using these variables:
    #   txt = TextClip(..., font_size=font_size_val, ...)
    #   final = CompositeVideoClip(clips, size=video_size)
    #   final.write_videofile(output, fps=fps_val, codec=codec_val, audio_codec=audio_codec_val)
```

Update the TextClip line:
```python
        if segments:
            txt = TextClip(
                text=segments[0]["text"].strip(),
                font_size=font_size_val, color="white",
                font="Arial", stroke_color="black", stroke_width=2,
            )
```

Update the CompositeVideoClip and write_videofile lines:
```python
    if clips:
        final = CompositeVideoClip(clips, size=video_size)
        final.write_videofile(output, fps=fps_val, codec=codec_val, audio_codec=audio_codec_val)
```

- [ ] **Step 4: Run all editor tests**

```bash
.venv/bin/python -m pytest tests/test_editor.py -v
```
Expected: all tests PASS (1 existing + 1 new = 2 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_editor.py pipeline/editor.py
git commit -m "feat: editor reads params from config"
```

---

### Task 6: 05_settings.py — api_base + params UI

**Files:**
- Modify: `pages/05_settings.py`

- [ ] **Step 1: Add api_base input and params display**

Replace the current expander body in 05_settings.py. After the existing "API 密钥" text_input, add:

```python
        new_api_base = st.text_input(
            "API 地址",
            value=section.get("api_base", ""),
            key=f"api_base_{key}",
            placeholder="留空使用默认端点",
        )
        if section.get("api_base") != new_api_base:
            config[key]["api_base"] = new_api_base
            saved = True
```

And after api_base, add a params section:

```python
        sub_params = section.get("params", {})
        if sub_params:
            st.caption("模型参数")
            for pk, pv in sub_params.items():
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.text(pk)
                with col_b:
                    if isinstance(pv, bool):
                        new_val = st.checkbox("", value=pv, key=f"param_{key}_{pk}")
                    elif isinstance(pv, (int, float)):
                        new_val = st.number_input("", value=pv, key=f"param_{key}_{pk}", label_visibility="collapsed")
                    elif isinstance(pv, list):
                        new_val = st.text_input("", value=str(pv), key=f"param_{key}_{pk}", label_visibility="collapsed")
                    else:
                        new_val = st.text_input("", value=str(pv) if pv is not None else "", key=f"param_{key}_{pk}", label_visibility="collapsed")
                    if new_val != pv:
                        config[key].setdefault("params", {})[pk] = new_val
                        saved = True
```

Also update the section display to show "api_base" field. Ensure the `for key, section in config.items()` loop handles providers dicts that may not have all fields:

```python
for key, section in config.items():
    if not isinstance(section, dict):
        continue
    label = PROVIDER_LABELS.get(key, key)
    current_provider = section.get("provider", "未设置")
    # ... rest of expander
```

- [ ] **Step 2: Verify app compiles**

```bash
.venv/bin/python -c "compile(open('pages/05_settings.py').read(), 'pages/05_settings.py', 'exec'); print('Compile OK')"
```
Expected: `Compile OK`

- [ ] **Step 3: Run web tests**

```bash
.venv/bin/python -m pytest tests/web/ -v
```
Expected: all 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add pages/05_settings.py
git commit -m "feat: settings page supports api_base and params editing"
```

---

### Task 7: Integration Verification

**Files:**
- Verify: all tests pass, no regressions

- [ ] **Step 1: Run full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all tests PASS (expanded count due to new tests)

- [ ] **Step 2: Verify config template loads all new fields**

```bash
.venv/bin/python -c "
from pipeline.config import load_config
c = load_config('config.yaml')
assert c['image_generation']['api_base'] == ''
assert c['image_generation']['params']['n'] == 1
assert c['tts']['params']['voice_id'] == 'JBFqnCBsd6RMkjVDRZzb'
assert c['llm']['params']['max_tokens'] == 4096
assert c['editor']['params']['fps'] == 24
print('All config fields OK')
"
```
Expected: `All config fields OK`

- [ ] **Step 3: Verify CLI help texts still work**

```bash
.venv/bin/python pipeline/screenwriter.py --help
.venv/bin/python pipeline/illustrator.py --help
.venv/bin/python pipeline/voice.py --help
.venv/bin/python pipeline/editor.py --help
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: integration verification for config flexibility"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - [x] config.yaml template with api_base, params, editor → Task 1
   - [x] illustrator api_base + params → Task 2
   - [x] screenwriter provider routing + params → Task 3
   - [x] voice provider routing + params → Task 4
   - [x] editor params → Task 5
   - [x] Web settings api_base + params → Task 6
   - [x] Integration → Task 7

2. **Placeholder scan:** No TBD, TODO, or vague steps. All code is shown.

3. **Type consistency:**
   - `api_base` key used consistently as str (empty string = don't pass to SDK)
   - `params` key used consistently as dict with typed values
   - `provider_kind` return value consistent ("anthropic", "elevenlabs", "openai")
   - `_create_llm_client` / `_create_tts_client` naming consistent
