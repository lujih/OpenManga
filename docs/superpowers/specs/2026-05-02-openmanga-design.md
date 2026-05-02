# OpenManga · 全AI生成式漫剧工厂 — 系统设计

> **一句话愿景**  
> 让一个人，只凭想法，就能创造出角色一致、视听完整的AI漫剧。

---

## 1. 项目概述

**OpenManga** 是一个基于 [OpenCode](https://github.com/opencode-ai/opencode) 多智能体平台构建的全自动漫剧生产管线。它以 **大语言模型（LLM）、文生图模型、视频生成模型、语音合成模型** 为核心引擎，将"创意 → 剧本 → 分镜 → 图像 → 动画 → 配音 → 合成"的完整流程，转化为多个专业化 AI 子代理的协同工作。

**核心特征**

- **全模型驱动**：不使用传统渲染引擎，一切视觉、听觉内容均由生成式 AI 模型产生。
- **角色一致性**：通过结构化资产库与参考图注入，在多个镜头中稳定保持同一角色的外貌。
- **OpenCode 基座**：利用 OpenCode 的子代理机制与插件系统，将复杂管线分解为可独立优化、可自由替换的智能体。
- **个人友好，持续进化**：单人或小团队即可运作，所有模块配置化、可插拔，跟随模型发展不断升级。

---

## 2. 技术架构

### 2.1 基座：OpenCode 多代理协调平台

```
用户 → OpenCode 主代理 (监制)
                │
    ┌───────────┼───────────┬───────────┬───────────┐
    ▼           ▼           ▼           ▼           ▼
  Task         Task         Task         Task        Task
    │           │           │           │           │
 编剧.md     画师.md     动效师.md    配音师.md   剪辑师.md
  (LLM)       (LLM)       (LLM)       (LLM)       (LLM)
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
screenwriter  illustrator  animator   voice.py    editor.py
   .py           .py          .py         │           │
    │           │           │           ▼           ▼
    ▼           ▼           ▼         foley.py   moviepy+ffmpeg
  剧本        关键帧      视频片段    环境音      合成导出
  JSON        +manifest   +manifest  +manifest
```

### 2.2 核心规则

1. **子代理** = `agents/*.md`（system prompt，声明 `tools: [bash, read, write]`）+ 通过 Bash 调用 `pipeline/*.py`（Click 子命令 CLI）
2. **状态传递** = 独立 manifest 文件（`shot_01_illustrate.manifest.yaml`），每步一文件
3. **统一入口** = 所有子代理只接受 `--input-file shot_brief.yaml`，上下文组装由监制负责
4. **模型配置** = `config.yaml` 按用途分类（`image_generation` / `video_generation` / `tts` / `llm`），用户填 provider
5. **错误恢复** = 监制检测失败 manifest → `--retake shot_03` 只清理该步骤的 manifest → 单步重跑

### 2.3 子代理职责表

| 子代理 | 职责 | 调用的工具脚本 | 主要模型 |
|--------|------|----------------|----------|
| 编剧 (Screenwriter) | 根据创意生成结构化剧本 JSON | `screenwriter.py` | LLM |
| 画师 (Illustrator) | 生成角色标准照、场景关键帧 | `illustrator.py` | Image Gen |
| 动效师 (Animator) | 将关键帧转化为动态视频片段 | `animator.py` | Video Gen |
| 配音师 (Voice Actor) | 生成角色对白音频 | `voice.py` | TTS |
| 拟音师 (Foley Artist) | 生成环境音与音效 | `foley.py` | TTS / Audio Gen |
| 剪辑师 (Editor) | 合成视频、添加字幕与转场 | `editor.py` | MoviePy + FFmpeg + Whisper |
| 监制 (Supervisor) | 流程控制、上下文组装、QC、重拍 | `supervisor.py` | LLM |

---

## 3. 数据协议

### 3.1 screenplay.json

编剧产出的结构化剧本，是全部流程的起点。

```json
{
  "meta": {
    "title": "雨夜序章",
    "style": "赛博朋克, 电影感, 冷色调",
    "total_duration_est": 90
  },
  "characters": {
    "男主": {
      "appearance": "25岁，黑色短发，深蓝眼睛，左眉尾有疤痕，棱角分明，深灰风衣",
      "voice_id": "male_01"
    }
  },
  "shots": [
    {
      "shot_id": 1,
      "character": "男主",
      "dialogue": "这一次，我不会再逃了。",
      "emotion": "坚定",
      "scene_desc": "深夜天台，城市灯火在脚下铺展，逆光，风吹动衣角",
      "camera": "中景，微仰视",
      "motion": "镜头缓慢推进，人物身体轻微晃动",
      "ambient": "城市低频嗡鸣，风声",
      "duration_sec": 4,
      "transition": "硬切"
    }
  ]
}
```

### 3.2 Manifest 文件规范

每个 manifest 记录一个子代理步骤的输入、输出、状态。统一格式：

```yaml
version: "1.0"
step: "illustrate"
shot_id: 1
status: "success"           # pending | running | success | failed | skipped
input:
  character: "男主"
  character_ref: "assets/characters/男主/standard.png"
  scene_desc: "深夜天台，城市灯火..."
  camera: "中景，微仰视"
  style: "赛博朋克, 电影感, 冷色调"
output:
  keyframe: "outputs/my_project/shot_01/shot_01_keyframe.png"
model:
  provider: "openai"
  model: "gpt-image-2"
timing:
  started_at: "2026-05-02T10:30:00Z"
  finished_at: "2026-05-02T10:30:12Z"
  duration_sec: 12
error:
  type: null                  # api_timeout | api_rate_limit | model_error | file_not_found | validation_error
  message: null
  retry_count: 0
  recoverable: null
  occurred_at: null
```

**各子代理 output 扩展：**

| 子代理 | output 特有字段 |
|--------|----------------|
| 画师 | `keyframe` |
| 动效师 | `video`, `source_frame`, `has_frontal_face` |
| 配音师 | `audio`, `phoneme_alignment` |
| 拟音师 | `audio` |
| 剪辑师 | `final_shot`, `subtitle` |

### 3.3 shot_brief.yaml（统一入口）

监制为每个镜头生成，并随步骤推进动态追加字段。子代理只读不写。

**初始版（画师调用前）：**
```yaml
shot_id: 1
character: "男主"
character_ref: "assets/characters/男主/standard.png"
dialogue: "这一次，我不会再逃了。"
emotion: "坚定"
scene_desc: "深夜天台，城市灯火在脚下铺展，逆光，风吹动衣角"
camera: "中景，微仰视"
motion: "镜头缓慢推进，人物身体轻微晃动"
ambient: "城市低频嗡鸣，风声"
duration_sec: 4
style: "赛博朋克, 电影感, 冷色调"
```

**画师跑完后追加：**
```yaml
keyframe: "outputs/my_project/shot_01/shot_01_keyframe.png"
```

**动效师跑完后追加：**
```yaml
video: "outputs/my_project/shot_01/shot_01_video.mp4"
source_frame: "outputs/my_project/shot_01/shot_01_keyframe.png"
has_frontal_face: true
```

**无对话镜头的处理：**
- 当 `dialogue` 为 `null` 或空字符串时，监制跳过 `voice.py`，标记 voice 步骤为 `"skipped"`
- `foley.py` 同理：`ambient` 为空时跳过

---

## 4. Pipeline CLI 接口

所有 `pipeline/*.py` 使用 Click 实现子命令，子代理通过 Bash 调用。

### screenwriter.py

```
python pipeline/screenwriter.py generate \
    --idea "雨夜天台上的最后告别" \
    --style "赛博朋克, 电影感" \
    --output outputs/my_project/screenplay.json
```
产出：`screenplay.json` + `screenplay.manifest.yaml`

### supervisor.py（流程编排中枢）

```
python pipeline/supervisor.py run \
    --project my_project \
    --config config.yaml \
    [--from-step illustrate]
```
调度逻辑（伪代码）：
```python
def run_project(project, config):
    screenplay = load_screenplay(project)
    for shot in screenplay['shots']:
        brief_path = prepare_shot(project, shot)

        if not manifest_exists(shot, 'illustrate'):
            call('illustrator.py generate-shot --input-file', brief_path)
            update_brief_with_keyframe(brief_path, manifest)

        if not manifest_exists(shot, 'animate'):
            call('animator.py generate --input-file', brief_path)
            update_brief_with_video(brief_path, manifest)

        if shot.get('dialogue') and not manifest_exists(shot, 'voice'):
            call('voice.py generate --input-file', brief_path)

        if shot.get('ambient') and not manifest_exists(shot, 'foley'):
            call('foley.py generate --input-file', brief_path)

        if not manifest_exists(shot, 'edit'):
            call('editor.py generate --input-file', brief_path, '--screenplay', screenplay_path)

    final_assembly(project)
```

```
python pipeline/supervisor.py retake \
    --project my_project \
    --shot-id 3
```
逻辑：删除 `shot_03/` 下所有 manifest 及中间产物 → 从画师开始重调度 shot_03。

```
python pipeline/supervisor.py status \
    --project my_project
```
汇总所有 manifest，输出每个 shot 每步的状态矩阵。

### illustrator.py

```
python pipeline/illustrator.py generate-character \
    --name "男主" \
    --appearance "25岁，黑色短发，深蓝眼睛，左眉尾有疤痕" \
    --angles front,side,quarter,back \
    --output assets/characters/男主/
```
产出多角度标准照 + `character.manifest.yaml`

```
python pipeline/illustrator.py generate-shot \
    --input-file outputs/my_project/shot_01/shot_brief.yaml
```
读取 `shot_brief.yaml` → 拼接 prompt（外貌 + 场景 + 镜头 + 风格）→ 调 API → 输出关键帧 + manifest

### animator.py / voice.py / foley.py / editor.py

统一模式：
```
python pipeline/{module}.py generate \
    --input-file outputs/my_project/shot_01/shot_brief.yaml
```
编辑器额外接收 `--screenplay` 参数用于字幕。

---

## 5. 模型配置

`config.yaml` 按用途分类，固定键名约定，每个 `.py` 脚本读取自己对应的节。

```yaml
image_generation:
  provider: "openai"
  model: "gpt-image-2"
  api_key: "${OPENAI_API_KEY}"

video_generation:
  provider: "seedance"
  model: "seedance-v1"
  api_key: "${SEEDANCE_API_KEY}"

tts:
  provider: "elevenlabs"
  model: "eleven_turbo_v2"
  api_key: "${ELEVENLABS_API_KEY}"

llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"
```

---

## 6. 项目目录结构

```
openmanga/
├── config.yaml
├── pipeline/
│   ├── screenwriter.py
│   ├── illustrator.py
│   ├── animator.py
│   ├── voice.py
│   ├── foley.py
│   ├── editor.py
│   └── supervisor.py
├── agents/
│   ├── screenwriter.md
│   ├── illustrator.md
│   ├── animator.md
│   ├── voice.md
│   ├── foley.md
│   ├── editor.md
│   └── supervisor.md
├── assets/
│   ├── characters/
│   ├── styles/
│   └── audio/
├── outputs/
│   └── <project_name>/
│       ├── screenplay.json
│       ├── screenplay.manifest.yaml
│       ├── shot_01/
│       │   ├── shot_brief.yaml
│       │   ├── shot_01_keyframe.png
│       │   ├── shot_01_illustrate.manifest.yaml
│       │   ├── shot_01_video.mp4
│       │   ├── shot_01_animate.manifest.yaml
│       │   ├── shot_01_voice.wav
│       │   ├── shot_01_voice.manifest.yaml
│       │   └── ...
│       ├── shot_02/
│       └── final.mp4
├── tests/
│   ├── test_screenwriter.py
│   ├── test_illustrator.py
│   ├── test_animator.py
│   ├── test_voice.py
│   ├── test_foley.py
│   ├── test_editor.py
│   ├── test_supervisor.py
│   └── fixtures/
│       ├── sample_screenplay.json
│       └── cassettes/
└── README.md
```

---

## 7. 实施路线图

### Phase 1：核心管道 MVP

**目标**：从一个创意生成一段 30–60 秒的视频，关键帧硬切，配对白和字幕。

| 模块 | Phase 1 | Phase 2+ |
|------|---------|----------|
| 编剧 | ✅ | — |
| 画师 | ✅ 角色标准照 + 所有分镜关键帧 | 图生图一致性插件 |
| 动效师 | ❌ 跳过 | ✅ 视频生成 + Wav2Lip |
| 配音师 | ✅ 仅对白 | 情感参数注入 |
| 拟音师 | ❌ 跳过 | ✅ 环境音 + 音效 |
| 剪辑师 | ✅ 图片序列→MP4 + SRT + 配音合轨 | 转场特效 + 动感字幕 + BGM |
| 监制 | ✅ run / retake / status | 成本统计、自动模型切换 |
| 测试 | ✅ 每模块单元测试 | 端到端集成测试 |

### Phase 2：动态与情绪升级

- 接入动效师代理
- 增加拟音师
- 实现 Wav2Lip 口型同步
- 转场逻辑、动感字幕
- 配置文件切换风格（二次元/写实/电影感）

### Phase 3：生态与进化

- 吸收更先进模型
- Web 界面
- 用户反馈闭环
- 系列剧跨集复用
- 开源社区共建

---

## 8. 关键风险与应对

| 风险 | 应对 |
|------|------|
| 角色外貌漂移 | 强制参考图注入 + 多角度标准照 |
| 视频生成模型崩坏 | 限制运动幅度，高风险镜头使用静帧 |
| API 调用成本过高 | 按镜头复杂度路由不同模型 |
| 多代理流程卡死 | Manifest 独立缓存 + `--retake` 断点续传 |
| 声音风格不统一 | 角色 Voice ID 固定化 |

---

## 9. 测试策略

- **单元测试**：每个 `pipeline/*.py` 的 CLI 解析、manifest 读写、shot_brief 解析
- **API Mock 测试**：用 `vcr.py` 录制真实 API 响应，离线重放验证
- **集成测试**：微缩剧本（2 镜头），全流程跑通
