import psycopg2
import os
from collections import Counter

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "spotsync")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

# Find categories that are vague
vague_cats = [
    '기타', '기타 스포츠시설 운영업', '기타 오락 관련 산업', 
    '그 외 기타 간이 음식점', '기타공원', '기타(가로공원)', 
    '기타 서양식 음식점', '기타 일식 음식점', '기타 한식 음식점'
]

cur.execute("SELECT name, category FROM places WHERE category = ANY(%s) LIMIT 20000", (vague_cats,))
results = cur.fetchall()

print(f"Total vague places fetched: {len(results)}")

# Extract common words from names to see what we are missing
words = []
for name, cat in results:
    for word in name.split():
        if len(word) > 1:
            words.append(word)

word_counts = Counter(words)
print("\nTop 50 common words in vague categories:")
for word, count in word_counts.most_common(50):
    print(f"{word}: {count}")

conn.close()
