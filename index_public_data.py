import pandas as pd
import json
import uuid
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch, helpers
import os

print("🔥 Loading AI Embedding Model (jhgan/ko-sroberta-multitask)...")
model = SentenceTransformer("jhgan/ko-sroberta-multitask", device="cpu")

print("🔌 Connecting to local Elasticsearch...")
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "spotsync_v4"

def process_and_index(df, name_col, addr_col, lat_col, lon_col, category_col, desc_func, sample_size=None):
    if sample_size and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)
    
    docs = []
    print(f"Embedding {len(df)} records...")
    
    # Filter out missing coordinates
    df = df.dropna(subset=[lat_col, lon_col])
    
    for _, row in df.iterrows():
        name = str(row[name_col])
        addr = str(row[addr_col]) if pd.notna(row[addr_col]) else ""
        lat = float(row[lat_col])
        lon = float(row[lon_col])
        category = str(row[category_col]) if category_col in row and pd.notna(row[category_col]) else "장소"
        desc = desc_func(row)
        
        # We only compute embedding for category + name to match v4 architecture logic
        text_to_embed = f"{category} {name}"
        embedding = model.encode(text_to_embed).tolist()
        
        doc = {
            "_index": INDEX_NAME,
            "_id": str(uuid.uuid4()),
            "_source": {
                "name": name,
                "address": addr,
                "category": category,
                "description": desc,
                "location": {"lat": lat, "lon": lon},
                "embedding": embedding
            }
        }
        docs.append(doc)
    
    print(f"Indexing {len(docs)} documents to Elasticsearch...")
    helpers.bulk(es, docs)
    print("Done!")

# Parks and Tourism skipped as they were just indexed.

# 3. Commercial POI (Seoul)
print("\n☕ Processing Seoul POIs (소상공인시장진흥공단_상가(상권)정보_서울_202603)...")
try:
    # Use utf-8 for this specific file, low memory to speed up
    df_poi = pd.read_csv("data/소상공인시장진흥공단_상가(상권)정보_서울_202603.csv", encoding="utf-8", low_memory=False)
    process_and_index(
        df_poi,
        name_col="상호명",
        addr_col="도로명주소",
        lat_col="위도",
        lon_col="경도",
        category_col="상권업종소분류명",
        desc_func=lambda r: f"{r['상호명']}은(는) {r['도로명주소']}에 위치한 {r['상권업종대분류명']} > {r['상권업종소분류명']}입니다.",
        sample_size=10000  # Sample 10,000 for local demonstration
    )
except Exception as e:
    print(f"Skipping Seoul POIs: {e}")

print("\n✅ All specified public data has been embedded and indexed!")
