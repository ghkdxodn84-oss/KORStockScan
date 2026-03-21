import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ml_v2_common import (
    get_period_liquid_codes, build_panel,
    HYBRID_XGB_PACK, HYBRID_LGBM_PACK, BULL_XGB_PACK, BULL_LGBM_PACK,
    META_MODEL_PACK, AI_PRED_PATH, AI_PICKS_PATH,
    META_FEATURES, load_pickle, save_pickle,
    build_meta_frame, print_basic_report, print_topk_report,
    select_daily_topk
)

# =========================================================
# 메타 학습 / 스코어링 기간
# =========================================================
META_START  = '2026-01-16'
META_END    = '2026-02-28'

# 아래는 메타 학습 후 실제 스코어링/백테스트용 기간
SCORE_START = '2026-03-01'
SCORE_END   = '2026-04-30'

TARGET_COL = 'Target_Strict'

def main():
    # 1) base model pack 로드
    hx_pack = load_pickle(HYBRID_XGB_PACK)
    hl_pack = load_pickle(HYBRID_LGBM_PACK)
    bx_pack = load_pickle(BULL_XGB_PACK)
    bl_pack = load_pickle(BULL_LGBM_PACK)

    # 2) universe
    codes = get_period_liquid_codes(META_START, SCORE_END, top_n=300, min_days=30)
    if not codes:
        print("❌ 메타 학습/스코어링 universe가 없습니다.")
        return

    # 3) panel 생성
    meta_panel = build_panel(codes, META_START, META_END, warmup_days=160, min_rows=60, with_target=True)
    score_panel = build_panel(codes, SCORE_START, SCORE_END, warmup_days=160, min_rows=60, with_target=True)

    if meta_panel.empty:
        print("❌ meta_panel이 비어 있습니다.")
        return

    # 4) 메타 피처 생성
    meta_df = build_meta_frame(meta_panel, hx_pack, hl_pack, bx_pack, bl_pack)

    # 5) 메타 구간 내부 시계열 split (80/20)
    dates = sorted(meta_df['Date'].unique())
    split_date = dates[int(len(dates) * 0.8)]

    meta_train = meta_df[meta_df['Date'] < split_date].copy()
    meta_valid = meta_df[meta_df['Date'] >= split_date].copy()

    if meta_train.empty or meta_valid.empty:
        print("❌ meta_train / meta_valid 분할 실패")
        return

    y_train = meta_train[TARGET_COL]
    y_valid = meta_valid[TARGET_COL]

    print(f"[Meta] Train/Valid = {len(meta_train):,}/{len(meta_valid):,}")
    print(f"[Meta] Strict Pos Ratio(train) = {(y_train == 1).mean():.2%}")

    meta_model = LogisticRegression(
        max_iter=1000,
        C=0.3,
        random_state=42
    )
    meta_model.fit(meta_train[META_FEATURES], y_train)

    valid_score = meta_model.predict_proba(meta_valid[META_FEATURES])[:, 1]
    valid_rep = meta_valid[['Date', 'Code', TARGET_COL, 'Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio', 'Breakout_20', 'Turnover_Shock']].copy()
    valid_rep['Meta_Score'] = valid_score

    print_basic_report("Meta Valid", y_valid, valid_score)
    print_topk_report("Meta Valid", valid_rep, 'Meta_Score', TARGET_COL)

    print("\n[전문가 의견 상관관계]")
    print(valid_rep[['Meta_Score']].join(meta_valid[['HX', 'HL', 'BX', 'BL']]).corr().round(3))

    # 6) 전체 meta 기간으로 재학습
    final_meta_model = LogisticRegression(
        max_iter=1000,
        C=0.3,
        random_state=42
    )
    final_meta_model.fit(meta_df[META_FEATURES], meta_df[TARGET_COL])

    meta_pack = {
        'model': final_meta_model,
        'features': META_FEATURES,
        'target_col': TARGET_COL,
        'meta_start': META_START,
        'meta_end': META_END
    }
    save_pickle(meta_pack, META_MODEL_PACK)
    print(f"✅ 메타 모델 저장 완료: {META_MODEL_PACK}")

    # 7) score_panel 스코어링
    if score_panel.empty:
        print("⚠️ score_panel이 비어 있어 예측 파일 생성은 생략합니다.")
        return

    score_df = build_meta_frame(score_panel, hx_pack, hl_pack, bx_pack, bl_pack)
    score_df['Meta_Score'] = final_meta_model.predict_proba(score_df[META_FEATURES])[:, 1]

    # 전체 예측 저장
    pred_cols = [
        'Date', 'Code', 'HX', 'HL', 'BX', 'BL',
        'Mean_Prob', 'Std_Prob', 'Max_Prob', 'Min_Prob',
        'Bull_Mean', 'Hybrid_Mean', 'Bull_Hybrid_Gap',
        'Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio',
        'Breakout_20', 'Turnover_Shock',
        'Meta_Score', 'Target_Strict', 'Realized_Ret_3D'
    ]
    score_out = score_df[pred_cols].copy().sort_values(['Date', 'Meta_Score'], ascending=[True, False])
    score_out.to_csv(AI_PRED_PATH, index=False, encoding='utf-8-sig')
    print(f"✅ 전체 예측 저장 완료: {AI_PRED_PATH}")

    # 8) 최종 추천 종목 선정: daily top-k + regime floor
    picks = select_daily_topk(
        score_out,
        score_col='Meta_Score',
        top_k_bull=5,
        top_k_bear=2,
        floor_bull=0.46,
        floor_bear=0.52,
        fallback_bull_floor=0.43
    )

    if picks.empty:
        print("⚠️ 선택된 추천 종목이 없습니다.")
    else:
        picks.to_csv(AI_PICKS_PATH, index=False, encoding='utf-8-sig')
        print(f"✅ 최종 추천 저장 완료: {AI_PICKS_PATH}")
        print(f"   - 총 추천 수: {len(picks):,}")
        print(f"   - 추천 일수: {picks['Date'].nunique():,}")

        if 'Target_Strict' in picks.columns:
            print(f"   - Pick Precision(Strict): {picks['Target_Strict'].mean():.2%}")
        if 'Realized_Ret_3D' in picks.columns:
            print(f"   - Pick Avg Realized 3D Return: {picks['Realized_Ret_3D'].mean():.2%}")

if __name__ == "__main__":
    main()