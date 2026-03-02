import os
import sqlite3

import FinanceDataReader as fdr
import joblib
import matplotlib.pyplot as plt
import pandas as pd

# --- [개선] 경로 설정 (상대 참조) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
# 모델 경로 통합
MODEL_PATHS = {
    'm_xgb': os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'),
    'm_lgbm': os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'),
    'b_xgb': os.path.join(DATA_DIR, 'bull_xgb_model.pkl'),
    'b_lgbm': os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'),
    'meta': os.path.join(DATA_DIR, 'stacking_meta_model.pkl')
}


def generate_features(df):
    """지표 생성 로직 (기존 유지)"""
    df = df.copy()
    df['Vol_Change'] = df['Volume'].pct_change()
    df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
    df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
    df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)
    return df


def run_backtest():
    print("🚀 [1/4] 데이터 로드 및 앙상블 모델 불러오기...")

    # 💡 [개선] 필수 컬럼만 조회하여 메모리 최적화
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, MACD, MACD_Sig, VWAP, OBV, BBL, BBU, RSI, ATR, BBB, BBP, Return"

    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Date >= '2025-08-01' ORDER BY Date ASC"
    raw_df = pd.read_sql(query, conn)
    conn.close()

    # 모델 로드
    models = {}
    for key, path in MODEL_PATHS.items():
        if not os.path.exists(path):
            print(f"🚨 모델 파일을 찾을 수 없습니다: {path}")
            return
        models[key] = joblib.load(path)

    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']

    # 💡 [개선] FDR 장애 대응: 코스피 지수 로드 예외 처리
    print("📈 시장 지수 필터링 데이터 준비 중...")
    try:
        kospi = fdr.DataReader('KS11', '2025-07-01')
        kospi['MA5'] = kospi['Close'].rolling(5).mean()
        market_filter_active = True
    except Exception as e:
        print(f"⚠️ FDR 지수 데이터 로드 실패 ({e}). 지수 필터를 비활성화합니다.")
        market_filter_active = False

    print("🚀 [2/4] 종목별 시뮬레이션 시작...")
    all_trades = []
    unique_codes = raw_df['Code'].unique()

    for i, code in enumerate(unique_codes):
        df = raw_df[raw_df['Code'] == code].copy().sort_values('Date')
        if len(df) < 40: continue

        df = generate_features(df)

        # 1. 모델 예측
        p_m_x = models['m_xgb'].predict_proba(df[features_xgb])[:, 1]
        p_m_l = models['m_lgbm'].predict_proba(df[features_lgbm])[:, 1]
        p_b_x = models['b_xgb'].predict_proba(df[features_xgb])[:, 1]
        p_b_l = models['b_lgbm'].predict_proba(df[features_lgbm])[:, 1]

        meta_input = pd.DataFrame({
            'XGB_Prob': p_m_x, 'LGBM_Prob': p_m_l,
            'Bull_XGB_Prob': p_b_x, 'Bull_LGBM_Prob': p_b_l
        })

        # 2. 메타 모델 확신도
        df['Final_Prob'] = models['meta'].predict_proba(meta_input)[:, 1]
        df['Disparity'] = df['Close'] / (df['MA20'] + 1e-9)

        # 3. 익일 데이터 (미래 참조 방지)
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)
        df = df.dropna(subset=['Next_Open', 'Next_High', 'Next_Low', 'Next_Close'])

        # 4. 신호 필터링 (확신도 0.75 이상 + 이격도 5% 이내)
        signals = df[(df['Final_Prob'] >= 0.75) & (df['Disparity'] <= 1.05)]

        for _, sig in signals.iterrows():
            curr_date = sig['Date']
            # 지수 필터링 적용 여부 판단
            if market_filter_active:
                if curr_date not in kospi.index or kospi.loc[curr_date, 'Close'] < kospi.loc[curr_date, 'MA5']:
                    continue

            # 🚀 매매 로직 (손절가 우선 판정 방식 유지)
            entry_p = sig['Next_Open']
            target_p = entry_p * 1.020  # 익절 +2.0%
            stop_p = entry_p * 0.975  # 손절 -2.5%

            if sig['Next_Low'] <= stop_p:
                profit = -2.5
            elif sig['Next_High'] >= target_p:
                profit = 2.0
            else:
                profit = (sig['Next_Close'] / entry_p - 1) * 100

            all_trades.append({'Date': sig['Date'], 'Code': code, 'Profit': profit - 0.25})

        if (i + 1) % 50 == 0:
            print(f" 진행 중... ({i + 1}/{len(unique_codes)})")

    print("🚀 [4/4] 결과 분석 중...")
    res_df = pd.DataFrame(all_trades)
    if res_df.empty:
        print("⚠️ 포착된 신호가 없습니다. (장이 너무 안 좋았거나 기준이 높음)")
        return

    res_df['Date'] = pd.to_datetime(res_df['Date'])
    res_df = res_df.sort_values('Date')
    res_df['Cum_Profit'] = res_df['Profit'].cumsum()

    win_rate = (res_df['Profit'] > 0).mean() * 100
    mdd = (res_df['Cum_Profit'].cummax() - res_df['Cum_Profit']).max()
    avg_profit = res_df['Profit'].mean()

    print("\n" + "="*45)
    print(f"📊 v12.1 스태킹 스나이퍼 백테스트 (2025-08~)")
    print(f" - 총 매매 횟수: {len(res_df)}회")
    print(f" - 승률 (Win Rate): {win_rate:.2f}%")
    print(f" - 누적 수익률: {res_df['Profit'].sum():.2f}%")
    print(f" - 회당 평균 수익: {avg_profit:.2f}%")
    print(f" - 최대 낙폭 (MDD): {mdd:.2f}%")
    print("="*45)

    plt.figure(figsize=(10, 5))
    plt.plot(res_df['Date'], res_df['Cum_Profit'], label='Cumulative Profit (%)', color='blue')
    plt.title('v12.1 Stacking Sniper Backtest')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    run_backtest()