import sqlite3
import os

# ==========================================
# 🛠️ SQLite 데이터 클렌징 스크립트
# ==========================================

# 파일 위치에 상관없이 절대 경로로 DB 찾기
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, 'korstockscan.db')

def nullify_columns():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB 파일을 찾을 수 없습니다: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print(f"🧹 데이터 정제 시작: {DB_PATH}")
        print("🔄 recommendation_history의 buy_time, sell_time 데이터를 NULL로 초기화합니다...")
        
        # 💡 [데이터 삭제 핵심] 값만 NULL로 업데이트하여 타입 충돌을 원천 차단
        cursor.execute("UPDATE recommendation_history SET buy_time = NULL, sell_time = NULL")
        
        conn.commit()
        print("✅ 데이터 비우기 완료! 이제 PostgreSQL로 이사할 준비가 되었습니다.")
        
    except sqlite3.OperationalError as e:
        print(f"❌ SQL 에러 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    nullify_columns()