import sqlalchemy
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/spotsync"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("--- Places with '분류 안된 외국식 음식점' category ---")
    foreign = conn.execute(text("SELECT id, name, category, address FROM places WHERE category = '분류 안된 외국식 음식점' LIMIT 50;")).fetchall()
    for row in foreign:
        print(row)
