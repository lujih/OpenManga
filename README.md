# 🎬 OpenManga · 全AI生成式漫剧工厂

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> 让一个人，只凭想法，就能创造出角色一致、视听完整的AI漫剧。

## ✨ 特性

- **全模型驱动** — 剧本、图像、配音、视频合成均由 AI 模型生成
- **角色一致性** — 多角度标准照 + 参考图注入，跨镜头保持外貌稳定
- **Provider 可插拔** — 支持 OpenAI / Anthropic / ElevenLabs / DeepSeek / Ollama 等任意组合
- **三个入口** — CLI 命令、Streamlit Web 控制台、OpenCode AI 对话
- **断点续传** — Manifest 状态系统，中断后自动跳过已完成步骤

## 🏗️ 架构

```
用户 → Web控制台 / CLI / AI对话
              │
    ┌─────────┼──────────┬───────────┐
    ▼         ▼          ▼           ▼
  编剧      画师       配音师      剪辑师
   LLM      DALL·E     TTS        MoviePy
   │         │          │           │
   ▼         ▼          ▼           ▼
 剧本JSON   关键帧    对白音频    视频合成
              │
              ▼
          监制 (run / retake / status)
```

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/lujih/OpenManga.git
cd OpenManga

# 2. 安装
python install.py

# 3. 配置 API Key
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export ELEVENLABS_API_KEY="..."

# 4. 生成剧本
python OpenManga/pipeline/screenwriter.py generate \
    --idea "雨夜天台，最后一场告别" \
    --style "赛博朋克, 电影感" \
    --output outputs/my_project/screenplay.json

# 5. 一键生成完整视频
python OpenManga/pipeline/supervisor.py run --project my_project

# 6. 查看状态
python OpenManga/pipeline/supervisor.py status --project my_project
```

### Web 控制台

```bash
streamlit run OpenManga/app.py
# → http://localhost:8501
```

五个页面：🏠 项目管理 · ✍️ 剧本工作室 · 🎬 制作看板 · 🖼️ 资产库 · ⚙️ 设置

### OpenCode AI 对话

安装后，任何 OpenCode 会话中直接说"帮我做一集漫剧"即可。

## 📁 目录结构

```
openmanga/
├── .opencode/                # OpenCode 配置
│   ├── opencode.json
│   ├── skills/               # Skill 文件
│   └── agents/               # 子代理定义
├── OpenManga/                # 源码包
│   ├── pipeline/             # 核心引擎
│   │   ├── screenwriter.py   # 编剧 — LLM 生成剧本
│   │   ├── illustrator.py    # 画师 — 角色 + 关键帧
│   │   ├── voice.py          # 配音师 — TTS 对白
│   │   ├── editor.py         # 剪辑师 — 合成 + 字幕
│   │   ├── supervisor.py     # 监制 — 流程编排
│   │   ├── config.py         # 配置加载
│   │   └── manifest.py       # 状态管理
│   ├── pages/                # Streamlit 页面
│   ├── tests/                # 测试 (38)
│   ├── assets/               # 资产库
│   └── app.py                # Streamlit 入口
├── scripts/                  # 工具脚本
│   └── install.py            # 跨平台安装器
├── logs/                     # 运行时日志
├── outputs/                  # 项目输出
├── config.yaml               # 模型配置
├── app.py                    # [root] Streamlit 快捷入口
└── README.md
```

## ⚙️ Provider 配置

`config.yaml` 支持多提供商 + 自定义端点。`api_base` 留空使用默认端点：

```yaml
# 用 DeepSeek 替代 Anthropic
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: ${DEEPSEEK_KEY}
  api_base: "https://api.deepseek.com/v1"
  params:
    max_tokens: 4096

# 用本地 Ollama
image_generation:
  provider: ollama
  model: stable-diffusion-xl
  api_key: "na"
  api_base: "http://localhost:11434/v1"
  params:
    size: "1024x1024"
```

provider 为空时默认走 OpenAI 协议。

## 🗺️ 路线图

| 阶段 | 内容 |
|------|------|
| ✅ Phase 1 | 编剧 + 画师 + 配音 + 剪辑 + 监制 + Web + Skill |
| ⏳ Phase 2 | 动效师 (视频生成) + 拟音师 (环境音) + Wav2Lip 口型同步 |
| 🔮 Phase 3 | 系列剧支持、开源社区共建 |
