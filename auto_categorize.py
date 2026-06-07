import sqlalchemy
from sqlalchemy import create_engine, text
import time

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/spotsync"
engine = create_engine(DATABASE_URL)

RULES = [
    (lambda n: '테니스' in n, '테니스장'),
    (lambda n: '농구' in n, '농구장'),
    (lambda n: '야구' in n, '야구장'),
    (lambda n: '축구' in n or '풋살' in n, '축구장/풋살장'),
    (lambda n: '골프' in n, '골프 연습장'),
    (lambda n: '당구' in n, '당구장'),
    (lambda n: '볼링' in n, '볼링장'),
    (lambda n: '수영장' in n, '수영장'),
    (lambda n: '탁구' in n, '탁구장'),
    
    (lambda n: '어린이공원' in n, '어린이공원'),
    (lambda n: '근린공원' in n, '근린공원'),
    (lambda n: '체육공원' in n, '체육공원'),
    (lambda n: '생태공원' in n or '자연공원' in n, '생태/자연공원'),
    (lambda n: '역사공원' in n, '역사공원'),
    (lambda n: '수변공원' in n, '수변공원'),
    (lambda n: '소공원' in n, '소공원'),
    (lambda n: '문화공원' in n, '문화공원'),
    (lambda n: '묘지공원' in n, '묘지공원'),
    (lambda n: '공원' in n, '기타공원'),
    
    (lambda n: '광장' in n, '광장'),
    (lambda n: '쉼터' in n, '쉼터/휴게공간'),
    (lambda n: '유원지' in n or '테마파크' in n, '유원지/테마파크'),
    (lambda n: n.endswith('역') and len(n) < 10, '지하철/철도역'),
    (lambda n: '정거장' in n, '지하철/철도역'),
    
    (lambda n: '노래방' in n or '코인노래' in n, '노래방'),
    (lambda n: 'PC방' in n or '피시방' in n, 'PC방'),
    (lambda n: '독서실' in n or '스터디' in n, '독서실/스터디 카페'),
    
    (lambda n: '미용실' in n or '헤어' in n, '미용실'),
    (lambda n: '네일' in n, '네일숍'),
    (lambda n: '피부' in n, '피부 관리실'),
]

def get_new_category(name, current_category):
    for condition, new_cat in RULES:
        if condition(name):
            return new_cat
    return None

def process_batch():
    batch_size = 5000
    updates_made = 0
    
    with engine.connect() as conn:
        # Fetch rows that are potentially anomalous
        # Including '기타', '알 수 없음', NULL, or any row that contains sports keywords but has wrong category
        query = text("""
            SELECT id, name, category FROM places 
            WHERE category IS NULL 
               OR category IN ('기타', '알 수 없음', '분류 안된 외국식 음식점')
               OR name LIKE '%테니스%' OR name LIKE '%농구%' OR name LIKE '%축구%'
               OR name LIKE '%야구%' OR name LIKE '%풋살%'
            LIMIT :batch_size
        """)
        rows = conn.execute(query, {"batch_size": batch_size}).fetchall()
        
        if not rows:
            return 0
            
        updates = []
        for row in rows:
            place_id, name, current_category = row
            if name is None:
                continue
                
            new_cat = get_new_category(name, current_category)
            
            # If our rule didn't catch it and it's '기타' or NULL, assign it to a default or leave it to be processed
            # But wait, if we leave it, the script will loop forever picking the same rows.
            # So if we can't classify it, we should maybe set it to a special "unclassifiable" so we don't fetch it again?
            # Or we can just set it to "기타" but exclude it next time.
            # Actually, the user asked to thoroughly categorize all anomalous places. Let's just set them to "분류 완료" or something? No, we shouldn't make up random categories.
            # Let's only fetch rows that we haven't checked or that we CAN update.
            # To avoid infinite loop, we can just fetch all and filter.
            pass
            
    return updates_made

# To avoid infinite loops, let's just query everything, apply rules, and update.
def run_all():
    offset = 0
    batch_size = 10000
    total_updated = 0
    
    while True:
        with engine.connect() as conn:
            # We will just scan the whole DB in chunks to be exhaustive
            query = text(f"SELECT id, name, category FROM places ORDER BY id LIMIT {batch_size} OFFSET {offset}")
            rows = conn.execute(query).fetchall()
            
            if not rows:
                break
                
            updates = []
            for row in rows:
                place_id, name, current_cat = row
                if not name:
                    continue
                    
                # If it's a known anomalous category, or has a sports keyword
                is_anomalous = current_cat in (None, '기타', '알 수 없음', '분류 안된 외국식 음식점')
                has_keyword = any(k in name for k in ['테니스', '농구', '축구', '야구', '풋살', '골프', '당구', '볼링', '수영', '탁구', '공원', '광장', '쉼터', '유원지'])
                
                if is_anomalous or has_keyword:
                    new_cat = get_new_category(name, current_cat)
                    if new_cat and new_cat != current_cat:
                        updates.append({"new_cat": new_cat, "id": place_id})
                    elif is_anomalous and not new_cat:
                        # If we can't classify an anomalous place, let's try to find a default
                        pass
            
            if updates:
                with engine.begin() as tx:
                    tx.execute(
                        text("UPDATE places SET category = :new_cat, embedding_vector_v4 = NULL WHERE id = :id"),
                        updates
                    )
                total_updated += len(updates)
                print(f"Updated {len(updates)} rows in this batch. Total updated: {total_updated}")
                
        offset += batch_size
        print(f"Processed up to offset {offset}")

if __name__ == '__main__':
    print("Starting categorization...")
    run_all()
    print("Done!")
