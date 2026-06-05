import os
import glob
import zipfile
import pandas as pd
import time
import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, insert, text
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry

# Reconfigure stdout/stderr encoding for UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Database Connection URI
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/spotsync"

# SQLAlchemy Model Definition
Base = declarative_base()

class Place(Base):
    __tablename__ = 'places'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    address = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    embedding_text = Column(Text, nullable=False)
    embedding_text_v2 = Column(Text, nullable=True)
    embedding_text_v3 = Column(Text, nullable=True)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)

def process_files():
    zip_path = "소상공인시장진흥공단_상가(상권)정보_20260331.zip"
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Could not find Gyeonggi-do ZIP data file: {zip_path}")
        print(f"[PIPELINE] CSV not found. Extracting ZIP file: {zip_path}...")
        t0 = time.perf_counter()
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        print(f"[PIPELINE] Extracted ZIP in {time.perf_counter() - t0:.2f} seconds.")
        csv_files = glob.glob("*.csv")
        
    target_files = csv_files
    if not target_files:
        raise FileNotFoundError("Could not find any CSV files even after extraction.")
        
    print(f"[PIPELINE] Found target CSV files to parse: {target_files}")
    
    # Pre-clear table once
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE places RESTART IDENTITY CASCADE;"))
        
    for i, csv_file_path in enumerate(target_files):
        print(f"  - Loading {csv_file_path} ({i+1}/{len(target_files)})...")
        raw_df = pd.read_csv(
            csv_file_path, 
            sep=',', 
            encoding='utf-8', 
            encoding_errors='replace', 
            dtype=str
        )
        cleaned_df, id_c, name_c, cat_c, addr_c, lon_c, lat_c = clean_and_transform(raw_df)
        load_to_postgis(cleaned_df, id_c, name_c, cat_c, addr_c, lon_c, lat_c, clear_table=False)

def clean_and_transform(df: pd.DataFrame):
    """Performs data cleaning, maps columns, filters Gyeonggi-do, and constructs embedding_text."""
    print("[PIPELINE] Beginning data cleaning and transformation...")
    
    from categories import CATEGORY_DESCRIPTIONS

    status_col = [col for col in df.columns if "영업상태" in col]
    if status_col:
        col_name = status_col[0]
        initial_len = len(df)
        df = df[~df[col_name].astype(str).str.contains("폐업", na=False)]
        print(f"[PIPELINE] Removed {initial_len - len(df)} closed businesses. Remaining: {len(df)}")
        
    id_col = [col for col in df.columns if "상가업소번호" in col][0]
    name_col = [col for col in df.columns if "상호명" in col][0]
    
    sub_cats = [col for col in df.columns if "상권업종소분류명" in col]
    category_col = sub_cats[0] if sub_cats else [col for col in df.columns if "상권업종대분류명" in col][0]
    
    address_col = [col for col in df.columns if "도로명주소" in col or "지번주소" in col][0]
    lon_col = [col for col in df.columns if "경도" in col][0]
    lat_col = [col for col in df.columns if "위도" in col][0]
    
    df = df.dropna(subset=[lat_col, lon_col])
    
    all_subcategories = list(CATEGORY_DESCRIPTIONS.keys())
        
    initial_len = len(df)
    df = df[df[category_col].astype(str).isin(all_subcategories)]
    print(f"[PIPELINE] Filtered relevant categories only. Removed {initial_len - len(df)} non-relevant places. Remaining: {len(df)}")
    
    df["embedding_text"] = ""
    df["embedding_text_v2"] = ""
    df["embedding_text_v3"] = ""
    
    df[lat_col] = df[lat_col].astype(float)
    df[lon_col] = df[lon_col].astype(float)
    
    return df, id_col, name_col, category_col, address_col, lon_col, lat_col

def load_to_postgis(df: pd.DataFrame, id_col, name_col, category_col, address_col, lon_col, lat_col, clear_table=False):
    """Creates the PostGIS database table and batch inserts the filtered records."""
    engine = create_engine(DATABASE_URL)
    
    t_prep = time.perf_counter()
    records = df[[id_col, name_col, category_col, address_col, lat_col, lon_col, "embedding_text", "embedding_text_v2", "embedding_text_v3"]].to_dict(orient='records')
    places_to_insert = [
        {
            "place_id": str(row[id_col]),
            "name": str(row[name_col]),
            "category": str(row[category_col]),
            "address": str(row[address_col]),
            "latitude": float(row[lat_col]),
            "longitude": float(row[lon_col]),
            "embedding_text": str(row["embedding_text"]),
            "embedding_text_v2": str(row["embedding_text_v2"]),
            "embedding_text_v3": str(row["embedding_text_v3"]),
            "location": f"SRID=4326;POINT({row[lon_col]} {row[lat_col]})"
        }
        for row in records
    ]
    print(f"[DB] Preprocessed {len(places_to_insert)} records in {time.perf_counter() - t_prep:.2f} seconds.")
        
    batch_size = 2000
    total_records = len(places_to_insert)
    
    t0 = time.perf_counter()
    with engine.begin() as conn:
        if clear_table:
            conn.execute(text("TRUNCATE TABLE places RESTART IDENTITY CASCADE;"))
            
        for i in range(0, total_records, batch_size):
            batch = places_to_insert[i:i+batch_size]
            conn.execute(insert(Place), batch)
            
    print(f"[SUCCESS] PostGIS load completed successfully in {time.perf_counter() - t0:.2f}s!")

if __name__ == "__main__":
    print("="*80)
    print("      SpotSync AI - PostGIS Data Pipeline & ETL Processor")
    print("="*80)
    
    try:
        process_files()
        print("\n🎉 ETL Data Pipeline execution finished successfully!")
    except Exception as e:
        print(f"\n❌ [CRITICAL ERROR] Pipeline failed: {str(e)}")
    print("="*80)
