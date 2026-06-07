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
    "농구장": ["%농구%"],
    "야구장": ["%야구%", "%배팅장%"],
    "축구장/풋살장": ["%축구%", "%풋살%"],
    "배드민턴장": ["%배드민턴%"],
    "사격장/양궁장": ["%사격%", "%양궁%"],
    "클라이밍/암벽등반": ["%클라이밍%", "%암벽%"],
    "아이스링크/스케이트장": ["%아이스링크%", "%스케이트%", "%롤러장%"],
    "만화카페": ["%만화%", "%코믹%"]
}

total_updated = 0
for cat, patterns in category_updates.items():
    for pattern in patterns:
        cur.execute("SELECT count(*) FROM places WHERE name LIKE %s", (pattern,))
        count = cur.fetchone()[0]
        if count > 0:
            cur.execute("UPDATE places SET category = %s WHERE name LIKE %s", (cat, pattern))
            print(f"Updated {count} places to category '{cat}' (Pattern: {pattern})")
            total_updated += count

conn.commit()
cur.close()
conn.close()

print(f"Total places updated: {total_updated}")
