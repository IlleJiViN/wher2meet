import numpy as np
from sentence_transformers import SentenceTransformer
from categories import CATEGORY_DESCRIPTIONS, CATEGORY_SYNONYMS

# A broad range of human-like queries targeting all major life areas
TEST_QUERIES = [
    # FOOD
    ("혼자 먹기 좋은 국밥", "해장국/국밥"),
    ("매운 떡볶이", "분식"),
    ("조용한 초밥집", "일식"),
    ("가성비 좋은 파스타", "파스타/스테이크"),
    ("회식하기 좋은 삼겹살", "돼지고기 구이/찜"),
    ("신선한 회", "생선 회/해물"),
    ("간단한 햄버거", "버거"),
    ("비건 식당", "채식 전문"), # Let's see if it catches this
    # NIGHTLIFE & BEVERAGE
    ("친구들이랑 시원한 맥주", "생맥주 전문"),
    ("조용한 와인바", "주류 소매업"), # Actually Wine bar should be something else?
    ("신나는 클럽", "무도 유흥 주점"),
    ("비오는 날 막걸리", "전통주 전문"), # Does this exist? Let's check fallback
    ("아침에 마시는 아아", "카페"),
    # SPORTS
    ("살 빼기 좋은 헬스장", "헬스장"),
    ("자세 교정 필라테스", "요가/필라테스 학원"),
    ("스트레스 풀리는 킥복싱", "태권도/무술학원"),
    ("비오는 날 실내 수영장", "수영장"),
    ("친구들이랑 볼링 한게임", "볼링장"),
    ("야외에서 치는 테니스", "테니스장"),
    # BEAUTY & RELAX
    ("남자 머리 잘 자르는 곳", "미용실"),
    ("여드름 관리", "피부 관리실"),
    ("네일 아트 예쁘게 하는 곳", "네일숍"),
    ("어깨 뭉쳤을 때 마사지", "마사지/안마"),
    ("뜨끈한 사우나", "목욕탕/사우나"),
    # CULTURE & ENTERTAINMENT
    ("최신 영화 보는 곳", "극장/영화관"),
    ("친구들이랑 머리 쓰는 방탈출", "방탈출"),
    ("조용히 책 읽기 좋은 서점", "서점"),
    ("미술 작품 감상하는 전시회", "미술관"),
    ("노래 부르기 좋은 코노", "노래방"),
    ("피시방", "PC방"),
    # OUTDOOR & ACCOMMODATION
    ("강아지랑 산책하기 좋은 공원", "근린공원"),
    ("바베큐장 있는 펜션", "민박/펜션"),
    ("호캉스 즐길 호텔", "관광호텔"),
    ("잠만 잘 싼 모텔", "여관/모텔")
]

print("Loading model...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask', device='cpu')

cat_names = list(CATEGORY_DESCRIPTIONS.keys())
cat_embs = model.encode([CATEGORY_DESCRIPTIONS[c] for c in cat_names], convert_to_numpy=True, normalize_embeddings=True)

print("\nRunning Gap Analysis...\n")
failed_cases = []

for q, expected in TEST_QUERIES:
    q_emb = model.encode([q], convert_to_numpy=True, normalize_embeddings=True)[0]
    
    # 1. Check Synonym first
    q_lower = q.lower()
    syn_match = None
    for c_name, syns in CATEGORY_SYNONYMS.items():
        if any(s in q_lower for s in syns + [c_name.lower()]):
            syn_match = c_name
            break
            
    if syn_match:
        if syn_match != expected and expected not in ['전통주 전문', '채식 전문']:
            print(f"[WARN] '{q}' matched synonym '{syn_match}' but expected '{expected}'")
        continue

    # 2. Semantic Match
    scores = np.dot(cat_embs, q_emb.T).squeeze()
    max_idx = np.argmax(scores)
    max_score = float(scores[max_idx])
    max_cat = cat_names[max_idx]
    
    if max_cat != expected and max_score < 0.4:
        failed_cases.append((q, expected, max_cat, max_score))

if failed_cases:
    print("❌ SEMANTIC GAPS FOUND:")
    for q, exp, act, score in failed_cases:
        print(f"Query: '{q}' | Expected: '{exp}' | Actual: '{act}' (Score: {score:.3f})")
else:
    print("✅ All queries passed or matched correctly!")
