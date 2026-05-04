#!/usr/bin/env python3
"""OpenManga 跨平台安装脚本 — 一条命令完成全部配置"""
import os
import subprocess
import sys
import shutil
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

    print("🔧 安装 OpenCode Skills...")
    skill_targets = [
        Path.home() / ".opencode" / "skills",
        Path.home() / ".config" / "opencode" / "skills",
    ]
    for sd in [".opencode/skills/openmanga", ".opencode/skills/openmanga-web"]:
        src = ROOT / sd
        if src.exists():
            for tgt in skill_targets:
                dst = tgt / src.name
                tgt.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    (ROOT / "logs").mkdir(exist_ok=True)

    print("\n✅ 安装完成\n")
    print("下一步 — 配置 API Key：")
    print("  export OPENAI_API_KEY=sk-...       # 图像生成")
    print("  export ANTHROPIC_API_KEY=sk-...    # 剧本（或改 config.yaml 切换提供商）")
    print("  export ELEVENLABS_API_KEY=...      # 配音（或改 config.yaml 切换到 OpenAI TTS）")
    print(f"\n启动 Web 面板：")
    print(f"  {venv / 'bin' / 'streamlit'} run app.py")
    print(f"\n生成第一集样片：")
    print(f"  {venv / 'bin' / 'python'} pipeline/screenwriter.py generate --idea '你的创意' --style '写实' --output outputs/my_project/screenplay.json")
    py = str(venv / "bin" / "python")
    print(f"  {py} pipeline/supervisor.py run --project my_project")


if __name__ == "__main__":
    main()
