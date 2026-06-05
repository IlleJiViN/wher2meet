import sys
content = open("/home/dev/AI/test/code.py").read()

# Add translation keys for engine
old_t = '        "sim_help": "낮음 = 폭넓은 검색, 높음 = 엄격한 의미 일치",'
new_t = '        "sim_help": "낮음 = 폭넓은 검색, 높음 = 엄격한 의미 일치",\n        "engine": "AI 엔진 버전",\n        "engine_help": "테스트할 양자화 버전을 선택하세요.",'
content = content.replace(old_t, new_t)

old_t_en = '        "sim_help": "Lower = broader matches, Higher = stricter semantic matches.",'
new_t_en = '        "sim_help": "Lower = broader matches, Higher = stricter semantic matches.",\n        "engine": "AI Engine Version",\n        "engine_help": "Select quantization version to test.",'
content = content.replace(old_t_en, new_t_en)

# Add selectbox in UI
old_sim = 'st.slider(t("sim_thresh"), 0.0, 1.0, 0.15, 0.05, help=t("sim_help"))'
new_sim = 'st.slider(t("sim_thresh"), 0.0, 1.0, 0.15, 0.05, help=t("sim_help"))\n    engine_version = st.selectbox(t("engine"), ["v4 (Float32 원본)", "v5 (INT8 양자화 모델)", "v6 (Float16 DB 압축)"], index=1, help=t("engine_help"))'
content = content.replace(old_sim, new_sim)

# Update payload in search_destinations
old_payload = '        payload = {\n            "query": keyword,\n            "users": [{"name": name, "latitude": coords[0], "longitude": coords[1]} for name, coords in origin_data],\n            "radius_meters": float(radius),\n            "similarity_threshold": similarity_threshold,\n            "top_k": 15\n        }'
new_payload = '        payload = {\n            "query": keyword,\n            "users": [{"name": name, "latitude": coords[0], "longitude": coords[1]} for name, coords in origin_data],\n            "radius_meters": float(radius),\n            "similarity_threshold": similarity_threshold,\n            "top_k": 15,\n            "engine_version": "v6" if "v6" in st.session_state.get("engine_version", "v5") else ("v4" if "v4" in st.session_state.get("engine_version", "v5") else "v5")\n        }'
content = content.replace(old_payload, new_payload)

# Ensure engine_version is passed properly by storing it in session state first
old_search_btn = '    search_btn = st.button(t("calc_rank"), type="primary", use_container_width=True)'
new_search_btn = '    st.session_state.engine_version = engine_version\n    search_btn = st.button(t("calc_rank"), type="primary", use_container_width=True)'
content = content.replace(old_search_btn, new_search_btn)

open("/home/dev/AI/test/code.py", "w").write(content)
