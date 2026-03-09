import FinanceDataReader as fdr
import pandas as pd
import pandas_ta as ta
import sqlite3
import time
import os
from datetime import datetime, timedelta

# 현재 스크립트(src 폴더)의 부모 폴더(KORStockScan)를 찾고 그 안의 data 폴더로 경로 지정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 혹시 모를 상황을 대비해 폴더가 없으면 생성 (있으면 무시됨)
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
TABLE_NAME = 'daily_stock_quotes'

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 기존 테이블이 있다면 안전하게 삭제하고 새로 만듭니다. (초기화 목적이므로)
    cursor.execute(f'DROP TABLE IF EXISTS {TABLE_NAME}')
    
    # 새로운 지표(VWAP, OBV, ATR, BBB, BBP) 컬럼이 추가된 스키마
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            Date TEXT, Code TEXT, Name TEXT,
            Open REAL, High REAL, Low REAL, Close REAL, Volume REAL,
            MA5 REAL, MA20 REAL, MA60 REAL, MA120 REAL,
            RSI REAL, MACD REAL, MACD_Sig REAL, MACD_Hist REAL,
            BBL REAL, BBM REAL, BBU REAL, BBB REAL, BBP REAL,
            VWAP REAL, OBV REAL, ATR REAL, Return REAL,
            PRIMARY KEY (Date, Code)
        )
    ''')
    conn.commit()
    return conn

def collect_and_save():
    conn = setup_database()
    # KRX 전체 상장종목을 먼저 가져옵니다
    df_krx = fdr.StockListing('KRX')
    # KOSPI 시장만 필터링합니다
    df_kospi = df_krx[df_krx['Market'] == 'KOSPI']
    kospi_list = df_kospi[['Code', 'Name']]

    end_date = datetime.now().strftime('%Y-%m-%d')
    # 원하는 데이터부터 수집하여 지표 계산 후 NaN을 자를 여유를 둡니다.
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

    print(f"[{start_date} ~ {end_date}] 안전한 방식으로 초기 데이터 수집을 시작합니다...")

    for index, row in kospi_list.iterrows():
        code, name = row['Code'], row['Name']
        
        try:
            df = fdr.DataReader(code, start_date, end_date)
            df = df.rename(columns={
                '시가': 'Open',
                '고가': 'High',
                '저가': 'Low',
                '종가': 'Close',
                '거래량': 'Volume'
            })
            df.index.name = 'Date'
            
            # 충분한 데이터가 있는지 확인 (이평선 120일 계산 등을 위해)
            if len(df) > 150:
                # 1. 이동평균선
                df['MA5'] = ta.sma(df['Close'], length=5)
                df['MA20'] = ta.sma(df['Close'], length=20)
                df['MA60'] = ta.sma(df['Close'], length=60)
                df['MA120'] = ta.sma(df['Close'], length=120)
                
                # 2. RSI
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 3. MACD
                macd_df = ta.macd(df['Close'])
                if macd_df is not None:
                    df['MACD'] = macd_df.iloc[:, 0]
                    df['MACD_Sig'] = macd_df.iloc[:, 1]
                    df['MACD_Hist'] = macd_df.iloc[:, 2]
                
                # 4. 볼린저 밴드 (+ Bandwidth, %B 추가)
                bb_df = ta.bbands(df['Close'], length=20, std=2)
                if bb_df is not None:
                    df['BBL'] = bb_df.iloc[:, 0] # Lower Band
                    df['BBM'] = bb_df.iloc[:, 1] # Mid Band
                    df['BBU'] = bb_df.iloc[:, 2] # Upper Band
                    df['BBB'] = bb_df.iloc[:, 3] # Bandwidth (변동성 팽창 확인)
                    df['BBP'] = bb_df.iloc[:, 4] # %B (밴드 내 상대적 위치)

                # ==========================================
                # 🚀 5. 신규 강력 지표 추가 (VWAP, OBV, ATR)
                # ==========================================
                
                # 일봉 기준 VWAP (일봉에서는 주로 누적 혹은 특정 주기로 끊어서 봅니다. 
                # pandas_ta.vwap 은 기본적으로 세션/전체 기간 누적으로 계산합니다.)
                df['VWAP'] = ta.vwap(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
                
                # OBV (세력 매집 판단)
                df['OBV'] = ta.obv(close=df['Close'], volume=df['Volume'])
                
                # ATR (14일 기준 변동성 폭 판단)
                df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)

                # 6. 기본 정보 및 수익률
                df['Return'] = df['Close'].pct_change()
                df['Code'] = code
                df['Name'] = name
                
                # 정리 및 저장
                # dropna()를 여기서 하면 지표 계산 초기의 NaN 값(예: 120일 MA가 계산되기 전의 119일치)이 깔끔하게 날아갑니다.
                df = df.dropna().reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

                # DB 저장 컬럼 매핑 (새로운 지표들 포함)
                cols = ['Date', 'Code', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume', 
                        'MA5', 'MA20', 'MA60', 'MA120', 'RSI', 'MACD', 'MACD_Sig', 'MACD_Hist', 
                        'BBL', 'BBM', 'BBU', 'BBB', 'BBP', 'VWAP', 'OBV', 'ATR', 'Return']
                
                df[cols].to_sql(TABLE_NAME, conn, if_exists='append', index=False)
                print(f"[{index+1}/{len(kospi_list)}] {name}({code}) 저장 완료")
            
            # API 호출 속도 조절 (너무 빠르면 차단될 수 있음)
            time.sleep(0.3)

        except sqlite3.IntegrityError:
            pass # 중복 데이터 무시
        except Exception as e:
            print(f"[{name}] 오류 발생: {e}")

    conn.close()
    print("\n[완료] 이제 오류 없이 최신 지표가 포함된 DB가 구성되었습니다!")

if __name__ == "__main__":
    collect_and_save()