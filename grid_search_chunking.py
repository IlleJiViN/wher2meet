import numpy as np
from sentence_transformers import SentenceTransformer
import time
from categories import CATEGORY_DESCRIPTIONS, CATEGORY_SYNONYMS

TEST_CASES = [
    # --- Synonym & Slang ---
    ("피방", ["PC방"]),
    ("운동", ["헬스장"]),
    ("코노", ["노래방"]),
    ("파마", ["미용실"]),
    ("카페", ["카페"]),
    ("수제버거", ["버거"]),
    ("치킨", ["치킨"]),
    ("짜장면", ["중국집"]),
    ("초밥", ["일식 회/초밥"]),
    ("삼겹살", ["돼지고기 구이/찜"]),
    ("곱창", ["곱창 전골/구이"]),
    ("떡볶이", ["김밥/만두/분식"]),
    ("마카롱", ["빵/도넛", "카페"]),
    
    # --- Descriptive / Long Queries ---
    ("조용하게 책 읽기 좋은 곳", ["서점", "독서실/스터디 카페", "카페"]),
    ("분위기 좋은 레스토랑", ["파스타/스테이크", "기타 서양식 음식점"]),
    ("가볍게 산책할래", ["근린공원", "소공원", "수변공원", "가로공원"]),
    ("가족끼리 외식하기 좋은 고기집", ["돼지고기 구이/찜", "소고기 구이/찜", "오리고기"]),
    ("비오는 날 막걸리", ["전/부침개", "요리 주점"]),
    ("밤 늦게 여는 술집", ["요리 주점", "생맥주 전문", "일반 유흥 주점"]),
    ("아이들 데리고 갈만한 공원", ["어린이공원", "주제공원", "근린공원"]),
    
    # --- Activity & Entertainment ---
    ("보드게임", ["카페", "기타"]),
    ("방탈출", ["전자 게임장", "기타"]),
    ("당구 한게임", ["당구장"]),
    ("스크린골프", ["골프 연습장"]),
    ("마사지 시원하게", ["마사지/안마"]),
    ("네일 아트", ["네일숍"]),
    
    # --- Multi-intent & Hard ---
    ("치맥", ["치킨", "생맥주 전문"]),
    ("소주에 삼겹살", ["돼지고기 구이/찜", "요리 주점"]),
    ("공부하기 좋은 조용한 카페", ["독서실/스터디 카페", "카페"]),
    
    # --- Negative / Noise ---
    ("아무거나", []),
    ("asdf", [])
]

def get_chunks(desc, window_size, stride):
    words = desc.split()
    if len(words) <= window_size:
        return [" ".join(words)]
    chunks = []
    for i in range(0, len(words), stride):
        chunk = words[i:i+window_size]
        chunks.append(" ".join(chunk))
        if i + window_size >= len(words):
            break
    return chunks

print("Loading Model...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask', device='cpu')

# Pre-encode all queries
print("Encoding Queries...")
queries = [q for q, _ in TEST_CASES]
q_embs = model.encode(queries, convert_to_numpy=True, normalize_embeddings=True)
q_emb_map = {q: q_embs[i] for i, q in enumerate(queries)}

cat_names = list(CATEGORY_DESCRIPTIONS.keys())

windows_strides = [(4, 2), (8, 4), (12, 6)]
pooling_percents = [0.1, 0.2, 0.3, 1.0] # 1.0 means mean of all chunks
thresholds = [0.30, 0.35, 0.40, 0.45, 0.50]

print("\n🚀 Starting Chunking Grid Search...")

best_accuracy = 0
best_params = None
best_noise = float('inf')
results = []

for w, s in windows_strides:
    print(f"\n[Encoding Chunks for Window={w}, Stride={s}]")
    # Cache chunk embeddings for this window/stride
    cat_chunk_embs = {}
    for cat in cat_names:
        desc = CATEGORY_DESCRIPTIONS[cat]
        chunks = get_chunks(desc, w, s)
        cat_chunk_embs[cat] = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        
    for p_pct in pooling_percents:
        for thresh in thresholds:
            passed_cases = 0
            total_noise = 0
            
            for query, expected_list in TEST_CASES:
                matched = []
                q_emb = q_emb_map[query]
                
                # Synonym Bypass
                query_lower = query.lower()
                for c_name, syns in CATEGORY_SYNONYMS.items():
                    valid_keywords = syns + [c_name.lower()]
                    if any(syn in query_lower for syn in valid_keywords):
                        if c_name not in matched:
                            matched.append(c_name)
                            
                # Chunk scoring
                for cat in cat_names:
                    if cat in matched: continue
                    c_embs = cat_chunk_embs[cat]
                    scores = np.dot(c_embs, q_emb.T).squeeze()
                    scores = np.atleast_1d(scores)
                    
                    # Top-X% Pooling
                    k = max(1, int(len(scores) * p_pct))
                    top_k = np.sort(scores)[-k:]
                    avg_score = np.mean(top_k)
                    
                    if avg_score >= thresh:
                        matched.append(cat)
                        
                # Evaluate
                if not expected_list:
                    if len(matched) <= 2: passed_cases += 1
                    else: total_noise += len(matched)
                else:
                    if any(e in matched for e in expected_list):
                        passed_cases += 1
                        total_noise += len([m for m in matched if m not in expected_list])
                    else:
                        total_noise += len(matched)
            
            acc = passed_cases / len(TEST_CASES)
            avg_noise = total_noise / len(TEST_CASES)
            
            results.append({
                'w': w, 's': s, 'p': p_pct, 't': thresh,
                'acc': acc, 'noise': avg_noise
            })
            
            if acc > best_accuracy or (acc == best_accuracy and avg_noise < best_noise):
                best_accuracy = acc
                best_noise = avg_noise
                best_params = (w, s, p_pct, thresh)

# Sort and print Top 5
results.sort(key=lambda x: (x['acc'], -x['noise']), reverse=True)
print("\n🏆 Top 5 Chunking Combinations:")
for i, r in enumerate(results[:5]):
    print(f"  {i+1}. W={r['w']}, S={r['s']}, Pool={r['p']*100}%, Thresh={r['t']:.2f} -> Acc: {r['acc']*100:.1f}%, Noise: {r['noise']:.2f}")

print(f"\n💡 Best Setting: Window {best_params[0]}, Stride {best_params[1]}, Top {best_params[2]*100}% Pool, Threshold {best_params[3]}")
