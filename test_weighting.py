import requests
import json
import time

API_URL = "http://localhost:8001/search"
HEADERS = {"Content-Type": "application/json"}

# 숭실대 위치 기준
payload_template = {
    "query": "",
    "user_latitude": 37.4966011,
    "user_longitude": 126.953682,
    "radius_meters": 10000,
    "category_threshold": 0.35,
    "similarity_threshold": 0.35,
    "top_k": 10,
    "users": [{"name": "숭실대", "latitude": 37.4966011, "longitude": 126.953682}]
}

queries_to_test = [
    "피방",          # Synonym explicitly matched -> Should only show PC방, ordered by distance
    "탁구장",        # Explicitly search 탁구장 -> Should show 탁구장
]

print("Waiting for API to boot...")
time.sleep(15) # Give uvicorn some time to load the model

for q in queries_to_test:
    print(f"\n==============================================")
    print(f"🎯 검색어 테스트: '{q}'")
    print(f"==============================================")
    
    payload = payload_template.copy()
    payload["query"] = q
    
    response = requests.post(API_URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        results = response.json()
        if isinstance(results, dict) and "results" in results:
            items = results["results"]
        else:
            items = results
            
        print(f"총 {len(items)}개의 결과가 검색되었습니다.\n")
        
        for i, res in enumerate(items):
            name = res.get("name", "Unknown")
            cat = res.get("category", "Unknown")
            dist = res.get("distance_meters", 0)
            score = res.get("similarity_score", 0.0)
            print(f"[{i+1}등] 이름: {name:<15} | 카테고리: {cat:<8} | 거리: {dist:>5.1f}m | 점수: {score:.3f}")
    else:
        print(f"Error: {response.status_code}")
