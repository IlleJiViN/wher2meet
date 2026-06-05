import pandas as pd
import numpy as np
import time
import torch
import warnings
from sqlalchemy import create_engine, insert, text
from sentence_transformers import SentenceTransformer
from data_pipeline import Place

warnings.filterwarnings("ignore")
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/spotsync"
MODEL_NAME = "jhgan/ko-sroberta-multitask"

def process_public_data(engine, model):
    print("[PUBLIC PIPELINE] Starting optimized processing for Public Data...")
    
    # 1. Load Tourism Data
    print("Loading Tourism data...")
    df_tour = pd.read_csv('data/전국관광지정보표준데이터.csv', encoding='cp949')
    df_tour = df_tour.dropna(subset=['위도', '경도', '관광지명'])
    
    # 2. Load Park Data
    print("Loading Park data...")
    df_park = pd.read_csv('data/전국도시공원정보표준데이터.csv', encoding='cp949')
    df_park = df_park.dropna(subset=['위도', '경도', '공원명'])
    
    places_to_insert = []
    
    # Parse Tourism
    for idx, row in df_tour.iterrows():
        name = str(row.get('관광지명', ''))
        cat = str(row.get('관광지구분', '관광지'))
        desc = str(row.get('관광지소개', ''))
        addr = str(row.get('소재지도로명주소', ''))
        lat, lon = float(row['위도']), float(row['경도'])
        
        # New Enriched Template Strategy
        embed_text = f"장소명: {name} (카테고리: {cat}) / 주소: {addr} / 특징: {desc}"
        
        places_to_insert.append({
            "place_id": f"TOUR_{idx}",
            "name": name[:255],
            "category": cat[:100],
            "address": addr,
            "latitude": lat,
            "longitude": lon,
            "embedding_text": embed_text,
            "embedding_text_v2": embed_text,
            "embedding_text_v3": embed_text,
            "location": f"SRID=4326;POINT({lon} {lat})"
        })
        
    # Parse Parks
    for idx, row in df_park.iterrows():
        name = str(row.get('공원명', ''))
        cat = str(row.get('공원구분', '공원'))
        addr = str(row.get('소재지도로명주소', ''))
        lat, lon = float(row['위도']), float(row['경도'])
        
        embed_text = f"장소명: {name} (카테고리: {cat}) / 주소: {addr} / 특징: 도심 속 휴식 공간"
        
        places_to_insert.append({
            "place_id": f"PARK_{idx}",
            "name": name[:255],
            "category": cat[:100],
            "address": addr,
            "latitude": lat,
            "longitude": lon,
            "embedding_text": embed_text,
            "embedding_text_v2": embed_text,
            "embedding_text_v3": embed_text,
            "location": f"SRID=4326;POINT({lon} {lat})"
        })
        
    print(f"Total public records prepared: {len(places_to_insert)}")
    
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM places WHERE place_id LIKE 'TOUR_%' OR place_id LIKE 'PARK_%'"))
        
    batch_size = 500
    for i in range(0, len(places_to_insert), batch_size):
        batch = places_to_insert[i:i+batch_size]
        texts = [b["embedding_text"] for b in batch]
        
        with torch.no_grad():
            embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32).tolist()
            
        for b, emb in zip(batch, embeddings):
            b["embedding_vector_v4"] = emb
            
        with engine.begin() as conn:
            conn.execute(insert(Place), batch)
            
        print(f"Inserted {i+len(batch)} / {len(places_to_insert)} records.")
        
    print("Public Data Pipeline completed successfully!")

def main():
    torch.set_num_threads(2)
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    engine = create_engine(DATABASE_URL)
    
    t0 = time.perf_counter()
    process_public_data(engine, model)
    print(f"Done in {time.perf_counter() - t0:.2f} seconds.")

if __name__ == "__main__":
    main()
