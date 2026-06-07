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
    "테마파크/놀이공원": ["%놀이공원%", "%테마파크%", "%워터파크%"],
    "동식물원/아쿠아리움": ["%동물원%", "%식물원%", "%아쿠아리움%", "%수족관%"],
    "공방/원데이클래스": ["%공방%", "%원데이클래스%"],
    "팝업스토어/플리마켓": ["%팝업스토어%", "%플리마켓%"],
    "마라탕/양꼬치": ["%마라탕%", "%훠궈%", "%양꼬치%", "%마라샹궈%"],
    "오마카세/파인다이닝": ["%오마카세%", "%파인다이닝%"],
    "브런치/비건/채식": ["%브런치%", "%비건%", "%채식%"],
    "사진관/셀프사진관": ["%사진관%", "%네컷%", "%스티커사진%", "%셀프스튜디오%"],
    "캠핑/글램핑": ["%캠핑%", "%글램핑%", "%카라반%", "%야영장%"]
}

total_updated = 0
updated_cats = list(category_updates.keys())

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

conn.commit()
cur.close()
conn.close()
