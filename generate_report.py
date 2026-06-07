import numpy as np
from sentence_transformers import SentenceTransformer
from categories import CATEGORY_DESCRIPTIONS

TEST_QUERIES = [
    # 식음료
    "비오는 날 먹기 좋은 뜨끈한 국밥",
    "스트레스 풀리는 엄청 매운 떡볶이",
    "데이트하기 좋은 조용한 파스타집",
    "혼자 가서 먹기 편한 가성비 햄버거",
    "회식하기 좋은 넓은 삼겹살 고깃집",
    "퇴근 후 친구랑 시원한 생맥주 한잔",
    # 카페/디저트
    "노트북하기 좋은 콘센트 많은 카페",
    "달달한 케이크랑 마카롱 파는 곳",
    # 스포츠/액티비티
    "다이어트하려고 끊을 헬스장",
    "자세 교정되는 기구 필라테스",
    "실내에서 치는 테니스장",
    "친구들이랑 신나게 치는 볼링장",
    # 유흥/엔터
    "최신 노래 부르기 좋은 코노",
    "머리 쓰는 재미있는 방탈출",
    "게임하기 좋은 최고사양 피시방",
    "밤새 놀기 좋은 클럽",
    # 문화/휴식
    "조용히 미술 작품 감상하는 전시회",
    "베스트셀러 책 읽기 좋은 조용한 서점",
    "강아지 데리고 걷기 좋은 산책로",
    # 뷰티/건강
    "남자 머리 펌 잘하는 미용실",
    "어깨 뭉쳤을 때 풀어주는 타이 마사지",
    "여드름 피부 관리해주는 에스테틱",
    # 숙박
    "잠만 자고 나올 싼 모텔",
    "수영장 있는 럭셔리 호캉스 호텔",
    "가족끼리 고기 구워 먹는 글램핑 펜션"
]

print("Loading model...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask', device='cpu')

cat_names = list(CATEGORY_DESCRIPTIONS.keys())
cat_embs = model.encode([CATEGORY_DESCRIPTIONS[c] for c in cat_names], convert_to_numpy=True, normalize_embeddings=True)

q_embs = model.encode(TEST_QUERIES, convert_to_numpy=True, normalize_embeddings=True)

report_lines = []
report_lines.append("# 🎯 Semantic Search AI Performance Report")
report_lines.append("본 보고서는 최신 `jhgan/ko-sroberta-multitask` 모델을 기반으로 한 86개 카테고리의 의미론적(Semantic) 매칭 결과를 보여줍니다. (사전 우선순위(Synonym) 로직을 제외한 **순수 AI 임베딩 유사도** 기준 1~3위입니다.)\n")

for idx, q in enumerate(TEST_QUERIES):
    q_emb = q_embs[idx]
    scores = np.dot(cat_embs, q_emb.T).squeeze()
    
    # Get top 3 indices
    top3_idx = np.argsort(scores)[::-1][:3]
    
    report_lines.append(f"### Q{idx+1}. `{q}`")
    for rank, i in enumerate(top3_idx):
        cat = cat_names[i]
        score = scores[i]
        icon = "🥇" if rank == 0 else ("🥈" if rank == 1 else "🥉")
        report_lines.append(f"- {icon} **{cat}** (유사도: `{score:.3f}`)")
    report_lines.append("")

with open("report_output.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print("Report generated at report_output.md")
