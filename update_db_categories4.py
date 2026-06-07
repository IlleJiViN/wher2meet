import psycopg2
import os

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

category_updates = {
    "이자카야/야키토리": ["%이자카야%", "%야키토리%", "%선술집%"],
    "타코/타코야끼": ["%타코야끼%", "%타코비%", "%타코%"],
    "디저트/마카롱/탕후루": ["%마카롱%", "%탕후루%", "%젤라또%", "%크로플%"],
    "백숙/흑염소/보양식": ["%흑염소%", "%보양식%", "%삼계탕%", "%장어%", "%백숙%"]
}

updated_cats = list(category_updates.keys())
total_updated = 0

for cat, patterns in category_updates.items():
    for pattern in patterns:
        cur.execute("SELECT count(*) FROM places WHERE name LIKE %s", (pattern,))
        count = cur.fetchone()[0]
        if count > 0:
            cur.execute("UPDATE places SET category = %s WHERE name LIKE %s", (cat, pattern))
            print(f"Updated {count} places to category '{cat}' (Pattern: {pattern})")
            total_updated += count

print(f"Total places updated: {total_updated}")

cur.execute("UPDATE places SET embedding_vector_v4 = NULL WHERE category = ANY(%s)", (updated_cats,))
null_count = cur.rowcount
print(f"Set {null_count} embedding_vector_v4 to NULL.")

# Also fix '꽈배기' which should just map to 분식
cur.execute("UPDATE places SET category = '김밥/만두/분식' WHERE name LIKE '%꽈배기%'")
count_k = cur.rowcount
if count_k > 0:
    cur.execute("UPDATE places SET embedding_vector_v4 = NULL WHERE name LIKE '%꽈배기%'")
    print(f"Updated {count_k} places to '김밥/만두/분식' (Pattern: %꽈배기%)")

conn.commit()
cur.close()
conn.close()
