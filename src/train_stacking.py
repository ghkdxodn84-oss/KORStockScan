import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
import FinanceDataReader as fdr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score
import warnings

warnings.filterwarnings('ignore')

# --- [신규] 경로 설정 (상대 참조) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')

# 불러올 하위 모델 4개 경로
HYBRID_XGB_PATH = os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl')
HYBRID_LGBM_PATH = os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl')
BULL_XGB_PATH = os.path.join(DATA_DIR, 'bull_xgb_model.pkl')
BULL_LGBM_PATH = os.path.join(DATA_DIR, 'bull_lgbm_model.pkl')

# 저장할 최종 메타 모델 경로
META_MODEL_PATH = os.path.join(DATA_DIR, 'stacking_meta_model.pkl')


# ==========================================
# [수정] 우량 대장주 필터링 (종목 대폭 확대)
# ==========================================
def get_stacking_target_codes():
    print("[1/5] 스태킹 모델용 타겟 종목 필터링 중 (종목 풀 확대)...")
    try:
        df_krx = fdr.StockListing('KOSPI')

        # 💡 [확대] 시총 상위 200 -> 500위로 확대 (초소형 잡주만 1차 배제)
        top_500 = df_krx.sort_values(by='Marcap', ascending=False).head(500)

        # 💡 [확대] 그 중 거래량 상위 100 -> 300위로 확대 (시장의 관심을 받는 종목 300개)
        target_top = top_500.sort_values(by='Volume', ascending=False).head(300)

        print(f"✅ FDR 기반으로 시총/거래량 상위 {len(target_top)}종목을 추출했습니다.")
        return target_top['Code'].tolist()

    except Exception as e:
        print(f"⚠️ FDR 종목 리스트 수집 실패 ({e}). DB 데이터로 우회합니다...")
        try:
            conn = sqlite3.connect(DB_NAME)
            max_date_query = "SELECT MAX(Date) FROM daily_stock_quotes"
            latest_date = pd.read_sql(max_date_query, conn).iloc[0, 0]

            # 💡 [DB 우회 로직도 함께 확대] LIMIT 100 -> 300
            query = f"SELECT Code FROM daily_stock_quotes WHERE Date = '{latest_date}' ORDER BY Volume DESC LIMIT 300"
            top_codes_df = pd.read_sql(query, conn)
            conn.close()

            if top_codes_df.empty:
                print("🚨 DB에서도 종목을 찾을 수 없습니다.")
                return []
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['Code'].tolist()
        except Exception as db_e:
            print(f"🚨 DB Fallback 조회 실패: {db_e}")
            return []


# ==========================================
# 2. 데이터 로드 및 전처리 (최적화)
# ==========================================
def load_data_for_stacking(codes):
    print(f"[2/5] {len(codes)}개 종목 메타 모델 학습용 데이터 로드 중...")
    conn = sqlite3.connect(DB_NAME)
    all_processed_data = []

    # 💡 [최적화] 4개 모델이 필요로 하는 모든 컬럼을 명시 (메모리 폭발 방지)
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, MACD, MACD_Sig, VWAP, OBV, BBL, BBU, RSI, ATR, BBB, BBP, Return"

    for code in codes:
        query = f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' AND Date >= '2025-08-01' ORDER BY Date ASC"
        df = pd.read_sql(query, conn)

        if len(df) < 60: continue

        # 공통 지표 생성
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

        df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
        df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)

        # 익일 데이터 생성
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)

        # ==========================================
        # 🎯 [기존 타겟 유지] 엄격한 정답지 조건
        # ==========================================
        hit_target = (df['Next_High'] / (df['Next_Open'] + 1e-9)) >= 1.020
        no_stop_loss = (df['Next_Low'] / (df['Next_Open'] + 1e-9)) >= 0.975
        solid_close = df['Next_Close'] > df['Next_Open']

        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)

        df = df.replace([np.inf, -np.inf], np.nan).dropna(
            subset=['Target', 'Next_Open', 'Next_High', 'Next_Low', 'Next_Close'])
        df = df.dropna()
        if not df.empty:
            all_processed_data.append(df)

    conn.close()
    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()


# ==========================================
# 3. 스태킹 앙상블 메인 로직
# ==========================================
def train_stacking_ensemble():
    target_codes = get_stacking_target_codes()
    if not target_codes: return

    total_df = load_data_for_stacking(target_codes)
    if total_df.empty:
        print("[-] 데이터가 부족합니다.")
        return

    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']

    total_df = total_df.sort_values(by='Date')
    split_idx = int(len(total_df) * 0.8)
    train_df, test_df = total_df.iloc[:split_idx], total_df.iloc[split_idx:]
    y_train, y_test = train_df['Target'], test_df['Target']

    print("[3/5] 전공이 분리된 4개의 베이스 모델 불러오는 중...")
    try:
        xgb_model = joblib.load(HYBRID_XGB_PATH)
        lgbm_model = joblib.load(HYBRID_LGBM_PATH)
        bull_xgb = joblib.load(BULL_XGB_PATH)
        bull_lgbm = joblib.load(BULL_LGBM_PATH)
    except FileNotFoundError as e:
        print(f"🚨 하위 모델 파일을 찾을 수 없습니다: {e}")
        print("이전에 train_xgboost.py 등의 모델 학습을 먼저 완료해야 합니다.")
        return

    print("[4/5] 각 전문가에게 질문하여 확률(Probability) 추출 중...")
    meta_X_train = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(train_df[features_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(train_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(train_df[features_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(train_df[features_lgbm])[:, 1]
    })

    meta_X_test = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(test_df[features_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(test_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(test_df[features_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(test_df[features_lgbm])[:, 1]
    })

    print("[5/5] 최종 결정권자(Meta-Model) 학습 및 임계값 테스트 중...")
    meta_model = LogisticRegression(class_weight='balanced', random_state=42)
    meta_model.fit(meta_X_train, y_train)

    meta_pred_proba = meta_model.predict_proba(meta_X_test)[:, 1]

    print("\n[전문가 의견 상관관계 분석]")
    print(meta_X_test.corr().round(3))

    thresholds = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85]
    print("\n=============================================")
    print("   임계값(Th) | 정밀도(Precision) | 매수횟수(Test)")
    print("---------------------------------------------")
    for th in thresholds:
        meta_pred = (meta_pred_proba >= th).astype(int)
        if sum(meta_pred) == 0: continue
        precision = precision_score(y_test, meta_pred, zero_division=0)
        print(f"      {th:.2f}    |      {precision * 100:.2f}%      |   {sum(meta_pred)}건")
    print("=============================================")

    joblib.dump(meta_model, META_MODEL_PATH)
    print(f"\n✅ 완전체 스태킹 모델 저장 완료: {META_MODEL_PATH}")


if __name__ == "__main__":
    train_stacking_ensemble()