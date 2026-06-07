import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from categories import CATEGORY_DESCRIPTIONS, CATEGORY_SYNONYMS

# Prepare categories
cat_names = list(CATEGORY_DESCRIPTIONS.keys())
cat_texts = list(CATEGORY_DESCRIPTIONS.values())

for cat_name, synonyms in CATEGORY_SYNONYMS.items():
    if cat_name in cat_names:
        idx = cat_names.index(cat_name)
        cat_texts[idx] = " ".join(synonyms) + " " + cat_texts[idx]

print("Loading model...")
model = SentenceTransformer("jhgan/ko-sroberta-multitask", device="cpu")

print("Encoding categories...")
with torch.no_grad():
    cat_vectors = model.encode(cat_texts, convert_to_numpy=True, normalize_embeddings=True)

test_queries = [
    "캠핑장", "글램핑", "카라반",
    "동물원", "아쿠아리움", "수족관", "식물원",
    "놀이공원", "테마파크", "워터파크",
    "팝업스토어", "플리마켓",
    "도예 공방", "향수 공방", "원데이클래스",
    "오마카세", "파인다이닝",
    "마라탕", "훠궈", "양꼬치",
    "브런치 카페",
    "비건 식당", "채식",
    "무한리필", "고기뷔페",
    "루프탑 카페", "야경",
    "수산시장", "야시장",
    "사진관", "네컷사진", "스티커사진"
]

print("\n--- Testing Categories ---")
for query in test_queries:
    with torch.no_grad():
        q_vec = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    
    scores = np.dot(cat_vectors, q_vec.T).squeeze()
    
    top_indices = np.argsort(scores)[::-1][:3]
    print(f"\nQuery: '{query}'")
    for rank, idx in enumerate(top_indices):
        print(f"  {rank+1}. {cat_names[idx]} (Score: {scores[idx]:.4f})")
