---
name: openmanga-web
description: >-
  Start the OpenManga Streamlit web console. Use whenever the user wants to
  launch, start, open, or run the OpenManga web panel, web UI, dashboard,
  or web console. Triggers: "启动web面板", "打开控制台", "launch OpenManga",
  "start web UI", "open the dashboard", "run the web app".
---

# OpenManga Web Launcher

启动 OpenManga 的 Streamlit Web 控制台。

## 启动

```bash
cd /home/cszx/workspace/OpenManga
pkill -f "streamlit run" 2>/dev/null || true
nohup .venv/bin/streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false > /tmp/streamlit.log 2>&1 &
sleep 3
```

验证：

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
```

应返回 `200`。

## 结果

Web 面板运行在 `http://localhost:8501`，包含五个页面：

| 页面 | 功能 |
|------|------|
| 🏠 项目管理 | 创建/选择项目 |
| ✍️ 剧本工作室 | 输入创意 → AI 生成剧本 |
| 🎬 制作看板 | 一键运行管线 + 状态矩阵 + 预览 |
| 🖼️ 资产库 | 角色标准照 + 配音试听 |
| ⚙️ 设置 | API Key + 模型配置 |

## 约束

- 工作目录必须是 `/home/cszx/workspace/OpenManga`
- 使用 `.venv/bin/python`，不是系统 python
- 端口 8501，如果被占用会先 kill 旧进程
- 启动后报告 URL 给用户
