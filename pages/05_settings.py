import os
import streamlit as st
import yaml

st.title("⚙️ 设置")

config_path = "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

st.subheader("API Key 配置")

providers = {
    "image_generation": "图像生成",
    "video_generation": "视频生成",
    "tts": "语音合成",
    "llm": "大语言模型",
}

saved = False
for key, label in providers.items():
    section = config.get(key, {})
    with st.expander(f"{label} ({section.get('provider', 'N/A')})"):
        new_key = st.text_input(
            "API Key",
            value=section.get("api_key", ""),
            type="password",
            key=f"key_{key}",
            placeholder=f"输入 {key} 的 API Key",
        )
        new_model = st.text_input(
            "模型",
            value=section.get("model", ""),
            key=f"model_{key}",
        )
        if new_key != section.get("api_key") or new_model != section.get("model"):
            config[key]["api_key"] = new_key
            config[key]["model"] = new_model
            saved = True

if saved and st.button("💾 保存设置", type="primary"):
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    st.success("设置已保存到 config.yaml")
    st.rerun()

st.divider()
st.subheader("关于")
st.markdown("""
**OpenManga** · 全AI生成式漫剧工厂

[GitHub](https://github.com) · v0.1.0
""")
