import numpy as np
from sentence_transformers import SentenceTransformer
import time
from categories import CATEGORY_DESCRIPTIONS, CATEGORY_SYNONYMS

# ==============================================================================
# 1. 100 Test Cases
# Format: (Query, [Expected Categories])
# ==============================================================================
TEST_CASES = [
    # --- Synonym & Slang ---
    ("피방", ["PC방"]),
    ("피시방", ["PC방"]),
    ("게임방", ["PC방"]),
    ("겜방", ["PC방"]),
    ("헬스", ["헬스장"]),
    ("운동", ["헬스장"]),
    ("웨이트", ["헬스장"]),
    ("코노", ["노래방"]),
    ("코인노래방", ["노래방"]),
    ("머리 자르러", ["미용실"]),
    ("파마", ["미용실"]),
    ("염색", ["미용실"]),
    ("카페", ["카페"]),
    ("디저트", ["카페"]),
    ("커피", ["카페"]),
    ("햄버거", ["버거"]),
    ("수제버거", ["버거"]),

    # --- Short Direct Categories ---
    ("치킨", ["치킨"]),
    ("피자", ["피자"]),
    ("중국집", ["중국집"]),
    ("짜장면", ["중국집"]),
    ("짬뽕", ["중국집"]),
    ("초밥", ["일식 회/초밥"]),
    ("스시", ["일식 회/초밥"]),
    ("돈가스", ["일식 카레/돈가스/덮밥"]),
    ("삼겹살", ["돼지고기 구이/찜"]),
    ("소고기", ["소고기 구이/찜"]),
    ("곱창", ["곱창 전골/구이"]),
    ("횟집", ["횟집"]),
    ("국밥", ["국/탕/찌개류"]),
    ("떡볶이", ["김밥/만두/분식"]),
    ("김밥", ["김밥/만두/분식"]),
    ("백반", ["백반/한정식"]),
    ("칼국수", ["국수/칼국수"]),
    ("냉면", ["냉면/밀면"]),
    ("파전", ["전/부침개"]),
    ("마카롱", ["빵/도넛", "카페"]),
    ("아이스크림", ["아이스크림/빙수"]),

    # --- Descriptive / Long Queries ---
    ("조용하게 책 읽기 좋은 곳", ["서점", "독서실/스터디 카페", "카페"]),
    ("분위기 좋은 레스토랑", ["파스타/스테이크", "기타 서양식 음식점"]),
    ("가볍게 산책할래", ["근린공원", "소공원", "수변공원", "가로공원", "역사공원", "체육공원", "기타공원"]),
    ("친구들이랑 술 한잔", ["요리 주점", "생맥주 전문", "일반 유흥 주점"]),
    ("가족끼리 외식하기 좋은 고기집", ["돼지고기 구이/찜", "소고기 구이/찜", "오리고기"]),
    ("데이트하기 좋은 파스타집", ["파스타/스테이크"]),
    ("혼자 밥먹기 좋은 식당", ["백반/한정식", "김밥/만두/분식", "일식 카레/돈가스/덮밥"]),
    ("비오는 날 막걸리", ["전/부침개", "요리 주점"]),
    ("매운 음식 땡길 때", ["닭/오리고기 구이/찜", "해산물 구이/찜", "중국집", "곱창 전골/구이"]),
    ("밤 늦게 여는 술집", ["요리 주점", "생맥주 전문", "일반 유흥 주점", "주류 소매업"]),
    ("아이들 데리고 갈만한 공원", ["어린이공원", "주제공원", "근린공원"]),
    ("연인과 분위기 잡기 좋은 와인바", ["파스타/스테이크", "요리 주점", "주류 소매업"]),

    # --- Activity & Entertainment ---
    ("영화관", ["기타"]),  # If not specifically mapped, "기타" or something
    ("보드게임", ["카페", "기타"]),
    ("방탈출", ["전자 게임장", "기타"]),
    ("당구 한게임", ["당구장"]),
    ("탁구 치러 가자", ["탁구장"]),
    ("볼링장", ["볼링장"]),
    ("스크린골프", ["골프 연습장"]),
    ("테니스 랠리", ["테니스장"]),
    ("배드민턴 치자", ["종합 스포츠시설", "체육공원"]),
    ("수영 마스터", ["수영장"]),
    ("클라이밍", ["기타 스포츠시설 운영업"]),
    ("필라테스", ["요가/필라테스 학원"]),
    ("요가", ["요가/필라테스 학원"]),
    ("마사지 시원하게", ["마사지/안마"]),
    ("네일 아트", ["네일숍"]),
    ("피부 관리", ["피부 관리실", "체형/비만 관리"]),
    ("찜질방", ["목욕탕/사우나"]),
    ("사우나", ["목욕탕/사우나"]),

    # --- Multi-intent & Hard ---
    ("치맥", ["치킨", "생맥주 전문"]),
    ("피맥", ["피자", "생맥주 전문"]),
    ("소주에 삼겹살", ["돼지고기 구이/찜", "요리 주점"]),
    ("공부하기 좋은 조용한 카페", ["독서실/스터디 카페", "카페"]),
    ("맛있는 수제버거랑 감자튀김", ["버거", "그 외 기타 간이 음식점"]),
    ("매콤한 낙지볶음", ["기타 한식 음식점", "해산물 구이/찜"]),
    ("시원한 밀면", ["냉면/밀면"]),

    # --- Negative / Noise (Should yield empty or highly generic) ---
    ("아무거나", []),
    ("asdf", []),
    ("1234", []),
    ("어디든", [])
]

