import sqlalchemy
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/spotsync"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Look for anomalous categories
    query = text("SELECT category, count(*) FROM places GROUP BY category ORDER BY count(*) DESC;")
    result = conn.execute(query).fetchall()
    
    print("Categories and counts:")
    for row in result:
        print(f"{row[0]}: {row[1]}")
