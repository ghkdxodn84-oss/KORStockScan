import sys
from pathlib import Path

# ==========================================
# 🚀 프로젝트 루트 경로 세팅
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import create_engine
from src.utils.constants import DATA_DIR, POSTGRES_URL

# 기존 SQLite 파일 경로
SQLITE_URL = f"sqlite:///{DATA_DIR}/korstockscan.db"

# 💡 [핵심] SQLite의 옛날 컬럼명을 PostgreSQL의 새 컬럼명으로 번역하는 사전
# models.py에 추가된 BBL, VWAP 등의 고급 지표들을 모두 포함시켰습니다.
COLUMN_MAPPING_DAILY = {
    'Date': 'quote_date',
    'Code': 'stock_code',
    'Name': 'stock_name',
    'Open': 'open_price',
    'High': 'high_price',
    'Low': 'low_price',
    'Close': 'close_price',
    'Volume': 'volume',
    'MA5': 'ma5',
    'MA20': 'ma20',
    'MA60': 'ma60',
    'MA120': 'ma120',
    'RSI': 'rsi',
    'MACD': 'macd',
    'MACD_Sig': 'macd_sig',
    'MACD_Hist': 'macd_hist',
    
    # --- 💡 신규 추가된 고급 기술적 지표들 매핑 ---
    'BBL': 'bbl',
    'BBM': 'bbm',
    'BBU': 'bbu',
    'BBB': 'bbb',
    'BBP': 'bbp',
    'VWAP': 'vwap',
    'OBV': 'obv',
    'ATR': 'atr',
    'Return': 'daily_return', # DB 컬럼명 'return'과 완벽히 일치하도록 매핑
    # ----------------------------------------------
    
    'Marcap': 'marcap',
    'Retail_Net': 'retail_net',
    'Foreign_Net': 'foreign_net',
    'Inst_Net': 'inst_net',
    'Margin_Rate': 'margin_rate'
}

def run_migration():
    print("🚀 [Phase 2.1] daily_stock_quotes 단일 테이블 마이그레이션을 시작합니다...")
    
    sqlite_engine = create_engine(SQLITE_URL)
    pg_engine = create_engine(POSTGRES_URL)
    
    # 💡 [요구사항 반영] 오직 daily_stock_quotes 테이블만 타겟팅합니다.
    target_tables = ['daily_stock_quotes']
    
    for table in target_tables:
        print(f"\n📦 테이블 [{table}] 마이그레이션 준비 중...")
        try:
            df = pd.read_sql_table(table, sqlite_engine)
            
            if df.empty:
                print(f"   ℹ️ 데이터가 0건입니다. 패스!")
                continue
            
            # 💡 스키마 변경에 따른 컬럼명 매핑 및 필터링
            if table == 'daily_stock_quotes':
                print("   🛠️ [데이터 정제] 추가된 지표를 포함하여 컬럼명을 번역합니다.")
                
                existing_cols = [col for col in COLUMN_MAPPING_DAILY.keys() if col in df.columns]
                df = df[existing_cols].rename(columns=COLUMN_MAPPING_DAILY)
                
                # 날짜 데이터 정합성 보장
                df['quote_date'] = pd.to_datetime(df['quote_date']).dt.strftime('%Y-%m-%d')
            
            print(f"   🚚 {len(df):,}개의 행을 이송합니다...")
            
            # PostgreSQL로 데이터 붓기
            df.to_sql(table, pg_engine, if_exists='append', index=False, chunksize=10000)
            print(f"   ✅ [{table}] 데이터 적재 완료!")

        except Exception as e:
            print(f"   ❌ [{table}] 이송 중 에러 발생: {e}")

    print("\n🎉 모든 데이터 마이그레이션이 완벽하게 끝났습니다!")

if __name__ == "__main__":
    run_migration()