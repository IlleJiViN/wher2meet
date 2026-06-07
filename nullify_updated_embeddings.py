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
    '농구장', '야구장', '축구장/풋살장', '배드민턴장',
    '사격장/양궁장', '클라이밍/암벽등반', '아이스링크/스케이트장',
    '만화카페'
]

cur.execute("UPDATE places SET embedding_vector_v4 = NULL WHERE category = ANY(%s)", (cats,))
count = cur.rowcount
print(f"Set {count} embedding_vector_v4 to NULL.")

conn.commit()
cur.close()
conn.close()
