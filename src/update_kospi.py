import os
import sqlite3
import pandas as pd
import FinanceDataReader as fdr
import pandas_ta as ta  # pandas_ta를 ta로 임포트
import json
import time
# 💡 핵심: datetime과 timedelta를 명확하게 임포트해야 합니다.
from datetime import datetime, timedelta
import kiwoom_utils

# ==========================================
# 1. 경로 설정 (상대 참조)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')

TABLE_NAME = 'daily_stock_quotes'
EXT_TABLE_NAME = 'external_indicators'


# --- [1. DB 마이그레이션: Marcap 컬럼 추가] ---
def migrate_db():
    """DB에 Marcap(시가총액) 컬럼이 없는 경우 추가합니다."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(daily_stock_quotes)")
    columns = [info[1] for info in cur.fetchall()]

    if 'Marcap' not in columns:
        print("🔧 [Migration] Marcap 컬럼을 추가합니다.")
        cur.execute("ALTER TABLE daily_stock_quotes ADD COLUMN Marcap INTEGER DEFAULT 0")
        conn.commit()
    conn.close()

def get_last_date(conn, table, date_col='Date', code_col=None, code=None):
    """DB에서 마지막 저장 날짜를 가져옵니다."""
    query = f"SELECT MAX({date_col}) FROM {table}"
    if code_col and code:
        query += f" WHERE {code_col} = '{code}'"
    
    try:
        df = pd.read_sql(query, conn)
        return df.iloc[0, 0]
    except:
        return None

def update_external_indicators(conn):
    """나스닥, S&P500, 환율 등 외부 경제 지표 업데이트 (중복 방지 강화)"""
    print("\n🌐 외부 거시 지표 업데이트 확인 중...")
    
    indicators = {
        'Nasdaq': 'IXIC',
        'S&P500': 'US500',
        'USD_KRW': 'USD/KRW',
        'US_10Y': 'US10YT',
        'VIX': 'VIX'
    }
    
    # 1. DB에서 마지막 업데이트 날짜 확인
    last_date_str = get_last_date(conn, EXT_TABLE_NAME, date_col='date')
    
    # 수집 시작일 설정 (마지막 날짜부터 오늘까지)
    if last_date_str:
        fetch_start = last_date_str # 마지막 날짜를 포함해서 가져온 뒤 아래에서 필터링
    else:
        fetch_start = '2022-01-01'
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 2. 데이터 수집
    df_ext = pd.DataFrame()
    for name, ticker in indicators.items():
        try:
            data = fdr.DataReader(ticker, fetch_start, today)['Close']
            if not data.empty:
                df_ext[name] = data
        except Exception as e:
            print(f"⚠️ {name}({ticker}) 수집 중 오류: {e}")

    if not df_ext.empty:
        # 3. 데이터 정제 및 날짜 포맷 변환
        df_ext.index.name = 'date'
        df_ext.reset_index(inplace=True)
        df_ext['date'] = pd.to_datetime(df_ext['date']).dt.strftime('%Y-%m-%d')
        
        # --- [핵심: 중복 제거 필터링] ---
        # DB에 저장된 마지막 날짜보다 큰(이후의) 데이터만 남깁니다.
        if last_date_str:
            df_ext = df_ext[df_ext['date'] > last_date_str]
        # ------------------------------

        if not df_ext.empty:
            # 최신 Pandas 문법 적용
            df_ext = df_ext.ffill().bfill()
            
            # 4. DB 저장
            try:
                df_ext.to_sql(EXT_TABLE_NAME, conn, if_exists='append', index=False)
                print(f"✅ 외부 지표 {len(df_ext)}일치 신규 데이터 추가 완료.")
            except sqlite3.IntegrityError:
                print("⚠️ 중복 데이터가 감지되어 삽입을 건너뛰었습니다.")
        else:
            print("✨ 외부 지표가 이미 최신 상태입니다.")
    else:
        print("ℹ️ 업데이트할 신규 외부 지표 데이터가 없습니다.")

def update_database():
    # 🚀 1. 공용 오프라인 영업일 체크 로직 호출
    print("📅 오늘이 주식시장 개장일인지 확인합니다...")
    is_open, reason = kiwoom_utils.is_trading_day()

    if not is_open:
        print(f"🛑 오늘은 {reason} 휴장일이므로 데이터베이스 업데이트를 수행하지 않고 안전하게 종료합니다.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ==========================================
    # 0. DB 마이그레이션: Marcap 컬럼 확인 및 추가
    # ==========================================
    cur.execute("PRAGMA table_info(daily_stock_quotes)")
    columns = [info[1] for info in cur.fetchall()]
    if 'Marcap' not in columns:
        print("🔧 [Migration] DB에 'Marcap(시가총액)' 컬럼을 추가합니다.")
        cur.execute("ALTER TABLE daily_stock_quotes ADD COLUMN Marcap INTEGER DEFAULT 0")
        conn.commit()

    # ==========================================
    # 1. 키움 API 토큰 준비 (Fallback용)
    # ==========================================
    kiwoom_token = None
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        kiwoom_token = kiwoom_utils.get_kiwoom_token(config)
    except Exception as e:
        print(f"⚠️ 토큰 발급 생략 (FDR 우선 모드): {e}")

    # ==========================================
    # 2. 코스피 종목 리스트 및 시가총액 확보
    # ==========================================
    print("🔍 최신 코스피 종목 및 시총 정보 확인 중...")
    kospi_list = pd.DataFrame()
    marcap_map = {}

    try:
        df_krx = fdr.StockListing('KOSPI')
        kospi_list = df_krx[['Code', 'Name']]
        # FDR 시총 데이터를 매핑 딕셔너리로 저장
        marcap_map = dict(zip(df_krx['Code'], df_krx['Marcap']))
        print(f"✅ FDR 확보: {len(kospi_list)} 종목")
    except Exception as e:
        print(f"⚠️ FDR 리스트 수집 실패: {e}. DB에서 불러옵니다.")
        try:
            kospi_list = pd.read_sql(f"SELECT DISTINCT Code, Name FROM {TABLE_NAME}", conn)
        except:
            print("🚨 종목 리스트 확보 불가. 종료합니다.")
            return

    # ==========================================
    # 3. 개별 종목 데이터 업데이트 루프
    # ==========================================
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 업데이트 기준일: {today_str}")

    for index, row in kospi_list.iterrows():
        code, name = row['Code'], row['Name']
        try:
            # --- [시가총액 확보 로직] ---
            marcap = marcap_map.get(code, 0)
            if (pd.isna(marcap) or marcap == 0) and kiwoom_token:
                # FDR에 없으면 키움 ka10100 통합 함수 호출
                info = kiwoom_utils.get_item_info_ka10100(kiwoom_token, code)
                if info:
                    marcap = int(info.get('listCount', 0)) * int(info.get('lastPrice', 0))
                time.sleep(0.1)

            # --- [날짜 확인 및 시작점 설정] ---
            last_date_str = get_last_date(conn, TABLE_NAME, date_col='Date', code_col='Code', code=code)

            if last_date_str:
                if last_date_str >= today_str:
                    # 오늘 데이터가 이미 존재한다면 시가총액만 최신화하고 다음 종목으로
                    if marcap > 0:
                        cur.execute(f"UPDATE {TABLE_NAME} SET Marcap = ? WHERE Code = ? AND Date = ?",
                                    (int(marcap), code, last_date_str))
                    continue
                # 마지막 날짜로부터 150일 전부터 수집 (지표 계산용 여유분)
                fetch_start = (datetime.strptime(last_date_str, '%Y-%m-%d') - timedelta(days=150)).strftime('%Y-%m-%d')
            else:
                fetch_start = (datetime.now() - timedelta(days=3 * 365)).strftime('%Y-%m-%d')
                last_date_str = '1900-01-01'

            # --- [데이터 수집: FDR -> Kiwoom] ---
            df = pd.DataFrame()
            try:
                df = fdr.DataReader(code, fetch_start, today_str)
            except:
                pass

            if df.empty and kiwoom_token:
                df = kiwoom_utils.get_daily_data_ka10005_df(kiwoom_token, code)
                if not df.empty:
                    df = df[df.index >= fetch_start]

            # --- [지표 연산 및 저장] ---
            if not df.empty:
                # 보조지표 (pandas_ta 활용)
                df['MA5'] = ta.sma(df['Close'], length=5)
                df['MA20'] = ta.sma(df['Close'], length=20)
                df['MA60'] = ta.sma(df['Close'], length=60)
                df['MA120'] = ta.sma(df['Close'], length=120)
                df['RSI'] = ta.rsi(df['Close'], length=14)

                macd = ta.macd(df['Close'])
                if macd is not None:
                    df['MACD'], df['MACD_Hist'], df['MACD_Sig'] = macd.iloc[:, 0], macd.iloc[:, 1], macd.iloc[:, 2]

                bb = ta.bbands(df['Close'], length=20)
                if bb is not None:
                    df['BBL'], df['BBM'], df['BBU'], df['BBB'], df['BBP'] = bb.iloc[:, 0], bb.iloc[:, 1], bb.iloc[:, 2], bb.iloc[:, 3], bb.iloc[:, 4]

                df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
                df['OBV'] = ta.obv(df['Close'], df['Volume'])
                df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
                df['Return'] = df['Close'].pct_change()
                df['Code'], df['Name'], df['Marcap'] = code, name, int(marcap)

                df = df.reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                new_rows = df[df['Date'] > last_date_str]

                if not new_rows.empty:
                    cols = ['Date', 'Code', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume',
                            'MA5', 'MA20', 'MA60', 'MA120', 'RSI', 'MACD', 'MACD_Sig', 'MACD_Hist',
                            'BBL', 'BBM', 'BBU', 'BBB', 'BBP', 'VWAP', 'OBV', 'ATR', 'Return', 'Marcap']
                    new_rows[cols].dropna(subset=['Close']).to_sql(TABLE_NAME, conn, if_exists='append', index=False)
                    print(f"✅ {name}({code}) - {len(new_rows)}일 추가")
                elif marcap > 0:
                    # 새로운 행은 없지만 최신 행의 시총 업데이트
                    cur.execute(f"UPDATE {TABLE_NAME} SET Marcap = ? WHERE Code = ? AND Date = (SELECT MAX(Date) FROM {TABLE_NAME} WHERE Code = ?)",
                                (int(marcap), code, code))
                conn.commit()

            time.sleep(0.1)

        except Exception as e:
            print(f"❌ {name}({code}) 오류: {e}")

    # 외부 지표 업데이트
    try:
        update_external_indicators(conn)
    except:
        pass

    conn.close()
    print("\n✨ 모든 데이터 업데이트 완료")

if __name__ == "__main__":
    update_database()