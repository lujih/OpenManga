#!/usr/bin/env python3
"""OpenManga 跨平台安装脚本 — 一条命令完成全部配置"""
import os
import subprocess
import sys
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, cwd=str(ROOT), **kw)


def main():
    print("🎬 OpenManga 安装器\n")

    if sys.version_info < (3, 10):
        sys.exit("❌ 需要 Python >= 3.10，当前版本: " + sys.version)

    venv = ROOT / ".venv"
    if not venv.exists():
        print("📦 创建虚拟环境...")
        run(f"{sys.executable} -m venv .venv", check=True)

    pip = (
        str(venv / "bin" / "pip")
        if platform.system() != "Windows"
        else str(venv / "Scripts" / "pip")
    )
    print("📥 安装依赖...")
    run(f'"{pip}" install -e ".[dev]"', check=True)

    (ROOT / "logs").mkdir(exist_ok=True)

    py = str(venv / "bin" / "python")
    streamlit = str(venv / "bin" / "streamlit")

    print("\n✅ 安装完成\n")
    print("Skills 和 Agents 已在 .opencode/ 目录，OpenCode 自动发现。")
    print("\n配置 API Key：")
    print("  export OPENAI_API_KEY=sk-...")
    print("  export ANTHROPIC_API_KEY=sk-...")
    print("  export ELEVENLABS_API_KEY=...")
    print(f"\n启动 Web 面板：{streamlit} run app.py")
    print(f"\n生成第一集：")
    print(f"  {py} pipeline/screenwriter.py generate --idea '你的创意' --style '写实' --output outputs/my_project/screenplay.json")
    print(f"  {py} pipeline/supervisor.py run --project my_project")


if __name__ == "__main__":
    main()
