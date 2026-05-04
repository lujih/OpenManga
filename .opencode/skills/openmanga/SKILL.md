---
name: openmanga
description: >-
  OpenManga is a full AI-generated comic drama pipeline. Use whenever the user
  wants to create a manga, comic, short film, or video drama; generate a
  screenplay; design characters; create keyframes; add voice acting; or
  compose a final video. Triggers: "make a comic", "generate a manga",
  "create a short film", "做一集漫剧", "生成剧本", "画角色", "配音",
  "合成视频", "帮我做动画", "做一个短片". Even if the user doesn't
  explicitly say "manga" or "comic", use this skill when they describe
  wanting to create a visual story with AI-generated images and audio.
---

# OpenManga — 全AI漫剧创作

从创意到成片的全流程 AI 管线：编剧 → 画师 → 配音师 → 剪辑师，由监制调度。

## 前置条件

在调用任何命令前，先检查工作目录是否在 OpenManga 项目根目录（应存在 `pyproject.toml` 和 `.venv/`）。

如果 `.venv/` 不存在，提示用户运行 `python install.py`。

## 一、全流程（用户说"帮我做一集"）

1. 询问用户创意和风格（如用户只给了模糊想法，根据内容推荐风格）
2. 确定项目名（默认 `my_project`，如有重名追加数字）
3. 生成剧本：
```bash
.venv/bin/python OpenManga/pipeline/screenwriter.py generate \
    --idea "..." \
    --style "..." \
    --output OpenManga/outputs/<project>/screenplay.json \
    --config OpenManga/config.yaml
```
4. 读取生成的 `screenplay.json`，提取所有角色。对每个在 `OpenManga/assets/characters/<name>/` 下不存在的角色，生成标准照：
```bash
.venv/bin/python OpenManga/pipeline/illustrator.py generate-character \
    --name "<角色名>" \
    --appearance "<外貌描述>" \
    --output OpenManga/assets/characters/<name>/ \
    --config OpenManga/config.yaml
```
5. 运行全流程：
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py run \
    --project <project> \
    --config OpenManga/config.yaml
```
6. 检查状态：
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py status \
    --project <project>
```
7. 如有失败镜头（状态显示 FAIL），重拍：
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py retake \
    --project <project> --shot-id <N> \
    --config OpenManga/config.yaml
```

## 二、单步操作

### 生成剧本
```bash
.venv/bin/python OpenManga/pipeline/screenwriter.py generate \
    --idea "..." --style "..." \
    --output OpenManga/outputs/<project>/screenplay.json \
    --config OpenManga/config.yaml
```
产出 `screenplay.json` + manifest

### 生成角色
```bash
.venv/bin/python OpenManga/pipeline/illustrator.py generate-character \
    --name "..." --appearance "..." \
    --output OpenManga/assets/characters/<name>/ \
    --config OpenManga/config.yaml
```
产出 front/side/quarter/back 四张 PNG + manifest

### 运行/续跑管线
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py run \
    --project <project> \
    --config OpenManga/config.yaml
```
自动跳过已完成步骤，只补跑缺失步骤。

### 查看状态
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py status --project <project>
```
显示 Shot × Step 状态矩阵。

## 三、错误处理

- **API 超时或限流**：等待 5 秒后重试，最多 3 次。检查 manifest 中 error.type 判断原因
- **LLM 返回非 JSON**：重试时在 system prompt 中强调"只返回 JSON，不要 markdown 包裹"
- **图像生成不符合预期**：调整 prompt 中的 scene_desc 细节重试
- **config.yaml 缺失**：提示用户 `OpenManga/config.yaml` 不存在，需创建或从模板复制
- **所有命令在项目根目录执行**，使用 `.venv/bin/python`

## 四、产出文件结构

```
OpenManga/outputs/<project>/
├── screenplay.json
├── screenplay.manifest.yaml
├── shot_01/
│   ├── shot_brief.yaml
│   ├── shot_01_keyframe.png
│   ├── shot_01_illustrate.manifest.yaml
│   ├── shot_01_voice.wav
│   ├── shot_01_voice.manifest.yaml
│   └── shot_01_final.mp4
└── shot_02/ ...
```