# Initialize Model
print("Loading Model...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask', device='cpu')

category_names = list(CATEGORY_DESCRIPTIONS.keys())
category_texts = list(CATEGORY_DESCRIPTIONS.values())
print("Encoding Categories...")
category_vectors = model.encode(category_texts, convert_to_numpy=True, normalize_embeddings=True)

# Function to simulate matching
def simulate_search(query, threshold):
    matched = []
    
    # 1. Synonym Bypass
    query_lower = query.lower()
    for cat_name, synonyms in CATEGORY_SYNONYMS.items():
        valid_keywords = synonyms + [cat_name.lower()]
        if any(syn in query_lower for syn in valid_keywords):
            if cat_name not in matched:
                matched.append(cat_name)
    
    # 2. Semantic Search
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores = np.dot(category_vectors, q_emb.T).squeeze()
    
    # Extract passing categories
    for i, score in enumerate(scores):
        if score >= threshold and category_names[i] not in matched:
            matched.append(category_names[i])
            
    return matched

thresholds_to_test = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]

print("\n🚀 Starting Grid Search...")

best_f1 = 0
best_thresh = 0
results_summary = []

for thresh in thresholds_to_test:
    total_queries = len(TEST_CASES)
    passed_cases = 0
    total_noise_matched = 0 # Count how many irrelevant categories were returned
    
    for query, expected_list in TEST_CASES:
        matched = simulate_search(query, thresh)
        
        # Scoring logic
        if not expected_list: # Negative cases
            if len(matched) <= 2:
                passed_cases += 1
            else:
                total_noise_matched += len(matched)
        else:
            # Positive cases: At least one expected category MUST be in the matched list
            hit = any(e in matched for e in expected_list)
            if hit:
                passed_cases += 1
                # Penalize if it matched way too many irrelevant things
                noise_count = len([m for m in matched if m not in expected_list])
                total_noise_matched += noise_count
            else:
                total_noise_matched += len(matched)
                
    accuracy = passed_cases / total_queries
    avg_noise = total_noise_matched / total_queries
    
    # F1 proxy: Balance Accuracy and inversely proportional Noise
    # Let's say we want accuracy > 0.85, and lowest noise possible
    print(f"[Threshold {thresh:.2f}] Accuracy: {accuracy*100:.1f}% ({passed_cases}/{total_queries}) | Avg Noise/Query: {avg_noise:.1f}")
    
    results_summary.append({
        'thresh': thresh,
        'accuracy': accuracy,
        'noise': avg_noise
    })

print("\n🎯 Detailed Evaluation of Best Candidate (0.35):")
failed_cases = []
for query, expected in TEST_CASES:
    matched = simulate_search(query, 0.35)
    if expected:
        hit = any(e in matched for e in expected)
        if not hit:
            failed_cases.append((query, expected, matched))

for q, e, m in failed_cases[:10]:
    print(f"  ❌ FAIL: '{q}' -> Expected: {e}, Got: {m[:3]}...")
