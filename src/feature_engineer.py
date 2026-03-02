import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    OHLCV 데이터프레임을 입력받아 KORStockScan의 모든 기술적 지표와
    AI 모델(XGB, LGBM)용 파생 피처를 한 번에 계산하여 반환합니다.
    (pandas-ta 라이브러리 사용)
    """
    # 원본 데이터 보호를 위한 복사
    df = df.copy()

    # 필수 컬럼 검증
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"입력 데이터에 필수 컬럼 '{col}'이 없습니다.")

    # ----------------------------------------------------
    # 1. 기본 기술적 지표 (pandas_ta 활용)
    # ----------------------------------------------------

    # 수익률
    df['Return'] = df['Close'].pct_change()

    # 이동평균선 (SMA)
    df['MA5'] = ta.sma(df['Close'], length=5)
    df['MA20'] = ta.sma(df['Close'], length=20)
    df['MA60'] = ta.sma(df['Close'], length=60)
    df['MA120'] = ta.sma(df['Close'], length=120)

    # RSI (상대강도지수)
    df['RSI'] = ta.rsi(df['Close'], length=14)

    # MACD (pandas_ta는 데이터프레임으로 3개 컬럼을 반환함)
    macd_df = ta.macd(df['Close'])
    if macd_df is not None and not macd_df.empty:
        df['MACD'] = macd_df.iloc[:, 0]  # MACD 선
        df['MACD_Hist'] = macd_df.iloc[:, 1]  # 히스토그램
        df['MACD_Sig'] = macd_df.iloc[:, 2]  # 시그널 선
    else:
        df['MACD'], df['MACD_Hist'], df['MACD_Sig'] = 0, 0, 0

    # 볼린저 밴드 (5개 컬럼 반환: Lower, Mid, Upper, Bandwidth, %B)
    bb_df = ta.bbands(df['Close'], length=20, std=2)
    if bb_df is not None and not bb_df.empty:
        df['BBL'] = bb_df.iloc[:, 0]  # 하단 밴드
        df['BBM'] = bb_df.iloc[:, 1]  # 중심선 (MA20)
        df['BBU'] = bb_df.iloc[:, 2]  # 상단 밴드
        df['BBB'] = bb_df.iloc[:, 3]  # 밴드 폭 (Bandwidth)
        df['BBP'] = bb_df.iloc[:, 4]  # %B (Position)
    else:
        for col in ['BBL', 'BBM', 'BBU', 'BBB', 'BBP']:
            df[col] = 0

    # OBV (On Balance Volume)
    df['OBV'] = ta.obv(close=df['Close'], volume=df['Volume'])

    # ATR (Average True Range)
    df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)

    # VWAP (거래량 가중 평균가)
    # pandas_ta의 vwap은 인덱스가 Datetime이 아닐 경우 에러가 날 수 있어 방어 로직 추가
    try:
        df['VWAP'] = ta.vwap(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
    except Exception:
        v = df['Volume']
        p = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (p * v).cumsum() / v.cumsum()

    # ----------------------------------------------------
    # 2. AI 앙상블 모델용 파생 피처
    # ----------------------------------------------------

    # XGBoost를 위한 가공 피처
    df['MA_Ratio'] = df['Close'] / df['MA20']
    df['Up_Trend_2D'] = (df['MA20'] > df['MA20'].shift(2)).astype(int)
    df['Dist_MA5'] = (df['Close'] - df['MA5']) / df['MA5']

    # LightGBM을 위한 가공 피처
    df['BB_Pos'] = df['BBP']
    df['RSI_Slope'] = df['RSI'] - df['RSI'].shift(3)
    df['Range_Ratio'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'] + 1e-8)  # 0으로 나누기 방지
    df['Vol_Momentum'] = df['Volume'] / df['Volume'].rolling(window=5).mean()
    df['Vol_Change'] = df['Volume'] / df['Volume'].shift(1).replace(0, 1e-8)

    # ----------------------------------------------------
    # 3. 결측치(NaN) 처리 및 반환
    # ----------------------------------------------------

    # 계산 중 발생한 무한대(Inf) 값을 NaN으로 일괄 변경
    df = df.replace([np.inf, -np.inf], np.nan)

    # 이동평균선 등으로 인해 초반 행에 발생하는 결측치는 뒤의 값(bfill)으로 1차 채움
    df.bfill(inplace=True)  # <--- 최신 문법으로 수정

    # 그래도 남은 결측치가 있다면 0으로 안전하게 채움
    df.fillna(0, inplace=True)

    return df


# ==========================================
# 단위 테스트용 (해당 파일만 실행해 볼 때)
# ==========================================
if __name__ == "__main__":
    import FinanceDataReader as fdr

    print("Feature Engineer 로직 테스트를 시작합니다...")
    # 삼성전자 데이터 샘플 로드
    test_df = fdr.DataReader('005930', '2023-01-01', '2023-12-31')

    # 피처 계산
    processed_df = calculate_all_features(test_df)

    print("✅ 계산 완료! 생성된 컬럼 목록 및 샘플 데이터:")
    print(list(processed_df.columns))
    print(processed_df[['Close', 'MA20', 'RSI', 'MACD', 'BB_Pos', 'Vol_Change']].tail())