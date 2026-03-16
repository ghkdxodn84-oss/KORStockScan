# src/utils/data_client.py
import requests
import pandas as pd
import FinanceDataReader as fdr
import time
from datetime import datetime

# 💡 [수정] 패키지 절대 경로를 통한 안전한 Import
from src.utils import kiwoom_utils
from src.database.db_manager import DBManager
from src.utils.logger import log_error  # 우리가 만든 안전한 로거 적용

class DataClient:
    """
    KORStockScan 데이터 수집 전담 클래스 (수집 창구 단일화 - Repository Pattern)
    메인 로직이 데이터 출처를 신경 쓰지 않고 항상 동일한 DataFrame을 받을 수 있도록 캡슐화합니다.
    """

    def __init__(self, kiwoom_token=None):
        self.kiwoom_token = kiwoom_token
        self.db = DBManager()  # 로컬 DB 접근을 위한 매니저 초기화

    def get_kospi_symbols(self) -> pd.DataFrame:
        """코스피 종목 리스트를 가져옵니다. (FDR 실패 시 로컬 DB 우회)"""
        # 1차 시도: FinanceDataReader
        try:
            df = fdr.StockListing('KOSPI')
            if 'Marcap' not in df.columns:
                df['Marcap'] = 0
            return df[['Code', 'Name', 'Marcap']]
        except Exception as e:
            log_error(f"FDR KOSPI 종목 리스트 수집 실패. 로컬 DB 우회 시도... (사유: {e})")

        # 2차 시도: 로컬 DB (방어 로직) - 💡 [수정] SQLAlchemy Engine 사용
        try:
            # 파이썬 모델의 소문자 컬럼명(code, name, marcap)에 맞춰 쿼리 작성
            query = "SELECT code as Code, name as Name, MAX(marcap) as Marcap FROM daily_stock_quotes GROUP BY code, name"
            
            # engine을 직접 넘겨주면 Pandas가 알아서 안전하게 데이터를 퍼옵니다.
            df_db = pd.read_sql(query, self.db.engine)

            if not df_db.empty:
                print(f"✅ 로컬 DB에서 {len(df_db)}개의 종목 정보를 성공적으로 복원했습니다.")
                return df_db[['Code', 'Name', 'Marcap']]
        except Exception as db_e:
            log_error(f"로컬 DB KOSPI 종목 리스트 수집 마저 실패: {db_e}")

        return pd.DataFrame()

    def get_ohlcv(self, code: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        특정 종목의 일봉 데이터를 수집합니다.
        [1순위] FDR 시도 -> [2순위] Kiwoom API 우회
        """
        df = pd.DataFrame()

        try:
            if end_date:
                df = fdr.DataReader(code, start_date, end_date)
            else:
                df = fdr.DataReader(code, start_date)

            if not df.empty:
                df = df.reset_index()
                return df

        except Exception as e:
            log_error(f"[{code}] FDR 수집 실패. 키움 API 우회 시도... (사유: {e})")

        # Kiwoom API 우회
        if self.kiwoom_token:
            try:
                df_kiwoom = kiwoom_utils.get_daily_data_ka10005_df(self.kiwoom_token, code)

                if df_kiwoom is not None and not df_kiwoom.empty:
                    df_kiwoom = df_kiwoom.reset_index()
                    mask = df_kiwoom['Date'] >= pd.to_datetime(start_date)
                    if end_date:
                        mask &= df_kiwoom['Date'] <= pd.to_datetime(end_date)
                    return df_kiwoom.loc[mask]

            except Exception as e:
                log_error(f"[{code}] 키움 API 수집 마저 실패: {e}")

        return pd.DataFrame()

    def get_full_daily_data(self, code: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        OHLCV 데이터에 키움 API의 수급 및 신용잔고율 데이터를 Left Join 하여 반환합니다.
        """
        df = self.get_ohlcv(code, start_date, end_date)
        if df.empty:
            return df

        if 'Date' in df.columns:
            # 💡 타임존 정보 제거 (병합 에러 차단)
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            df.set_index('Date', inplace=True)

        if self.kiwoom_token:
            today_str = datetime.now().strftime("%Y%m%d")
            
            # 수급 및 신용 데이터 수집 (안전한 딜레이 포함)
            try:
                df_investor = kiwoom_utils.get_investor_daily_ka10059_df(self.kiwoom_token, code, today_str)
                time.sleep(0.3)
                df_margin = kiwoom_utils.get_margin_daily_ka10013_df(self.kiwoom_token, code, today_str)

                if not df_investor.empty:
                    df_investor.index = pd.to_datetime(df_investor.index).tz_localize(None)
                    df = df.join(df_investor, how='left')
                if not df_margin.empty:
                    df_margin.index = pd.to_datetime(df_margin.index).tz_localize(None)
                    df = df.join(df_margin, how='left')
            except Exception as e:
                 log_error(f"[{code}] 수급/신용 데이터 조인 중 에러 발생: {e}")

        # 결측치 0 처리
        for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']:
            if col not in df.columns:
                df[col] = 0
            else:
                df[col] = df[col].fillna(0)

        return df.reset_index()
    
    def get_top_marketcap_stocks(limit=300):
        """
        [FDR 완벽 대체용] KOSPI 시가총액 상위 종목 코드를 가져옵니다.
        네이버 모바일 증권 API가 허용하는 최대 호출량(60개)에 맞춰
        여러 페이지를 안전하게 순회하며 우량주 종목을 수집합니다.
        """
        # 💡 [해결 1] 평범한 크롬 웹 브라우저인 것처럼 신분증(헤더) 위조
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://m.stock.naver.com/'
        }

        target_codes = []
        # 💡 [해결 2] 300개를 한 번에 부르지 않고(400 에러 방지), 60개씩 쪼개서 요청합니다.
        page_size = 60
        max_pages = (limit // page_size) + 1

        for page in range(1, max_pages + 1):
            url = f"https://m.stock.naver.com/api/stocks/marketValue/KOSPI?page={page}&pageSize={page_size}"

            try:
                res = requests.get(url, headers=headers, timeout=10)

                if res.status_code == 200:
                    data = res.json()
                    stocks = data.get('stocks', [])

                    # 더 이상 불러올 종목이 없으면 루프 탈출
                    if not stocks:
                        break

                    for stock in stocks:
                        code = stock.get('itemCode')
                        name = stock.get('stockName')

                        # 스팩, 우선주, ETF 등 불순물 제거 로직 통과 후 적재
                        if kiwoom_utils.is_valid_stock(code, name):
                            target_codes.append(code)

                            # 목표 개수(300개)를 채우면 즉시 반환
                            if len(target_codes) >= limit:
                                return target_codes
                else:
                    print(f"🚨 네이버 API 접근 거절 (HTTP {res.status_code}) - 페이지: {page}")
                    break

            except Exception as e:
                log_error(f"네이버 시가총액 상위 종목 조회 실패: {e}")
                print(f"🚨 시가총액 상위 종목 조회 실패: {e}")
                break

            # 💡 [핵심] 네이버 서버 차단 방지를 위한 짧은 휴식 시간
            time.sleep(0.3)

        return target_codes