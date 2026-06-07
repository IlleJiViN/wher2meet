import time
import numpy as np
import torch
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from typing import List, Optional

from app.models.schemas import SearchRequest, SearchResponse, PlaceSearchResult
from categories import CATEGORY_DESCRIPTIONS, CATEGORY_SYNONYMS

ALPHA_CATEGORY = 0.7
BETA_NAME = 0.3

def execute_search(
    body: SearchRequest,
    model: SentenceTransformer,
    engine,
    category_names: List[str],
    category_vectors: np.ndarray
) -> SearchResponse:
    start_time = time.perf_counter()
    
    lat = body.user_latitude
    lon = body.user_longitude
    
    if body.users:
        valid_users = [u for u in body.users if u.latitude is not None and u.longitude is not None]
        if valid_users:
            total_weight = sum(u.weight for u in valid_users)
            if total_weight > 0:
                lat = sum(u.latitude * u.weight for u in valid_users) / total_weight
                lon = sum(u.longitude * u.weight for u in valid_users) / total_weight
            else:
                lat = sum(u.latitude for u in valid_users) / len(valid_users)
                lon = sum(u.longitude for u in valid_users) / len(valid_users)
            
    if lat is None or lon is None:
        raise ValueError("Either user_latitude/user_longitude or users list must be provided.")

    clean_name_query = body.query
    if body.users:
        for u in body.users:
            clean_loc = u.name.replace("역", "").replace("삼거리", "").strip()
            if len(clean_loc) >= 2:
                clean_name_query = clean_name_query.replace(clean_loc, "")
    
    for area in ["이태원", "신촌", "홍대", "강남", "종로", "명동", "혜화", "대학로", "성수"]:
        clean_name_query = clean_name_query.replace(area, "")
    
    clean_name_query = clean_name_query.strip()
    if not clean_name_query:
        clean_name_query = body.query
        
    with torch.no_grad():
        query_vector = model.encode(
            [body.query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')
        
        name_query_vector = model.encode(
            [clean_name_query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')
    
    matched_categories = []
    category_sim_map = {}
    
    explicit_matches = []
    query_lower = body.query.lower()
    for cat_name, synonyms in CATEGORY_SYNONYMS.items():
        valid_keywords = synonyms + [cat_name.lower()]
        if any(syn in query_lower for syn in valid_keywords):
            explicit_matches.append(cat_name)
            category_sim_map[cat_name] = 1.0
            
    # If explicit matches found, ONLY use them (strict filtering)
    if explicit_matches:
        matched_categories = explicit_matches
    else:
        # Otherwise, fall back to semantic similarity matching
        cat_scores = np.dot(category_vectors, query_vector.T).squeeze()
        for i, score in enumerate(cat_scores):
            if float(score) >= body.category_threshold:
                matched_categories.append(category_names[i])
                category_sim_map[category_names[i]] = float(score)

    matched_categories = list(set(matched_categories))
    matched_categories.sort(key=lambda c: category_sim_map.get(c, 0.0), reverse=True)
    
    degrees = (body.radius_meters / 111000.0) * 1.1
    
    if matched_categories:
        cat_placeholders = ", ".join([f":cat_{i}" for i in range(len(matched_categories))])
        # Allow places that match the categories OR places that have the exact search query in their name
        category_filter_sql = f"AND (category IN ({cat_placeholders}) OR name ILIKE :query_like)"
    else:
        # If no categories matched, at least try to find it in the name
        category_filter_sql = "AND name ILIKE :query_like"
    
    sql_params = {
        "lon": lon,
        "lat": lat,
        "degrees": degrees,
        "query_like": f"%{clean_name_query}%"
    }
    for i, cat in enumerate(matched_categories):
        sql_params[f"cat_{i}"] = cat
    
    sql_query = text(f"""
        SELECT id, name, category, latitude, longitude, address,
               ST_Distance(location::geography, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography) AS distance_meters,
               embedding_vector_v4
        FROM places
        WHERE location && ST_Expand(ST_SetSRID(ST_Point(:lon, :lat), 4326), :degrees)
          AND ST_DWithin(location, ST_SetSRID(ST_Point(:lon, :lat), 4326), :degrees)
          {category_filter_sql}
          AND name NOT SIMILAR TO '%(개발|컴퍼니|산업|주식회사|홀딩스|사내|구내)%'
          AND embedding_vector_v4 IS NOT NULL
        ORDER BY distance_meters ASC
        LIMIT 3000
    """)
    
    candidates = []
    with engine.connect() as conn:
        result = conn.execute(sql_query, sql_params)
        for r in result:
            candidates.append({
                "id": r[0],
                "name": r[1],
                "category": r[2],
                "latitude": r[3],
                "longitude": r[4],
                "address": r[5],
                "distance_meters": float(r[6]),
                "embedding": np.array(r[7], dtype='float32')
            })
    
    if not candidates:
        latency = (time.perf_counter() - start_time) * 1000
        return SearchResponse(
            query=body.query,
            matched_categories=[],
            results=[],
            latency_ms=round(latency, 2)
        )
    
    name_vectors = np.stack([c["embedding"] for c in candidates])
    name_scores = np.dot(name_vectors, name_query_vector.T).squeeze()
    name_scores = np.atleast_1d(name_scores)
    
    scored_candidates = []
    boost_keywords = []
    if "와인" in query_lower or "wine" in query_lower:
        boost_keywords.extend(["와인", "wine", "bar", "바", "펍", "pub"])
    if "카페" in query_lower or "cafe" in query_lower or "커피" in query_lower:
        boost_keywords.extend(["카페", "cafe", "커피", "coffee", "찻집"])
    if "합주" in query_lower or "밴드" in query_lower:
        boost_keywords.extend(["합주", "밴드", "연습실", "studio", "스튜디오"])
    if "노래방" in query_lower or "코인" in query_lower:
        boost_keywords.extend(["노래", "코인", "sing", "노래방"])
        
    for idx, candidate in enumerate(candidates):
        cat_sim = category_sim_map.get(candidate["category"], 0.0)
        name_sim = float(name_scores[idx])
        
        boost = 0.0
        cand_name_lower = candidate["name"].lower()
        if boost_keywords:
            is_singing_room = "노래" in cand_name_lower or candidate["category"] == "노래방"
            for kw in boost_keywords:
                if ("합주" in query_lower or "연습" in query_lower or "studio" in query_lower) and kw in ["연습실", "스튜디오", "studio"] and is_singing_room:
                    continue
                if kw in cand_name_lower:
                    boost += 0.30
                    break
        
        if clean_name_query and clean_name_query.lower() in cand_name_lower:
            boost += 1.0
            cat_sim = 1.0  # Treat exact substring match as a perfect category match

        if matched_categories:
            final_score = ALPHA_CATEGORY * cat_sim + BETA_NAME * max(name_sim, 0.0) + boost
        else:
            final_score = max(name_sim, 0.0) + boost
        
        if final_score >= body.similarity_threshold:
            scored_candidates.append({
                "candidate": candidate,
                "final_score": final_score,
                "cat_score": cat_sim,
                "name_score": name_sim
            })
    
    scored_candidates.sort(
        key=lambda x: x["cat_score"] - (x["candidate"].get("distance_meters", 10000) / 10000.0) * 0.5, 
        reverse=True
    )
    
    search_results = []
    for item in scored_candidates[:body.top_k]:
        c = item["candidate"]
        cat_desc = CATEGORY_DESCRIPTIONS.get(c["category"], "")
        search_results.append(
            PlaceSearchResult(
                place_id=c["id"],
                name=c["name"],
                category=c["category"],
                latitude=c["latitude"],
                longitude=c["longitude"],
                description=cat_desc,
                address=c.get("address", ""),
                distance_meters=round(c["distance_meters"], 1),
                similarity_score=round(item["final_score"], 4),
                category_score=round(item["cat_score"], 4),
                name_score=round(item["name_score"], 4)
            )
        )
        
    latency = (time.perf_counter() - start_time) * 1000
    
    system_msg = None
    if "미술관/박물관" in matched_categories:
        system_msg = "ℹ️ '미술관/박물관' 카테고리는 현재 데이터베이스에 준비되지 않은 항목입니다. 추후 업데이트될 예정입니다!"
        
    return SearchResponse(
        query=body.query,
        matched_categories=matched_categories,
        results=search_results,
        latency_ms=round(latency, 2),
        system_message=system_msg
    )
