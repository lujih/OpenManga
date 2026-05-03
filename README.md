# OpenManga · 全AI生成式漫剧工厂

让一个人，只凭想法，就能创造出角色一致、视听完整的AI漫剧。

## 架构

```
用户 → Web控制台 / CLI / AI对话
              │
    ┌─────────┼──────────┬───────────┐
    ▼         ▼          ▼           ▼
  编剧      画师       配音师      剪辑师
   │         │          │           │
   ▼         ▼          ▼           ▼
 screenplay  关键帧    对白音频    视频合成
  JSON      + manifest  + manifest  + manifest
              │
              ▼
          监制 (run / retake / status)
```

## 快速开始

```bash
# 1. 安装
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. 配置 API key
export OPENAI_API_KEY="sk-..."      # 生图
export ANTHROPIC_API_KEY="sk-..."   # 剧本 (或改用 DeepSeek/OpenAI)
export ELEVENLABS_API_KEY="..."     # 配音 (或改用 OpenAI TTS)

# 3. 生成剧本
python pipeline/screenwriter.py generate \
    --idea "雨夜天台，最后一场告别" \
    --style "赛博朋克, 电影感, 冷色调" \
    --output outputs/my_project/screenplay.json

# 4. 一键生成完整视频
python pipeline/supervisor.py run --project my_project

# 5. 查看状态
python pipeline/supervisor.py status --project my_project
```

### 使用 Web 控制台

```bash
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，五个页面：项目管理 → 剧本工作室 → 制作看板 → 资产库 → 设置。

### 使用 OpenCode Skill

将 `skills/openmanga.md` 复制到 `~/.opencode/skills/`，之后在任何 OpenCode 会话中说"帮我做一集漫剧"即可。

## 目录结构

```
openmanga/
├── config.yaml              # 模型配置 (provider / api_base / params)
├── pipeline/                # 核心引擎
│   ├── screenwriter.py      # 编剧 — LLM 生成结构化剧本
│   ├── illustrator.py        # 画师 — 角色标准照 + 分镜关键帧
│   ├── animator.py           # 动效师 — 关键帧→视频 (Phase 2)
│   ├── voice.py              # 配音师 — TTS 对白生成
│   ├── foley.py              # 拟音师 — 环境音 (Phase 2)
│   ├── editor.py             # 剪辑师 — 合成视频 + 字幕
│   └── supervisor.py         # 监制 — 流程编排
├── agents/                   # OpenCode 子代理 prompt
├── skills/                   # OpenCode Skill 文件
├── pages/                    # Streamlit Web 页面
├── tests/                    # 测试 (29 tests)
└── outputs/                  # 项目输出
```

## Provider 配置

`config.yaml` 支持多提供商 + 自定义端点。示例：

```yaml
# 用 DeepSeek 替代 Anthropic
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: ${DEEPSEEK_KEY}
  api_base: "https://api.deepseek.com/v1"
  params:
    max_tokens: 4096

# 用 OpenAI TTS 替代 ElevenLabs
tts:
  provider: openai
  model: tts-1
  api_key: ${OPENAI_API_KEY}
  params:
    voice: alloy
    response_format: mp3
```

provider 为空或不填时默认走 OpenAI 协议。

## 路线图

| 阶段 | 内容 |
|------|------|
| ✅ Phase 1 | 编剧 + 画师 + 配音 + 剪辑 + 监制 + Web + Skill |
| ⏳ Phase 2 | 动效师 (视频生成) + 拟音师 (环境音) + Wav2Lip |
| 🔮 Phase 3 | Web 协作、系列剧支持、开源社区 |
