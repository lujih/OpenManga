# OpenManga · 双入口架构（Web + Skill）— 系统设计

> **目标**  
> 在现有 CLI 核心引擎之上，新增 Web 控制台（人类友好）和 OpenCode Skill（AI 友好），让"一个人，只凭想法"就能创作。核心引擎 `pipeline/` 零改动。

---

## 1. 架构总览

```
                    ┌──────────────────────────────┐
                    │    OpenManga 核心引擎         │
                    │    pipeline/*.py (不变)       │
                    │    config.yaml / manifest     │
                    └──────────────┬───────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  CLI (已有)      │  │  Web (新增)      │  │  Skill (新增)    │
    │  pipeline/*.py   │  │  app.py          │  │  openmanga.md   │
    ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
    │ 面向：开发者/脚本  │  │ 面向：人类创作者   │  │ 面向：AI 代理     │
    │ 触发：Bash 命令   │  │ 触发：浏览器点击   │  │ 触发：自然语言     │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
```

**核心原则：**
- `pipeline/` 模块零改动，Web 和 Skill 只是新消费端
- Web 通过 `subprocess.Popen` + 异步轮询 manifest 调用 CLI
- Skill 通过 Bash 调用 CLI，AI 加载后自行决定调用哪个步骤
- 三者共享同一套 manifest 状态系统，互不冲突

---

## 2. Web 控制台设计

技术栈：**Streamlit**，通过 `subprocess.Popen` 非阻塞调用 CLI，异步轮询 manifest 文件获取进度。

### 2.1 页面路由

五个页面由 Streamlit `pages/` 目录自动路由，数字前缀控制顺序：

```
app.py                         # 主入口：重定向到项目管理
pages/
├── 01_projects.py             # 项目管理
├── 02_screenplay.py           # 剧本工作室
├── 03_dashboard.py            # 制作看板（核心）
├── 04_assets.py               # 资产库
└── 05_settings.py             # 设置
```

### 2.2 各页面设计

#### 🏠 01_projects.py — 项目管理

- **新建项目**：输入框（项目名）+ 风格选择器（下拉：赛博朋克 / 写实 / 电影感 / 自定义）
- **项目列表**：从 `outputs/` 读取子目录，卡片式展示。每张卡片显示项目名、进度条（已生成镜头数/总镜头数）、最后修改时间
- **点击卡片** → `st.session_state.project` 设置为该项目名，自动跳转到 03_dashboard

#### ✍️ 02_screenplay.py — 剧本工作室

- **创意输入**：多行文本 + 风格选择（从 `config.yaml` 或预设读取）
- **"生成剧本"按钮** → `subprocess.Popen` 调 `screenwriter.py generate`，轮询 `shot_00_screenplay.manifest.yaml` 等待完成
- **剧本预览**：左侧角色卡片（角色名 + 外貌描述），右侧分镜表格（shot_id, 角色, 对白, 场景, 景别, 时长），所有字段可编辑
- **"保存修改"按钮** → 写回 `screenplay.json`
- **"进入制作"按钮** → 跳转到 03_dashboard

#### 🎬 03_dashboard.py — 制作看板（核心页面）

- **顶部栏**：项目名 + 风格标签 + "一键运行"按钮
- **状态矩阵**：
  - 行 = shot，列 = illustrate / voice / edit
  - 状态标记：✅ OK | ⏳ PENDING | ❌ FAIL（悬停显示 `error.message`）| — SKIP
  - 数据源：`supervisor.py status` 输出的文本表格，Web 端解析各行状态标记
- **每行操作**："重拍此镜"按钮 → 调 `supervisor.py retake --shot-id N`（清理+自动重生成），轮询 manifest 更新进度
- **右侧预览面板**：选中镜头 → 显示关键帧缩略图（`shot_NN_keyframe.png`）+ 配音播放器（`shot_NN_voice.wav`）
- **底部**：整体进度条 + 实时日志区（`subprocess` stdout 流）
- **并发控制**：运行前检查 `.lock_running` 文件，存在则弹提示"已有任务在运行"，不允许多个 run 进程并发

#### 🖼️ 04_assets.py — 资产库

- **角色列表**：从 `assets/characters/` 读取子目录列表
- **角色详情**：多角度标准照网格（front / side / quarter / back），从对应目录读取 PNG 文件
- **"重新生成"按钮** → 调 `illustrator.py generate-character`
- **"设为默认参考图"**：勾选某个角度（如 front.png），写入偏好到角色目录下的 `_default.txt`
- **配音试听**：从 `outputs/<project>/shot_NN/` 读取所有 `.wav` 文件，可点击播放

