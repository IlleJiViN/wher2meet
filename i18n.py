import sys

content = open("/home/dev/AI/test/code.py").read()

t_code = """
if "lang" not in st.session_state:
    st.session_state.lang = "한국어"

T = {
    "English": {
        "title": "🗺️ Multi-Origin Routing & Fair Meetup App",
        "subtitle": "Find the most fair and optimal meeting spots for multiple starting locations.",
        "step1": "1. Starting Points",
        "enter_origin": "Enter an origin address:",
        "add_origin": "Add Origin",
        "finding_addr": "Finding address...",
        "addr_not_found": "Address not found.",
        "origin_list": "### Origin List",
        "step2": "2. Search Destination",
        "ai_active": "🤖 **SpotSync AI Local Semantic Search is active!** Enter any natural language search intent:",
        "search_intent": "Search Intent (e.g., '노트북 하기 좋은 카페', '방음 합주실'):",
        "sim_thresh": "AI Similarity Threshold",
        "sim_help": "Lower = broader matches, Higher = stricter semantic matches.",
        "calc_rank": "Calculate & Rank",
        "need_origin": "👈 Please add at least one starting point from the sidebar to begin.",
        "searching": "Searching for '{}' near the center point...",
        "no_dest": "No destinations found for '{}'. Try a different keyword.",
        "calc_routes": "Calculating routes...",
        "routing_to": "Routing to {}...",
        "ranked_overview": "📊 Ranked Candidate Locations Overview",
        "rank": "Rank",
        "name": "Name",
        "addr": "Address",
        "total_dist": "Total Dist (km)",
        "fairness": "Fairness Variance (km)",
        "interactive_map": "Interactive Map",
        "top_ranked": "Top Ranked Locations",
        "route_from": "Route from {}",
        "top_pick": "★ Top Pick: {}",
        "candidate": "Candidate: {}"
    },
    "한국어": {
        "title": "🗺️ 다중 출발지 최적 모임 장소 찾기",
        "subtitle": "여러 명의 출발 위치를 기반으로 가장 공평하고 최적화된 모임 장소를 찾아보세요.",
        "step1": "1. 출발지 설정",
        "enter_origin": "출발지 주소를 입력하세요:",
        "add_origin": "출발지 추가",
        "finding_addr": "주소 검색 중...",
        "addr_not_found": "주소를 찾을 수 없습니다.",
        "origin_list": "### 출발지 목록",
        "step2": "2. 목적지 검색",
        "ai_active": "🤖 **SpotSync AI 로컬 시맨틱 검색이 켜져 있습니다!** 자연어로 원하는 장소를 검색하세요:",
        "search_intent": "검색어 (예: '노트북 하기 좋은 카페', '방음 합주실'):",
        "sim_thresh": "AI 유사도 임계치",
        "sim_help": "낮음 = 폭넓은 검색, 높음 = 엄격한 의미 일치",
        "calc_rank": "계산 및 순위 매기기",
        "need_origin": "👈 시작하려면 사이드바에서 최소 하나 이상의 출발지를 추가해 주세요.",
        "searching": "중심점 근처에서 '{}' 검색 중...",
        "no_dest": "'{}'에 대한 목적지를 찾을 수 없습니다. 다른 검색어를 시도해 보세요.",
        "calc_routes": "경로 계산 중...",
        "routing_to": "{}까지 경로 계산 중...",
        "ranked_overview": "📊 추천 목적지 순위 요약",
        "rank": "순위",
        "name": "이름",
        "addr": "주소",
        "total_dist": "총 이동 거리 (km)",
        "fairness": "거리 편차 (km)",
        "interactive_map": "인터랙티브 지도",
        "top_ranked": "최상위 추천 장소",
        "route_from": "출발지: {}",
        "top_pick": "★ 1위 추천: {}",
        "candidate": "후보 장소: {}"
    }
}

def t(key):
    return T[st.session_state.lang][key]
"""

