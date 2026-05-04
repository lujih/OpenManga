---
name: openmanga
description: >-
  OpenManga is a full AI-generated comic drama pipeline. Use when the user
  wants to create a manga/comic drama, generate a screenplay, create character
  art, produce animated shots, add voice acting, or compose a final video.
  Triggers: "make a comic", "generate a manga", "create a short film",
  "我需要剧本/角色/分镜/配音/合成视频".
---

# OpenManga Skill

## 管线概览

编剧 → 画师 → 配音师 → 剪辑师，由监制统一调度。

## 快速开始（全流程）

如果用户说"帮我做一集漫剧"，执行：

1. 确定项目名（如用户未提供，用 `my_project`）
2. 生成剧本：
```bash
.venv/bin/python OpenManga/pipeline/screenwriter.py generate --idea "..." --style "..." --output OpenManga/outputs/<project>/screenplay.json
```
3. 为每个角色生成标准照（如 `OpenManga/assets/characters/<name>/` 不存在）：
```bash
.venv/bin/python OpenManga/pipeline/illustrator.py generate-character --name "..." --appearance "..." --output OpenManga/assets/characters/<name>/
```
4. 运行全流程：
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py run --project <project>
```
5. 检查状态：
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py status --project <project>
```
6. 如有失败镜头，重拍（自动清理+重生成）：
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py retake --project <project> --shot-id N
```

## 单步操作

### 生成剧本
用户只需提供创意和风格。
```bash
.venv/bin/python OpenManga/pipeline/screenwriter.py generate --idea "..." --style "..." --output OpenManga/outputs/<project>/screenplay.json
```
产出：`screenplay.json` + manifest

### 生成角色标准照
```bash
.venv/bin/python OpenManga/pipeline/illustrator.py generate-character --name "..." --appearance "..." --output OpenManga/assets/characters/<name>/
```
产出：`OpenManga/assets/characters/<name>/{front,side,quarter,back}.png` + manifest

### 运行/续跑管线
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py run --project <project>
```
自动跳过已完成的步骤，只补跑缺失步骤。

### 查看状态
```bash
.venv/bin/python OpenManga/pipeline/supervisor.py status --project <project>
```

## 约束
- 所有命令在项目根目录 `OpenManga/` 下执行
- 使用 `.venv/bin/python` 而非系统 python
- config.yaml 需先配置 image_generation / tts / llm 三节的 api_key
- retake 会自动清理旧产物并重生成所有缺失步骤，无需额外调用 run
