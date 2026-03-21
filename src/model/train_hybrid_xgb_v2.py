import numpy as np
from xgboost import XGBClassifier
from sklearn.isotonic import IsotonicRegression

from ml_v2_common import (
    get_period_liquid_codes, build_panel, split_dates_4way, recency_weights,
    XGB_FEATURES, HYBRID_XGB_PACK, save_pickle,
    build_model_pack, print_basic_report, print_topk_report
)

# =========================================================
# 학습 구간 설정
# =========================================================
BASE_START = '2024-11-01'
BASE_END   = '2026-01-15'
TARGET_COL = 'Target_Loose'

def main():
    codes = get_period_liquid_codes(BASE_START, BASE_END, top_n=300, min_days=80)
    if not codes:
        print("❌ 학습 universe가 없습니다.")
        return

    panel = build_panel(codes, BASE_START, BASE_END, warmup_days=160, min_rows=150, with_target=True)
    if panel.empty:
        print("❌ 학습 패널이 비어 있습니다.")
        return

    train_df, valid_df, calib_df, test_df = split_dates_4way(panel)

    y_train = train_df[TARGET_COL]
    y_valid = valid_df[TARGET_COL]
    y_calib = calib_df[TARGET_COL]
    y_test = test_df[TARGET_COL]

    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_weight = 1.0 if pos == 0 else neg / pos
    sample_weight = recency_weights(train_df['Date'], half_life_days=90)

    print(f"[Hybrid XGB] Train/Valid/Calib/Test = {len(train_df):,}/{len(valid_df):,}/{len(calib_df):,}/{len(test_df):,}")
    print(f"[Hybrid XGB] Pos Ratio(train) = {pos / max(len(y_train), 1):.2%}, scale_pos_weight={scale_pos_weight:.2f}")

    model = XGBClassifier(
        n_estimators=1000,
        learning_rate=0.03,
        max_depth=4,
        min_child_weight=10,
        gamma=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.5,
        reg_lambda=2.0,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        eval_metric='aucpr',
        early_stopping_rounds=100
    )

    model.fit(
        train_df[XGB_FEATURES], y_train,
        sample_weight=sample_weight,
        eval_set=[(valid_df[XGB_FEATURES], y_valid)],
        verbose=100
    )

    calib_raw = model.predict_proba(calib_df[XGB_FEATURES])[:, 1]
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(calib_raw, y_calib)

    test_prob = calibrator.transform(model.predict_proba(test_df[XGB_FEATURES])[:, 1])

    report_df = test_df[['Date', 'Code', TARGET_COL]].copy()
    report_df['Score'] = test_prob

    print_basic_report("Hybrid XGB Test", y_test, test_prob)
    print_topk_report("Hybrid XGB Test", report_df, 'Score', TARGET_COL)

    pack = build_model_pack(
        model=model,
        calibrator=calibrator,
        features=XGB_FEATURES,
        target_col=TARGET_COL,
        name='hybrid_xgb_v2',
        extra={
            'base_start': BASE_START,
            'base_end': BASE_END
        }
    )
    save_pickle(pack, HYBRID_XGB_PACK)
    print(f"✅ 저장 완료: {HYBRID_XGB_PACK}")

if __name__ == "__main__":
    main()