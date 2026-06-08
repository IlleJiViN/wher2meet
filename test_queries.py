import requests
import json

queries = [
    "크로스핏", "루프탑 카페", "비건 식당", "오마카세",
    "실내 클라이밍", "보드게임 카페", "글램핑", "만화방",
    "애견 카페", "파인다이닝", "수영장", "방탈출", "칵테일 바"
]

url = "http://localhost:8001/search"
headers = {"Content-Type": "application/json"}

for q in queries:
    payload = {
        "query": q,
        "user_latitude": 37.496,
        "user_longitude": 126.953,
        "radius_meters": 5000,
        "similarity_threshold": 0.2,
        "top_k": 3
    }
    try:
        res = requests.post(url, json=payload).json()
        print(f"\n[{q}]")
        print(f"Matched Categories: {res.get('matched_categories', [])}")
        results = res.get('results', [])
        if not results:
            print("  No results found.")
        for r in results:
            print(f"  - {r['name']} ({r['category']}) | Score: {r['similarity_score']}")
    except Exception as e:
        print(f"Error on {q}: {e}")
