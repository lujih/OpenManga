import os
import subprocess
import sys
import streamlit as st

st.title("🖼️ 资产库")

characters_dir = "assets/characters"
os.makedirs(characters_dir, exist_ok=True)
characters = sorted([d for d in os.listdir(characters_dir) if os.path.isdir(os.path.join(characters_dir, d))])

tab1, tab2 = st.tabs(["角色", "配音试听"])

with tab1:
    st.subheader("角色管理")
    if not characters:
        st.info("暂无角色资产")

    for char_name in characters:
        char_dir = os.path.join(characters_dir, char_name)
        angles = sorted([f for f in os.listdir(char_dir) if f.endswith(".png")])

        st.markdown(f"### {char_name}")
        if angles:
            cols = st.columns(min(len(angles), 4))
            for i, angle_file in enumerate(angles):
                with cols[i % 4]:
                    angle_path = os.path.join(char_dir, angle_file)
                    st.image(angle_path, caption=angle_file, use_container_width=True)
                    default_marker = os.path.join(char_dir, "_default.txt")
                    default_angle = ""
                    if os.path.exists(default_marker):
                        with open(default_marker) as df:
                            default_angle = df.read().strip()
                    is_default = (angle_file == default_angle)
                    if st.button(
                        "⭐ 默认" if is_default else "设为默认",
                        key=f"def_{char_name}_{angle_file}",
                        use_container_width=True,
                    ):
                        with open(default_marker, "w") as df:
                            df.write(angle_file)
                        st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            with st.expander("重新生成"):
                appearance = st.text_area("外貌描述", key=f"app_{char_name}", height=68)
                if st.button("重新生成", key=f"regen_{char_name}"):
                    with st.spinner(f"正在生成 {char_name}..."):
                        subprocess.run([
                            sys.executable, "pipeline/illustrator.py", "generate-character",
                            "--name", char_name, "--appearance", appearance,
                            "--output", char_dir, "--config", "config.yaml",
                        ], check=False)
                    st.rerun()
        st.divider()

with tab2:
    st.subheader("配音试听")
    outputs_dir = "outputs"
    if os.path.exists(outputs_dir):
        for proj in sorted(os.listdir(outputs_dir)):
            proj_path = os.path.join(outputs_dir, proj)
            wav_files = []
            for root, dirs, files in os.walk(proj_path):
                for f in files:
                    if f.endswith(".wav"):
                        wav_files.append(os.path.join(root, f))
            if wav_files:
                st.markdown(f"**{proj}**")
                for wf in sorted(wav_files):
                    shot_name = os.path.basename(os.path.dirname(wf))
                    st.caption(f"{shot_name}/{os.path.basename(wf)}")
                    st.audio(wf)
    else:
        st.info("暂无输出文件")
