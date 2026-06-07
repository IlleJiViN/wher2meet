import sqlalchemy
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/spotsync"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("--- Places with NULL category ---")
    null_cat = conn.execute(text("SELECT id, name, category, address FROM places WHERE category IS NULL LIMIT 10;")).fetchall()
    for row in null_cat:
        print(row)
        
    print("\n--- Places with '기타' category ---")
    gita_cat = conn.execute(text("SELECT id, name, category, address FROM places WHERE category = '기타' LIMIT 50;")).fetchall()
    for row in gita_cat:
        print(row)

    print("\n--- Any places with '알 수 없음' ---")
    unknown = conn.execute(text("SELECT id, name, category, address FROM places WHERE category = '알 수 없음' LIMIT 10;")).fetchall()
    for row in unknown:
        print(row)
