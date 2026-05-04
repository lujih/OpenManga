import streamlit as st

st.set_page_config(page_title="OpenManga", page_icon="🎬", layout="wide")

st.title("OpenManga · 漫剧工厂")
st.markdown("全AI生成式漫剧创作平台")

if "project" not in st.session_state:
    st.session_state.project = None

pg = st.navigation({
    "创作": [
        st.Page("OpenManga/pages/01_projects.py", title="项目管理", icon="🏠"),
        st.Page("OpenManga/pages/02_screenplay.py", title="剧本工作室", icon="✍️"),
        st.Page("OpenManga/pages/03_dashboard.py", title="制作看板", icon="🎬"),
    ],
    "资源": [
        st.Page("OpenManga/pages/04_assets.py", title="资产库", icon="🖼️"),
        st.Page("OpenManga/pages/05_settings.py", title="设置", icon="⚙️"),
    ],
})
pg.run()