content = content.replace('st.title("🗺️ Multi-Origin Routing & Fair Meetup App")', t_code + '\nst.title(t("title"))')
content = content.replace('st.markdown("Find the most fair and optimal meeting spots for multiple starting locations.")', 'st.markdown(t("subtitle"))')

content = content.replace('with st.sidebar:', 'with st.sidebar:\n    st.session_state.lang = st.radio("Language / 언어", ["한국어", "English"], index=0 if st.session_state.lang == "한국어" else 1)')

content = content.replace('st.header("1. Starting Points")', 'st.header(t("step1"))')
content = content.replace('st.text_input("Enter an origin address:")', 'st.text_input(t("enter_origin"))')
content = content.replace('st.form_submit_button("Add Origin")', 'st.form_submit_button(t("add_origin"))')
content = content.replace('st.spinner("Finding address...")', 'st.spinner(t("finding_addr"))')
content = content.replace('st.error("Address not found.")', 'st.error(t("addr_not_found"))')
content = content.replace('st.write("### Origin List")', 'st.write(t("origin_list"))')

content = content.replace('st.header("2. Search Destination")', 'st.header(t("step2"))')
content = content.replace('st.markdown("🤖 **SpotSync AI Local Semantic Search is active!** Enter any natural language search intent:")', 'st.markdown(t("ai_active"))')
content = content.replace('st.text_input("Search Intent (e.g., \'노트북 하기 좋은 카페\', \'방음 합주실\'):")', 'st.text_input(t("search_intent"))')
content = content.replace('st.slider("AI Similarity Threshold", 0.0, 1.0, 0.15, 0.05,\n                                    help="Lower = broader matches, Higher = stricter semantic matches.")', 'st.slider(t("sim_thresh"), 0.0, 1.0, 0.15, 0.05, help=t("sim_help"))')
content = content.replace('st.button("Calculate & Rank", type="primary", use_container_width=True)', 'st.button(t("calc_rank"), type="primary", use_container_width=True)')

content = content.replace('st.info("👈 Please add at least one starting point from the sidebar to begin.")', 'st.info(t("need_origin"))')
content = content.replace('st.spinner(f"Searching for \'{keyword}\' near the center point...")', 'st.spinner(t("searching").format(keyword))')
content = content.replace('st.error(f"No destinations found for \'{keyword}\'. Try a different keyword.")', 'st.error(t("no_dest").format(keyword))')
content = content.replace('progress_text = "Calculating routes..."', 'progress_text = t("calc_routes")')
content = content.replace('text=f"Routing to {dest[\'name\']}..."', 'text=t("routing_to").format(dest["name"])')

content = content.replace('st.subheader("📊 Ranked Candidate Locations Overview")', 'st.subheader(t("ranked_overview"))')
content = content.replace('"Rank": i + 1', 't("rank"): i + 1')
content = content.replace('"Name": res["name"]', 't("name"): res["name"]')
content = content.replace('"Address": res["address"]', 't("addr"): res["address"]')
content = content.replace('"Total Dist (km)": round(res["total_dist"] / 1000, 2)', 't("total_dist"): round(res["total_dist"] / 1000, 2)')
content = content.replace('"Fairness Variance (km)": round(res["fairness"] / 1000, 2)', 't("fairness"): round(res["fairness"] / 1000, 2)')
content = content.replace('df = pd.DataFrame(df_data).set_index("Rank")', 'df = pd.DataFrame(df_data).set_index(t("rank"))')

content = content.replace('st.subheader("Interactive Map")', 'st.subheader(t("interactive_map"))')
content = content.replace('tooltip=f"★ Top Pick: {top_dest[\'name\']}"', 'tooltip=t("top_pick").format(top_dest["name"])')
content = content.replace('tooltip=f"Candidate: {res[\'name\']}"', 'tooltip=t("candidate").format(res["name"])')
content = content.replace('tooltip=f"Route from {route_info[\'name\']}"', 'tooltip=t("route_from").format(route_info["name"])')

content = content.replace('st.subheader("Top Ranked Locations")', 'st.subheader(t("top_ranked"))')

open("/home/dev/AI/test/code.py", "w").write(content)
print("Modifications applied locally.")
