import requests
import json
import time

queries = [
    # Food - Specific
    "평양냉면", "마라샹궈", "텐동", "국밥", "순대국", "수제버거", "돈카츠", "알리오올리오", "시카고피자", "타코", 
    "케밥", "마카롱", "크로플", "소금빵", "베이글", "브런치", "비건", "오마카세", "회전초밥", "양꼬치", 
    "훠궈", "샤브샤브", "밀면", "팟타이", "쌀국수", "인도커리", "파인다이닝", "김치찌개", "삼겹살", "소고기",
    # Drink / Cafe
    "드립커피", "에스프레소 바", "디저트 카페", "루프탑 카페", "베이커리 카페", "스터디 카페", "북카페", "드로잉 카페", "고양이 카페", "애견 카페",
    # Nightlife
    "이자카야", "와인바", "LP바", "수제맥주", "호프집", "포장마차", "전통주", "칵테일 바", "뮤직바", "클럽",
    # Activities
    "스크린야구", "야구 연습장", "당구장", "스크린골프", "탁구장", "PC방", "코인노래방", "합주실", "댄스 연습실", "테니스장", 
    "볼링장", "실내 클라이밍", "방탈출", "보드게임 카페", "만화방", "사격장", "롤러장", "아이스링크", "수영장", "크로스핏",
    # Beauty / Health
    "필라테스", "요가", "헬스장", "PT", "네일샵", "바버샵", "미용실", "피부과", "안과", "약국",
    # Retail / Shopping
    "편집샵", "팝업스토어", "소품샵", "서점", "꽃집", "안경점", "다이소", "올리브영", "편의점", "마트",
    # Accommodation / Outdoors
    "글램핑", "풀빌라", "게스트하우스", "호텔", "모텔", "캠핑장", "테마파크", "놀이공원", "수목원", "산책로"
]

url = "http://localhost:8001/search"
headers = {"Content-Type": "application/json"}

results_summary = []
failed_queries = []

print(f"Testing {len(queries)} queries...")

for i, q in enumerate(queries):
    payload = {
        "query": q,
        "user_latitude": 37.496,
        "user_longitude": 126.953,
        "radius_meters": 10000,
        "similarity_threshold": 0.2,
        "top_k": 1
    }
    try:
        res = requests.post(url, json=payload).json()
        results = res.get('results', [])
        if not results:
            failed_queries.append(q)
        else:
            top_res = results[0]
            # Store summary to find weak spots
            results_summary.append({
                "query": q,
                "top_name": top_res['name'],
                "category": top_res['category'],
                "score": top_res['similarity_score']
            })
    except Exception as e:
        print(f"Error on {q}: {e}")
    time.sleep(0.05)

print("\n=== Failed Queries (0 Results) ===")
for fq in failed_queries:
    print(f"- {fq}")

print("\n=== Weak Matches (Score < 0.6) ===")
for r in results_summary:
    if r['score'] < 0.6:
        print(f"- {r['query']} -> {r['top_name']} ({r['category']}) | Score: {r['score']}")

with open('100_test_results.json', 'w') as f:
    json.dump({"failed": failed_queries, "weak": [r for r in results_summary if r['score'] < 0.6], "all": results_summary}, f, ensure_ascii=False, indent=2)
