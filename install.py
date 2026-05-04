#!/usr/bin/env python3
"""OpenManga 安装脚本 — 克隆后一条命令完成全部配置

用法:
  git clone https://github.com/lujih/OpenManga.git
  cd OpenManga
  python install.py
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, cwd=str(ROOT), **kw)


def print_step(msg):
    print(f"  › {msg}")


def main():
    print("\n🎬 OpenManga 安装器\n")

    # ---- 检查 Python 版本 ----
    if sys.version_info < (3, 10):
        sys.exit("❌ 需要 Python >= 3.10，当前: " + sys.version.split()[0])

    # ---- 检查是否在仓库根目录 ----
    if not (ROOT / "pyproject.toml").exists():
        sys.exit("❌ 请在 OpenManga 仓库根目录运行此脚本")

    # ---- 创建虚拟环境 ----
    venv = ROOT / ".venv"
    if not venv.exists():
        print_step("创建虚拟环境...")
        result = run(f'"{sys.executable}" -m venv .venv')
        if result.returncode != 0:
            sys.exit("❌ 创建虚拟环境失败，请确认 Python venv 模块可用")
    else:
        print_step("虚拟环境已存在，跳过")

    # ---- pip 路径 (跨平台) ----
    system = platform.system()
    pip = str(venv / "bin" / "pip") if system != "Windows" else str(venv / "Scripts" / "pip")
    python = str(venv / "bin" / "python") if system != "Windows" else str(venv / "Scripts" / "python")

    # ---- 安装依赖 ----
    print_step("安装依赖...")
    result = run(f'"{pip}" install -e ".[dev]"')
    if result.returncode != 0:
        print_step("普通安装失败，尝试无 dev 依赖...")
        result = run(f'"{pip}" install -e .', check=True)

    # ---- 创建必要的目录 ----
    for d in ["OpenManga/logs", "OpenManga/outputs", "OpenManga/assets/audio", "OpenManga/assets/styles"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)

    # ---- 验证安装 ----
    print_step("验证安装...")
    verify = subprocess.run(
        [python, "-c", "from pipeline.config import load_config"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if verify.returncode != 0:
        sys.exit(f"❌ 安装验证失败:\n{verify.stderr}")

    # ---- 完成 ----
    print("\n╔══════════════════════════════════╗")
    print("║      ✅ 安装完成                 ║")
    print("╚══════════════════════════════════╝\n")

    print("📌 下一步 — 配置 API Key：\n")
    print("  在 Linux / macOS 上：")
    print("    export OPENAI_API_KEY=sk-...")
    print("    export ANTHROPIC_API_KEY=sk-...")
    print("    export ELEVENLABS_API_KEY=...")
    print("  在 Windows (PowerShell) 上：")
    print("    $env:OPENAI_API_KEY='sk-...'")
    print("    $env:ANTHROPIC_API_KEY='sk-...'")
    print("    $env:ELEVENLABS_API_KEY='...'")
    print()
    print("  也可以编辑 OpenManga/config.yaml 直接填入 key")
    print()

    print("🚀 启动 Web 控制台：")
    streamlit = str(venv / "bin" / "streamlit") if system != "Windows" else str(venv / "Scripts" / "streamlit")
    print(f"  {streamlit} run OpenManga/app.py\n")

    print("🎬 命令行快速上手：")
    print(f"  {python} OpenManga/pipeline/screenwriter.py generate \\")
    print(f"      --idea '雨夜天台，最后一场告别' \\")
    print(f"      --style '赛博朋克' \\")
    print(f"      --output OpenManga/outputs/my_project/screenplay.json")
    print(f"  {python} OpenManga/pipeline/supervisor.py run --project my_project")
    print(f"  {python} OpenManga/pipeline/supervisor.py status --project my_project")
    print()

    print("💡 Skills 和 Agents 已在 .opencode/ 中，OpenCode 自动发现。\n")


if __name__ == "__main__":
    main()
