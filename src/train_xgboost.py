import sqlite3
import os
import FinanceDataReader as fdr
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score
from xgboost import XGBClassifier

# --- [신규] 경로 설정 (상대 참조) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
MODEL_PATH = os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl')
FEATURE_PATH = os.path.join(DATA_DIR, 'hybrid_features.pkl')


# ==========================================
# 1. 우량 대장주 필터링 (FDR + DB Fallback)
# ==========================================
def get_hybrid_top_codes():
    print("[1/5] 최신 시장 데이터 기반 우량 대장주 필터링 중...")

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
# 2. 데이터 로드 및 전처리 (최적화 적용)
# ==========================================
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 정답지(Target) 생성 중...")
    conn = sqlite3.connect(DB_NAME)
    all_data = []

    # DB에 저장된 필요 컬럼만 명시적으로 가져와 메모리 절약
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, MACD, MACD_Sig, VWAP, OBV"

    for code in codes:
        # 전체 데이터가 아닌, 최근 데이터만(예: 약 3년치 750 거래일) 제한하여 로딩 속도 향상
        query = f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date DESC LIMIT 750"
        df = pd.read_sql(query, conn)

        # 최신순으로 가져왔으므로 다시 과거순(Ascending)으로 정렬
        df = df.sort_values('Date', ascending=True).reset_index(drop=True)

        if len(df) < 150:
            continue

        # --- [리팩토링] 파생 변수 계산 ---
        # 이미 DB에 있는 값들을 활용하여 가볍게 비율만 계산합니다.
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

        # 추세 지표 (2일 연속 상승)
        df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
        df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)

        # 수익률
        df['Return'] = df['Close'].pct_change()

        # --- 정답지(Target) 생성을 위한 미래 데이터 시프트 ---
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)

        # 🚀 [v12.1] 스나이퍼 타겟 조건 (고가 +2.0%, 저가 방어, 양봉 마감)
        hit_target = (df['Next_High'] / (df['Next_Open'] + 1e-9)) >= 1.020
        no_stop_loss = (df['Next_Low'] / (df['Next_Open'] + 1e-9)) >= 0.975
        solid_close = df['Next_Close'] > df['Next_Open']

        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)

        # 결측치(과거 지표 미생성 구간 및 맨 마지막 줄 미래 데이터) 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        if not df.empty:
            all_data.append(df)

    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()


# ==========================================
# 3. 모델 학습 (경로 분리 적용)
# ==========================================
def train_hybrid_xgb():
    target_codes = get_hybrid_top_codes()
    if not target_codes:
        print("[-] 학습을 위한 대상 종목이 없어 종료합니다.")
        return

    total_df = load_and_preprocess(target_codes)

    if total_df.empty:
        print("[-] 학습할 데이터가 부족합니다. DB 상태를 확인하세요.")
        return

    # 모델이 학습할 특징(Features) 목록
    features = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']

    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]

    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    # --- 동적 가중치 계산 ---
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()

    print(f"\n📊 [학습 데이터 현황] 일반(0): {neg_count}개 | 스나이퍼 타겟(1): {pos_count}개")

    if pos_count == 0:
        print("🚨 [비상] 정답(1) 데이터가 0개입니다! 타겟 조건을 낮춰야 합니다.")
        dynamic_weight = 1.0
    else:
        dynamic_weight = neg_count / pos_count
        print(f"⚖️ [처방] 정답 예측에 {dynamic_weight:.1f}배의 가중치를 부여합니다.\n")

    print(f"[3/5] XGBoost 모델 최적화 학습 시작 (데이터: {len(X_train)}건)...")
    model = XGBClassifier(
        n_estimators=2000,
        learning_rate=0.005,
        max_depth=5,
        min_child_weight=5,
        gamma=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.05,
        reg_lambda=1.2,
        scale_pos_weight=dynamic_weight,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=100,
        eval_metric='logloss'
    )

    # 💡 최신 XGBoost 버전에 맞춘 early_stopping 방식 (warning 방지)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
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
    print(f"✅ XGBoost 검증 정밀도 (임계값 {threshold:.3f} 기준): {precision:.2%}")
    print("=" * 50)

    # 💡 [핵심] 분리된 경로(data 폴더)에 모델 저장
    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, FEATURE_PATH)
    print(f"[5/5] 모델 파일 저장 완료: {MODEL_PATH}")


if __name__ == "__main__":
    train_hybrid_xgb()