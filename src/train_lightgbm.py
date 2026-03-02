import os
import sqlite3
import FinanceDataReader as fdr
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.metrics import precision_score

# --- [신규] 경로 설정 (상대 참조) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
MODEL_PATH = os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl')
FEATURE_PATH = os.path.join(DATA_DIR, 'lgbm_features.pkl')


# ==========================================
# 1. 우량 대장주 필터링 (FDR + DB Fallback)
# ==========================================
def get_hybrid_top_codes():
    print("[1/5] 최신 시장 데이터 기반 우량 대장주 필터링 중 (LGBM 버전)...")
    try:
        df_krx = fdr.StockListing('KOSPI')
        # 💡 시총 상위 500개 중 거래량 상위 300개 추출 (잡주 배제 & 풀 확대)
        top_500 = df_krx.sort_values(by='Marcap', ascending=False).head(500)
        target_top = top_500.sort_values(by='Volume', ascending=False).head(300)
        print(f"✅ FDR 기반으로 시총/거래량 상위 {len(target_top)}종목을 추출했습니다.")
        return target_top['Code'].tolist()

    except Exception as e:
        print(f"⚠️ FDR 종목 리스트 수집 실패 ({e}). DB 데이터로 우회합니다...")
        try:
            conn = sqlite3.connect(DB_NAME)
            max_date_query = "SELECT MAX(Date) FROM daily_stock_quotes"
            latest_date = pd.read_sql(max_date_query, conn).iloc[0, 0]

            # 💡 DB 우회 시에도 300개 추출
            query = f"SELECT Code FROM daily_stock_quotes WHERE Date = '{latest_date}' ORDER BY Volume DESC LIMIT 300"
            top_codes_df = pd.read_sql(query, conn)
            conn.close()

            if top_codes_df.empty:
                return []
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['Code'].tolist()
        except Exception as db_e:
            print(f"🚨 DB Fallback 실패: {db_e}")
            return []


# ==========================================
# 2. 데이터 로드 및 전처리 (최적화 적용 & 엄격한 타겟 유지)
# ==========================================
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 최신 지표 적용 중...")
    conn = sqlite3.connect(DB_NAME)
    all_data = []

    # 💡 [최적화] LightGBM에 필요한 컬럼만 명시적으로 가져와 메모리 절약
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, BBL, BBU, RSI, ATR, BBB, BBP"

    for code in codes:
        # 최근 약 3년 치(750일) 데이터만 빠르게 로드
        query = f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date DESC LIMIT 750"
        df = pd.read_sql(query, conn)
        df = df.sort_values('Date', ascending=True).reset_index(drop=True)

        if len(df) < 150:
            continue

        # 파생 지표 계산
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

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
        solid_close = df['Next_Close'] > df['Next_Open']  # 양봉 마감 조건 유지

        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)

        # 결측치 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna(
            subset=['Target', 'Next_Open', 'Next_High', 'Next_Low', 'Next_Close'])
        df = df.dropna()

        if not df.empty:
            all_data.append(df)

    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()


# ==========================================
# 3. LightGBM 모델 학습
# ==========================================
def train_hybrid_lgbm():
    target_codes = get_hybrid_top_codes()
    if not target_codes:
        print("[-] 학습을 위한 대상 종목이 없어 종료합니다.")
        return

    total_df = load_and_preprocess(target_codes)

    if total_df.empty:
        print("[-] 학습할 데이터가 부족합니다. DB 상태를 확인하세요.")
        return

    # 변동성 및 지표 강도 위주의 LightGBM 특화 Feature
    features = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']

    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]

    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()

    print(f"\n📊 [학습 데이터 현황] 일반(0): {neg_count}개 | 스나이퍼 타겟(1): {pos_count}개")

    if pos_count == 0:
        print("🚨 [비상] 정답(1) 데이터가 0개입니다! 타겟 조건을 낮춰야 합니다.")
        dynamic_weight = 1.0
    else:
        dynamic_weight = neg_count / pos_count
        print(f"⚖️ [처방] 정답 예측에 {dynamic_weight:.1f}배의 가중치를 부여합니다.\n")

    model = LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.005,
        num_leaves=31,
        max_depth=5,
        min_child_samples=20,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        subsample_freq=5,
        lambda_l1=0.1,
        lambda_l2=0.1,
        scale_pos_weight=dynamic_weight,
        random_state=42,
        n_jobs=-1,
        force_col_wise=True,
        importance_type='gain'
    )

    print("[3/5] LightGBM 모델 학습 시작...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric='logloss',
        callbacks=[
            early_stopping(stopping_rounds=100),
            log_evaluation(period=100)
        ]
    )

    print("\n[4/5] 테스트 데이터로 성능 검증 중...")
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    max_prob = y_pred_proba.max()
    print(f"💡 [AI의 최고 확신도] 가장 정답일 것 같은 종목의 확률: {max_prob * 100:.2f}%")

    threshold = 0.50
    if max_prob < 0.50:
        threshold = max_prob * 0.9
        print(f"⚠️ 50% 이상 확신하는 종목이 없어, 임계값을 {threshold:.3f}로 낮춰서 채점합니다.")

    y_pred = (y_pred_proba >= threshold).astype(int)
    precision = precision_score(y_test, y_pred, zero_division=0)

    print("\n" + "=" * 50)
    print(f"✅ LightGBM 검증 정밀도 (임계값 {threshold:.3f} 기준): {precision:.2%}")
    print("=" * 50)

    # 💡 분리된 경로(data 폴더)에 모델 저장
    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, FEATURE_PATH)
    print(f"[5/5] 모델 파일 저장 완료: {MODEL_PATH}")


if __name__ == "__main__":
    train_hybrid_lgbm()