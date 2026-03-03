import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    OHLCV 데이터프레임을 입력받아 KORStockScan의 모든 기술적 지표와
    AI 모델(XGB, LGBM)용 파생 피처를 계산하여 반환합니다.
    """
    df = df.copy()

    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"입력 데이터에 필수 컬럼 '{col}'이 없습니다.")

    # ----------------------------------------------------
    # 1. 기본 기술적 지표
    # ----------------------------------------------------
    df['Return'] = df['Close'].pct_change()
    df['MA5'] = ta.sma(df['Close'], length=5)
    df['MA20'] = ta.sma(df['Close'], length=20)
    df['MA60'] = ta.sma(df['Close'], length=60)
    df['MA120'] = ta.sma(df['Close'], length=120)

    df['RSI'] = ta.rsi(df['Close'], length=14)

    macd_df = ta.macd(df['Close'])
    if macd_df is not None and not macd_df.empty:
        df['MACD'] = macd_df.iloc[:, 0]
        df['MACD_Hist'] = macd_df.iloc[:, 1]
        df['MACD_Sig'] = macd_df.iloc[:, 2]
    else:
        df['MACD'] = df['MACD_Hist'] = df['MACD_Sig'] = 0

    bb_df = ta.bbands(df['Close'], length=20, std=2, ddof=1)
    if bb_df is not None and not bb_df.empty:
        df['BBL'] = bb_df.iloc[:, 0]
        df['BBM'] = bb_df.iloc[:, 1]
        df['BBU'] = bb_df.iloc[:, 2]
        df['BBB'] = bb_df.iloc[:, 3]
        df['BBP'] = bb_df.iloc[:, 4]
    else:
        for col in ['BBL', 'BBM', 'BBU', 'BBB', 'BBP']:
            df[col] = 0

    df['OBV'] = ta.obv(close=df['Close'], volume=df['Volume'])
    df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)

    # === [수정됨] 안전한 VWAP 계산 로직 ===
    v = df['Volume']
    p = (df['High'] + df['Low'] + df['Close']) / 3
    vwap_calc = None

    # 1. 인덱스가 이미 날짜형인 경우 (수집기에서 바로 넣을 때)
    if isinstance(df.index, pd.DatetimeIndex):
        vwap_calc = ta.vwap(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
    # 2. Date 컬럼이 존재하는 경우 (DB에서 꺼내올 때)
    elif 'Date' in df.columns:
        temp_idx = pd.to_datetime(df['Date'])
        vwap_calc = ta.vwap(
            high=df['High'].set_axis(temp_idx),
            low=df['Low'].set_axis(temp_idx),
            close=df['Close'].set_axis(temp_idx),
            volume=df['Volume'].set_axis(temp_idx)
        )
        if vwap_calc is not None:
            vwap_calc = vwap_calc.values  # 인덱스 충돌 방지를 위해 값(array)만 추출

    # 반환값이 없거나(None) 에러가 났다면 수동 누적 평균으로 계산 (안전장치)
    if vwap_calc is None:
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
    else:
        df['VWAP'] = vwap_calc

    # !!! 가장 중요한 부분: XGBoost object 에러 차단을 위해 강제로 float 타입 변환 !!!
    df['VWAP'] = pd.to_numeric(df['VWAP'], errors='coerce')

    # ----------------------------------------------------
    # 2. AI 앙상블 모델용 파생 피처
    # ----------------------------------------------------
    df['Vol_Change'] = df['Volume'].pct_change()
    df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
    df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)

    # ----------------------------------------------------
    # 3. 결측치(NaN) 처리 및 반환
    # ----------------------------------------------------
    df = df.replace([np.inf, -np.inf], np.nan)
    df.bfill(inplace=True)
    df.fillna(0, inplace=True)

    return df


if __name__ == "__main__":
    import FinanceDataReader as fdr

    print("Feature Engineer 로직 테스트를 시작합니다...")
    test_df = fdr.DataReader('005930', '2023-01-01', '2023-12-31')

    # DB에서 불러온 상황을 강제로 모방하기 위해 인덱스를 날리고 Date 컬럼화
    test_df = test_df.reset_index()
    processed_df = calculate_all_features(test_df)

    print("✅ 계산 완료! VWAP 데이터 및 타입 확인:")
    print(processed_df['VWAP'].tail())
    print("VWAP Dtype:", processed_df['VWAP'].dtype)