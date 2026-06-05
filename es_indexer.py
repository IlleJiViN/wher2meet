import os
import time
import numpy as np
from sqlalchemy import create_engine, text
from elasticsearch import Elasticsearch, helpers

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/spotsync")
ES_URL = os.environ.get("ES_URL", "http://localhost:9200")
INDEX_NAME = "spotsync_places"

def main():
    print("Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    
    print(f"Connecting to Elasticsearch at {ES_URL}...")
    es = Elasticsearch([ES_URL])
    
    # Check if ES is ready
    if not es.ping():
        print("Error: Could not connect to Elasticsearch.")
        return

    # Delete index if exists
    if es.indices.exists(index=INDEX_NAME):
        print(f"Deleting existing index {INDEX_NAME}...")
        es.indices.delete(index=INDEX_NAME)

    # Create Index with mappings for vector search and geo queries
    mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "text", "analyzer": "nori"} if False else {"type": "text"}, # Note: nori needs to be installed, using default text for now
                "category": {"type": "keyword"},
                "address": {"type": "text"},
                "location": {"type": "geo_point"},
                "embedding_vector_v4": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    
    print(f"Creating index {INDEX_NAME}...")
    es.indices.create(index=INDEX_NAME, body=mapping)
    
    # Fetch data from Postgres and stream to Elasticsearch
    print("Fetching places from PostgreSQL & indexing to Elasticsearch...")
    
    def generate_actions():
        chunk_size = 5000
        offset = 0
        total_indexed = 0
        
        while True:
            query = text("""
                SELECT id, name, category, latitude, longitude, address, embedding_vector_v4 
                FROM places 
                WHERE embedding_vector_v4 IS NOT NULL
                ORDER BY id
                LIMIT :limit OFFSET :offset
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {"limit": chunk_size, "offset": offset})
                rows = result.fetchall()
                
            if not rows:
                break
                
            for row in rows:
                place_id, name, category, lat, lon, address, embedding = row
                
                doc = {
                    "_index": INDEX_NAME,
                    "_id": place_id,
                    "_source": {
                        "id": place_id,
                        "name": name,
                        "category": category,
                        "address": address,
                        "location": {
                            "lat": float(lat),
                            "lon": float(lon)
                        },
                        "embedding_vector_v4": np.array(embedding, dtype='float32').tolist()
                    }
                }
                yield doc
                
            offset += len(rows)
            total_indexed += len(rows)
            print(f"Prepared {total_indexed} actions...")

    success, failed = 0, 0
    t0 = time.perf_counter()
    for ok, item in helpers.streaming_bulk(es, generate_actions(), chunk_size=2000, max_chunk_bytes=10*1024*1024):
        if ok:
            success += 1
        else:
            failed += 1
        if (success + failed) % 10000 == 0:
            elapsed = time.perf_counter() - t0
            speed = (success + failed) / elapsed if elapsed > 0 else 0
            print(f"Indexed {(success + failed)} records | Speed: {speed:.1f} rows/s")
            
    print(f"Indexing completed. Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
