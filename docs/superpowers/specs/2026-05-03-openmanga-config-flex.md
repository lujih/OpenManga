# OpenManga · 模型配置灵活化 — 系统设计

> **目标**  
> 将硬编码在 pipeline 模块中的模型参数、自定义 API 端点、Provider 路由逻辑全部提升到 `config.yaml` 可配置层。

---

## 1. 变更总览

| 变更 | 说明 |
|------|------|
| `params` 子节 | 每个 provider 节增加可选 `params:` 字典，存放模型参数（max_tokens、size、voice_id 等） |
| `api_base` 字段 | 每个 provider 节增加可选 `api_base:` 字段，支持自定义 API 端点（兼容 Ollama、DeepSeek 等） |
| Provider 路由 | `provider` 字段值决定使用哪个 SDK：`anthropic`→Anthropic SDK，`elevenlabs`→ElevenLabs SDK，其他→OpenAI SDK（默认） |

---

## 2. config.yaml 完整模板

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

**字段规则：**
- `api_base` 为空字符串时不传入 SDK，使用 SDK 默认端点
- `params` 缺失时模块使用代码内置默认值
- 用户可自由添加新 provider 节，Web 设置页面自动显示
- `${ENV_VAR}` 语法由 `config.py` 的 `os.path.expandvars` 解析

---

## 3. Provider 路由规则

```
provider 字段    →  SDK                    →  用于模块
──────────────     ────────────────────       ─────────
"anthropic"     →  anthropic.Anthropic    →  screenwriter.py
"elevenlabs"    →  elevenlabs.ElevenLabs  →  voice.py
其他/空/不填     →  openai.OpenAI (默认)    →  screenwriter / illustrator / voice
```

`openai.OpenAI` 为默认路由，覆盖 `deepseek`、`ollama`、`siliconflow` 等所有 OpenAI 协议兼容服务，通过 `api_base` 区分端点。

---

## 4. 各模块 API 适配

### 4.1 screenwriter.py — LLM

**当前**：只用 Anthropic SDK，`max_tokens=4096` 硬编码。

**改后**：

```python
def _create_llm_client(cfg):
    if cfg.get("provider") == "anthropic":
        return "anthropic", anthropic.Anthropic(
            api_key=cfg["api_key"],
            base_url=cfg.get("api_base") or None,
        )
    else:
        base_url = cfg.get("api_base") or None
        return "openai", openai.OpenAI(
            api_key=cfg["api_key"],
            base_url=base_url,
        )

# 调用端：
provider_kind, client = _create_llm_client(cfg["llm"])
params = cfg["llm"].get("params", {})
max_tokens = params.get("max_tokens", 4096)

if provider_kind == "anthropic":
    msg = client.messages.create(
        model=cfg["llm"]["model"],
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    result_text = msg.content[0].text
else:
    msg = client.chat.completions.create(
        model=cfg["llm"]["model"],
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    result_text = msg.choices[0].message.content
```

### 4.2 illustrator.py — 生图

**当前**：只用 OpenAI SDK，`n=1`、`size='1024x1024'` 硬编码。

**改后**：不涉及 provider 路由（图生始终用 OpenAI 协议）。只读取 params：

```python
params = cfg["image_generation"].get("params", {})
n = params.get("n", 1)
size = params.get("size", "1024x1024")

client = openai.OpenAI(
    api_key=cfg["image_generation"]["api_key"],
    base_url=cfg["image_generation"].get("api_base") or None,
)
response = client.images.generate(
    model=cfg["image_generation"]["model"],
    prompt=prompt,
    n=n,
    size=size,
)
```

### 4.3 voice.py — TTS

**当前**：只用 ElevenLabs SDK，`voice_id`、`output_format` 硬编码。

**改后**：

```python
def _create_tts_client(cfg):
    if cfg.get("provider") == "elevenlabs":
        return "elevenlabs", elevenlabs.ElevenLabs(
            api_key=cfg["api_key"],
            base_url=cfg.get("api_base") or None,
        )
    else:
        return "openai", openai.OpenAI(
            api_key=cfg["api_key"],
            base_url=cfg.get("api_base") or None,
        )

# 调用端：
provider_kind, client = _create_tts_client(cfg["tts"])
params = cfg["tts"].get("params", {})

if provider_kind == "elevenlabs":
    voice_id = params.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
    output_format = params.get("output_format", "mp3_44100_128")
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        output_format=output_format,
        text=brief["dialogue"],
        model_id=cfg["tts"]["model"],
    )
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
else:
    voice = params.get("voice", "alloy")
    response_format = params.get("response_format", "mp3")
    response = client.audio.speech.create(
        model=cfg["tts"]["model"],
        voice=voice,
        input=brief["dialogue"],
        response_format=response_format,
    )
    response.stream_to_file(output_path)
```

### 4.4 editor.py — 纯本地

不涉及 SDK 路由。从 `cfg["editor"].get("params", {})` 读取参数：

```python
params = cfg["editor"].get("params", {})
video_size = tuple(params.get("video_size", [1024, 1024]))
fps_val = params.get("fps", 24)
codec_val = params.get("codec", "libx264")
audio_codec_val = params.get("audio_codec", "aac")
font_size_val = params.get("font_size", 48)
```

---

## 5. Web 设置页联动

`pages/05_settings.py` 已在上一轮改为动态 provider。本轮新增：

- 每个 provider expander 中增加 `api_base` 输入框（标签："API 地址"）
- 每个 provider expander 中增加 `params` 动态表单（遍历 `params` 子字典自动生成输入框，支持任意 params key）

---

## 6. 测试策略

| 模块 | 新增测试 |
|------|---------|
| screenwriter | test: provider=openai 走 OpenAI SDK；provider=anthropic 走 Anthropic SDK；params.max_tokens 从配置读取 |
| illustrator | test: params.n / params.size 从配置读取 |
| voice | test: provider=openai 走 OpenAI TTS API；provider=elevenlabs 走 ElevenLabs；voice_id 从 params 读取 |
| editor | test: video_size / fps / font_size 从 params 读取 |
| config.yaml | test: api_base 为空时 SDK 不传 base_url 参数 |

---

## 7. 影响范围

| 文件 | 改动类型 |
|------|---------|
| `config.yaml` | 模板更新（加 api_base、params、editor 节） |
| `pipeline/screenwriter.py` | provider 路由 + params 读取 |
| `pipeline/illustrator.py` | api_base 支持 + params 读取 |
| `pipeline/voice.py` | provider 路由 + params 读取 |
| `pipeline/editor.py` | params 读取 |
| `pages/05_settings.py` | api_base 输入框 + params 动态表单 |
| 各模块测试文件 | 新增 / 修改现有测试 |
