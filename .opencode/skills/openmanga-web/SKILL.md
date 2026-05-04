---
name: openmanga-web
description: >-
  Start the OpenManga Streamlit web console. Use whenever the user asks to
  launch, start, open, or run the OpenManga web UI, dashboard, control panel,
  or web app. Triggers: "启动web面板", "打开控制台", "打开网页",
  "launch OpenManga", "start the web UI", "open the dashboard", "run web",
  "启动Streamlit".
---

# OpenManga Web 面板启动器

## 启动

在项目根目录执行：

```bash
.venv/bin/streamlit run OpenManga/app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > OpenManga/logs/streamlit.log 2>&1 &
sleep 3
```

如端口被占用，先清理：

```bash
kill $(lsof -ti :8501) 2>/dev/null || true
```

## 验证

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
```
应返回 `200`。非 200 时检查 `OpenManga/logs/streamlit.log`。

## 结果

面板运行在 `http://localhost:8501`：

| 页面 | 功能 |
|------|------|
| 🏠 项目管理 | 创建/选择项目 |
| ✍️ 剧本工作室 | 创意输入 → AI 生成剧本 |
| 🎬 制作看板 | 一键运行 + 状态矩阵 + 预览 |
| 🖼️ 资产库 | 角色标准照 + 配音试听 |
| ⚙️ 设置 | API Key + 模型配置 |

启动后报告 URL 给用户。
