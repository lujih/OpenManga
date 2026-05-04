import os
import json
import subprocess
import sys
import time
import streamlit as st
import yaml

st.title("✍️ 剧本工作室")

if not st.session_state.project:
    st.warning("请先在项目管理中选择或创建一个项目")
    st.stop()

project_dir = os.path.join("outputs", st.session_state.project)
os.makedirs(project_dir, exist_ok=True)
screenplay_path = os.path.join(project_dir, "screenplay.json")

st.subheader("创意输入")
idea = st.text_area("故事创意", placeholder="深夜的雨巷里，一个身影缓缓走来...", height=100)
col1, col2 = st.columns(2)
with col1:
    style = st.text_input("视觉风格", value="写实, 电影感, 冷色调")
with col2:
    if st.button("🎬 生成剧本", type="primary", use_container_width=True):
        if idea:
            with st.spinner("AI 正在创作剧本..."):
                subprocess.run([
                    sys.executable, "pipeline/screenwriter.py", "generate",
                    "--idea", idea, "--style", style,
                    "--output", screenplay_path, "--config", "config.yaml",
                ], check=False)
            st.rerun()

if os.path.exists(screenplay_path):
    with open(screenplay_path) as f:
        screenplay = json.load(f)

    st.divider()
    st.subheader("📜 剧本预览")

    tab1, tab2, tab3 = st.tabs(["角色", "分镜", "JSON"])

    with tab1:
        if screenplay.get("characters"):
            cols = st.columns(min(len(screenplay["characters"]), 3))
            for i, (name, info) in enumerate(screenplay["characters"].items()):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{name}**")
                        st.caption(f"配音: {info.get('voice_id', '无')}")
                        st.text(info.get("appearance", ""))

    with tab2:
        shots = screenplay.get("shots", [])
        st.caption(f"共 {len(shots)} 个镜头，预估时长 {screenplay['meta'].get('total_duration_est', 0)} 秒")
        for shot in shots:
            with st.expander(f"镜 {shot['shot_id']} — {shot.get('character') or '环境'} — {shot.get('duration_sec', 0)}秒"):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("角色", shot.get("character", ""), key=f"ch_{shot['shot_id']}")
                    st.text_input("对白", shot.get("dialogue", ""), key=f"dl_{shot['shot_id']}")
                    st.text_input("情绪", shot.get("emotion", ""), key=f"em_{shot['shot_id']}")
                with c2:
                    st.text_area("场景描述", shot.get("scene_desc", ""), key=f"sc_{shot['shot_id']}", height=68)
                    st.text_input("景别", shot.get("camera", ""), key=f"ca_{shot['shot_id']}")
                st.number_input("时长(秒)", value=shot.get("duration_sec", 3), min_value=1, max_value=10, key=f"du_{shot['shot_id']}")

    with tab3:
        st.code(json.dumps(screenplay, ensure_ascii=False, indent=2), language="json")

    if st.button("进入制作 →", type="primary"):
        st.switch_page("pages/03_dashboard.py")
