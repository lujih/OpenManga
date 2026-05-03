import os
import streamlit as st

st.title("🏠 项目管理")

outputs_dir = "outputs"
os.makedirs(outputs_dir, exist_ok=True)
projects = sorted([d for d in os.listdir(outputs_dir) if os.path.isdir(os.path.join(outputs_dir, d))])

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("已有项目")
    if not projects:
        st.info("暂无项目，创建一个吧")
    for proj in projects:
        proj_path = os.path.join(outputs_dir, proj)
        screenplay_path = os.path.join(proj_path, "screenplay.json")
        has_screenplay = os.path.exists(screenplay_path)
        status = "📜 有剧本" if has_screenplay else "📭 空项目"

        if st.button(f"{proj}  {status}", key=f"proj_{proj}", use_container_width=True):
            st.session_state.project = proj
            st.switch_page("pages/03_dashboard.py")

with col2:
    st.subheader("新建项目")
    new_name = st.text_input("项目名", placeholder="my_project")
    default_styles = ["赛博朋克", "写实", "电影感", "二次元", "水墨风"]
    new_style = st.selectbox("风格预设", default_styles)
    if st.button("创建项目", type="primary", use_container_width=True):
        if new_name:
            new_dir = os.path.join(outputs_dir, new_name)
            os.makedirs(new_dir, exist_ok=True)
            with open(os.path.join(new_dir, "style.txt"), "w") as f:
                f.write(new_style)
            st.success(f"项目 `{new_name}` 已创建")
            st.session_state.project = new_name
            st.rerun()
        else:
            st.warning("请输入项目名")
