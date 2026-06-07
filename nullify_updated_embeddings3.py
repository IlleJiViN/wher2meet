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

cats = [
    '동식물원/아쿠아리움', '마라탕/양꼬치', '오마카세/파인다이닝', '브런치/비건/채식'
]

cur.execute("UPDATE places SET embedding_vector_v4 = NULL WHERE category = ANY(%s)", (cats,))
null_count = cur.rowcount
print(f"Set {null_count} embedding_vector_v4 to NULL.")

conn.commit()
cur.close()
conn.close()
