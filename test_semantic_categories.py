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
    "타코야끼", "탕후루", "타코", "야키토리", "이자카야",
    "유부초밥", "제육볶음", "덮밥", "흑염소", "보양식",
    "핫도그", "꽈배기", "마카롱"
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
