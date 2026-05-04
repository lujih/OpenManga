import os
import copy
import streamlit as st
import yaml

st.title("⚙️ 设置")

config_path = "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

st.subheader("API 密钥配置")

PROVIDER_LABELS = {
    "image_generation": "图像生成",
    "video_generation": "视频生成",
    "tts": "语音合成",
    "llm": "大语言模型",
}

saved = False
for key, section in config.items():
    label = PROVIDER_LABELS.get(key, key)
    current_provider = section.get("provider", "未设置") if isinstance(section, dict) else "未设置"
    with st.expander(f"{label}（{current_provider}）"):
        if not isinstance(section, dict):
            st.warning("配置格式错误，请检查 config.yaml")
            continue
        new_provider = st.text_input(
            "提供商",
            value=section.get("provider", ""),
            key=f"provider_{key}",
        )
        new_model = st.text_input(
            "模型",
            value=section.get("model", ""),
            key=f"model_{key}",
        )
        new_key = st.text_input(
            "API 密钥",
            value=section.get("api_key", ""),
            type="password",
            key=f"key_{key}",
        )
        new_api_base = st.text_input(
            "API 地址",
            value=section.get("api_base", ""),
            key=f"api_base_{key}",
            placeholder="留空使用默认端点",
        )
        if section.get("api_base") != new_api_base:
            config[key]["api_base"] = new_api_base
            saved = True

        sub_params = section.get("params", {})
        if sub_params:
            st.caption("模型参数")
            for pk, pv in sub_params.items():
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.text(pk)
                with col_b:
                    if isinstance(pv, bool):
                        new_val = st.checkbox("", value=pv, key=f"param_{key}_{pk}")
                    elif isinstance(pv, (int, float)):
                        new_val = st.number_input("", value=pv, key=f"param_{key}_{pk}", label_visibility="collapsed")
                    elif isinstance(pv, list):
                        new_val = st.text_input("", value=str(pv), key=f"param_{key}_{pk}", label_visibility="collapsed")
                    else:
                        new_val = st.text_input("", value=str(pv) if pv is not None else "", key=f"param_{key}_{pk}", label_visibility="collapsed")
                    if new_val != pv:
                        config[key].setdefault("params", {})[pk] = new_val
                        saved = True

        for field, new_val in [("provider", new_provider), ("model", new_model), ("api_key", new_key)]:
            if section.get(field) != new_val:
                config[key][field] = new_val
                saved = True

st.divider()
st.subheader("添加提供商")
new_section = st.text_input("提供商标识（如 sound_effects）", placeholder="sound_effects")
new_label = st.text_input("中文名称（可选）", placeholder="音效生成")
if st.button("➕ 添加", use_container_width=True):
    if new_section and new_section not in config:
        config[new_section] = {"provider": "", "model": "", "api_key": ""}
        if new_label:
            PROVIDER_LABELS[new_section] = new_label
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        st.success(f"已添加 `{new_section}`")
        st.rerun()
    elif new_section in config:
        st.warning("该标识已存在")

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
