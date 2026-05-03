import os
import json
import subprocess
import sys
import time
import streamlit as st
import yaml
from pipeline.manifest import manifest_exists, get_manifest_status, manifest_path

st.title("🎬 制作看板")

if not st.session_state.project:
    st.warning("请先在项目管理中选择或创建一个项目")
    st.stop()

project = st.session_state.project
project_dir = os.path.join("outputs", project)
screenplay_path = os.path.join(project_dir, "screenplay.json")
lock_path = os.path.join(project_dir, ".lock_running")

if not os.path.exists(screenplay_path):
    st.warning("该项目还没有剧本，请先去剧本工作室生成")
    st.stop()

with open(screenplay_path) as f:
    screenplay = json.load(f)

PHASE1_STEPS = ["screenplay", "illustrate", "voice", "edit"]

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.caption(f"项目：**{project}** | 风格：{screenplay['meta'].get('style', 'N/A')}")
with col2:
    running = os.path.exists(lock_path)
    if st.button("▶️ 一键运行", type="primary", disabled=running, use_container_width=True):
        with open(lock_path, "w") as f:
            f.write(str(time.time()))
        subprocess.Popen([
            sys.executable, "pipeline/supervisor.py", "run",
            "--project", project, "--config", "config.yaml",
        ])
        st.rerun()
with col3:
    if st.button("🔄 刷新状态", use_container_width=True):
        st.rerun()

if os.path.exists(lock_path):
    st.info("⏳ 管线正在运行中...")
    time.sleep(1)
    st.rerun()

st.divider()

header_cols = st.columns([1] + [1] * (len(PHASE1_STEPS) - 1))
header_cols[0].markdown("**Shot**")
for i, step in enumerate(PHASE1_STEPS[1:], 1):
    header_cols[i].markdown(f"**{step}**")

shots = screenplay.get("shots", [])
selected_shot = st.session_state.get("selected_shot", None)

for shot in shots:
    shot_id = shot["shot_id"]
    cols = st.columns([1] + [1] * (len(PHASE1_STEPS) - 1))
    cols[0].write(f"Shot {shot_id:02d}")

    for i, step in enumerate(PHASE1_STEPS[1:], 1):
        status = get_manifest_status(project_dir, shot_id, step)
        if status == "success":
            cols[i].success("OK")
        elif status == "skipped":
            cols[i].info("SKIP")
        elif status == "failed":
            mf = manifest_path(project_dir, shot_id, step)
            if os.path.exists(mf):
                with open(mf) as mf_f:
                    err = yaml.safe_load(mf_f).get("error", {})
                cols[i].error(f"FAIL\n{err.get('message', 'unknown')[:30]}")
            else:
                cols[i].error("FAIL")
        else:
            cols[i].warning("-")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("重拍", key=f"retake_{shot_id}"):
            subprocess.Popen([
                sys.executable, "pipeline/supervisor.py", "retake",
                "--project", project, "--shot-id", str(shot_id), "--config", "config.yaml",
            ])
            st.rerun()
    with c2:
        if st.button(f"预览 Shot {shot_id:02d}", key=f"preview_{shot_id}"):
            st.session_state.selected_shot = shot_id
            st.rerun()

st.divider()

if selected_shot:
    st.subheader(f"预览 Shot {selected_shot:02d}")
    shot_dir = os.path.join(project_dir, f"shot_{selected_shot:02d}")
    prev_col1, prev_col2 = st.columns(2)
    with prev_col1:
        keyframe = os.path.join(shot_dir, f"shot_{selected_shot:02d}_keyframe.png")
        if os.path.exists(keyframe):
            st.image(keyframe, caption="关键帧", use_container_width=True)
        else:
            st.info("暂无关键帧")
    with prev_col2:
        voice = os.path.join(shot_dir, f"shot_{selected_shot:02d}_voice.wav")
        if os.path.exists(voice):
            st.audio(voice)
        else:
            st.info("暂无配音")
    video = os.path.join(shot_dir, f"shot_{selected_shot:02d}_final.mp4")
    if os.path.exists(video):
        st.video(video)