#### ⚙️ 05_settings.py — 设置

- **API Key 管理**：四个 provider（image_generation / video_generation / tts / llm），输入框支持显示/隐藏。保存时用单引号包裹写入 `config.yaml`，避免 `$` 被 YAML 误解析
- **模型选择**：下拉框，选项从各 provider SDK 的可用模型列表获取（或预设常用模型）
- **输出目录**：可自定义 `outputs/` 根路径

---

## 3. Skill 文件设计

**文件**：`skills/openmanga.md`

**定位**：Master Skill，AI 加载后自行决定调用哪个 CLI 步骤。只回答"我是什么、何时用我、怎么调"，不重复 agents/ 里的思考逻辑。

**内容**：

```markdown
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
2. 生成剧本：`python pipeline/screenwriter.py generate --idea "..." --style "..." --output outputs/<project>/screenplay.json`
3. 为每个角色生成标准照（如 `assets/characters/<name>/` 不存在）：
   `python pipeline/illustrator.py generate-character --name "..." --appearance "..." --output assets/characters/<name>/`
4. 运行全流程：`python pipeline/supervisor.py run --project <project>`
5. 检查状态：`python pipeline/supervisor.py status --project <project>`
6. 如有失败镜头：`python pipeline/supervisor.py retake --project <project> --shot-id N`
   （该命令自动清理旧产物并重新生成所有缺失步骤）

## 单步操作

### 生成剧本
python pipeline/screenwriter.py generate --idea "..." --style "..." --output outputs/<project>/screenplay.json

### 生成角色标准照
python pipeline/illustrator.py generate-character --name "..." --appearance "..." --output assets/characters/<name>/

### 运行/续跑管线
python pipeline/supervisor.py run --project <project>
自动跳过已完成的步骤，只补跑缺失步骤。

### 查看状态
python pipeline/supervisor.py status --project <project>

### 单镜重拍
python pipeline/supervisor.py retake --project <project> --shot-id N

## 约束
- 所有命令在项目根目录 OpenManga/ 下执行
- 使用 `.venv/bin/python` 而非系统 python
- config.yaml 需先配置 image_generation / tts / llm 三节的 api_key
- retake 会自动重生成，无需额外调用 run
```

---

## 4. 文件结构更新

```
openmanga/
├── app.py                      # [NEW] Streamlit 主入口
├── pages/
│   ├── 01_projects.py          # [NEW]
│   ├── 02_screenplay.py        # [NEW]
│   ├── 03_dashboard.py         # [NEW] 核心页面
│   ├── 04_assets.py            # [NEW]
│   └── 05_settings.py          # [NEW]
├── skills/
│   └── openmanga.md            # [NEW] Master Skill
├── pipeline/                   # [UNCHANGED]
├── agents/                     # [UNCHANGED]
├── tests/
│   └── web/
│       └── test_app.py         # [NEW]
├── config.yaml                 # [UNCHANGED]
└── pyproject.toml              # [MODIFY] 加 streamlit>=1.30 依赖
```

### pyproject.toml 变更

在 `dependencies` 中新增：
```toml
"streamlit>=1.30",
```

---

## 5. supervisor.py retake 行为变更

**当前行为**：`retake` 只清理 manifest 和中间产物，不重生成。  
**新行为**：`retake` 清理后自动调用该镜头的 illustrate → voice → edit 流程，无需再跑 `run`。

改动点：在 `retake` 命令末尾，复用 `run` 的镜头级调度逻辑（只处理指定 shot_id）。

---

## 6. 并发控制

Web 调用 `supervisor.py run` 时用 `.lock_running` 文件互斥：

- `run` 启动时创建 `outputs/<project>/.lock_running`
- `run` 结束时删除该文件
- 若文件已存在 → 拒绝执行，返回"已有任务在运行"
- Web 端检查到 lock → 禁用"一键运行"按钮并提示

对单人本地使用足够，无需队列系统。

---

## 7. 实施路线

| 步骤 | 内容 | 预计 |
|------|------|------|
| 1 | 修复 `supervisor.py` retake（清理+重生成） | 小 |
| 2 | 搭建 Streamlit 框架（app.py + 5 页面骨架） | 中 |
| 3 | 实现 03_dashboard（核心页面，含 Popen + 轮询 + lock） | 核心 |
| 4 | 实现 01_projects + 02_screenplay | 中 |
| 5 | 实现 04_assets + 05_settings | 中 |
| 6 | 编写 `skills/openmanga.md` | 轻量 |
| 7 | Web 测试 + 端到端验证 | 中 |
