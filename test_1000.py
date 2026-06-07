import random
import numpy as np
import time
from sentence_transformers import SentenceTransformer
from categories import CATEGORY_DESCRIPTIONS, CATEGORY_SYNONYMS

# 1. 쿼리 생성기 (Query Generator)
PREFIXES = ["", "비오는 날 ", "스트레스 받을 때 ", "친구들이랑 ", "여자친구랑 ", "혼자 ", "가족들이랑 ", "회식으로 ", "우울할 때 ", "밤늦게 "]
ADJECTIVES = ["", "조용한 ", "가성비 좋은 ", "분위기 좋은 ", "매운 ", "달달한 ", "넓은 ", "깨끗한 ", "사진 찍기 좋은 ", "힙한 ", "전망 좋은 "]
TARGETS = [
    "카페", "커피", "디저트", "노래방", "코노", "피시방", "피방", "당구장", "볼링장", 
    "공원", "산책", "고기", "삼겹살", "소고기", "국밥", "치킨", "피자", "파스타", "스테이크",
    "맥주", "소주", "와인", "막걸리", "칵테일", "책", "서점", "머리 자르기", "미용실", "네일아트",
    "마사지", "목욕탕", "영화관", "방탈출", "보드게임", "호텔", "모텔", "펜션", "빵", "아이스크림"
]
SUFFIXES = [" 가고 싶어", " 어디가 좋을까?", " 추천해줘", " 찾아줘", " 땡긴다", " 갈래", ""]

random.seed(42)
all_combinations = []
for p in PREFIXES:
    for a in ADJECTIVES:
        for t in TARGETS:
            for s in SUFFIXES:
                all_combinations.append(f"{p}{a}{t}{s}".strip())

# 랜덤하게 1000개 추출
test_queries = random.sample(all_combinations, 1000)

print(f"✅ Generated {len(test_queries)} test queries.")
print("Example:", test_queries[:5])

# 2. 모델 로드 및 임베딩
print("Loading Model...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask', device='cpu')

cat_names = list(CATEGORY_DESCRIPTIONS.keys())
print(f"Encoding {len(cat_names)} Categories...")
cat_embs = model.encode([CATEGORY_DESCRIPTIONS[c] for c in cat_names], convert_to_numpy=True, normalize_embeddings=True)

print("Encoding 1000 Queries...")
q_embs = model.encode(test_queries, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)

# 3. 평가
THRESHOLD = 0.35

failed_queries = []
borderline_queries = []
high_confidence_queries = []

for idx, query in enumerate(test_queries):
    q_emb = q_embs[idx]
    query_lower = query.lower()
    
    # Synonym check
    syn_matched = False
    for cat_name, synonyms in CATEGORY_SYNONYMS.items():
        valid_keywords = synonyms + [cat_name.lower()]
        if any(syn in query_lower for syn in valid_keywords):
            syn_matched = True
            break
            
    if syn_matched:
        high_confidence_queries.append((query, "SYNONYM_MATCH", 1.0))
        continue
        
    # AI similarity check
    scores = np.dot(cat_embs, q_emb.T).squeeze()
    max_idx = np.argmax(scores)
    max_score = float(scores[max_idx])
    max_cat = cat_names[max_idx]
    
    if max_score < THRESHOLD:
        failed_queries.append((query, max_cat, max_score))
    elif max_score < 0.45:
        borderline_queries.append((query, max_cat, max_score))
    else:
        high_confidence_queries.append((query, max_cat, max_score))

print("\n" + "="*50)
print(f"📊 1000 Test Results (Threshold: {THRESHOLD})")
print("="*50)
print(f"✅ Pass (High Confidence > 0.45 or Synonym): {len(high_confidence_queries)}")
print(f"⚠️ Borderline (0.35 ~ 0.45): {len(borderline_queries)}")
print(f"❌ Fail (< 0.35): {len(failed_queries)}")

print("\n🔴 [Coverage Holes] Top Failed Queries (AI couldn't map these well):")
failed_queries.sort(key=lambda x: x[2]) # Sort by lowest score
for q, cat, score in failed_queries[:15]:
    print(f"  - '{q}' -> Best match was '{cat}' (Score: {score:.3f})")

print("\n🟡 [Borderline] Needs monitoring:")
for q, cat, score in borderline_queries[:10]:
    print(f"  - '{q}' -> Matched '{cat}' (Score: {score:.3f})")
    
# Save detailed report
with open("test_1000_report.txt", "w", encoding="utf-8") as f:
    f.write(f"Total Queries: {len(test_queries)}\n")
    f.write(f"Fails: {len(failed_queries)}\n\n")
    for q, cat, score in failed_queries:
        f.write(f"FAIL: '{q}' -> {cat} ({score:.3f})\n")
