from xgboost import XGBClassifier
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.isotonic import IsotonicRegression

from ml_v2_common import (
    get_period_liquid_codes, build_panel, split_dates_4way, recency_weights,
    XGB_FEATURES, LGBM_FEATURES,
    BULL_XGB_PACK, BULL_LGBM_PACK, save_pickle,
    build_model_pack, print_basic_report, print_topk_report
)

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

    # 날짜기반 bull 기간이 아니라, Bull_Regime 상태 기반으로 필터
    bull_panel = panel[panel['Bull_Regime'] == 1].copy()
    if bull_panel.empty:
        print("❌ Bull_Regime=1 데이터가 없습니다.")
        return

    train_df, valid_df, calib_df, test_df = split_dates_4way(bull_panel)

    y_train = train_df[TARGET_COL]
    y_valid = valid_df[TARGET_COL]
    y_calib = calib_df[TARGET_COL]
    y_test = test_df[TARGET_COL]

    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_weight = 1.0 if pos == 0 else neg / pos
    sample_weight = recency_weights(train_df['Date'], half_life_days=63)

    print(f"[Bull Specialists] Rows = {len(bull_panel):,}, Pos Ratio(train) = {pos / max(len(y_train), 1):.2%}")

    # -----------------------------------------------------
    # Bull XGB
    # -----------------------------------------------------
    bull_xgb = XGBClassifier(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=4,
        min_child_weight=8,
        gamma=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.5,
        reg_lambda=2.0,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        eval_metric='aucpr',
        early_stopping_rounds=100
    )

    bull_xgb.fit(
        train_df[XGB_FEATURES], y_train,
        sample_weight=sample_weight,
        eval_set=[(valid_df[XGB_FEATURES], y_valid)],
        verbose=100
    )

    xgb_cal_raw = bull_xgb.predict_proba(calib_df[XGB_FEATURES])[:, 1]
    xgb_cal = IsotonicRegression(out_of_bounds='clip').fit(xgb_cal_raw, y_calib)

    xgb_test_prob = xgb_cal.transform(bull_xgb.predict_proba(test_df[XGB_FEATURES])[:, 1])
    xgb_rep = test_df[['Date', 'Code', TARGET_COL]].copy()
    xgb_rep['Score'] = xgb_test_prob

    print_basic_report("Bull XGB Test", y_test, xgb_test_prob)
    print_topk_report("Bull XGB Test", xgb_rep, 'Score', TARGET_COL)

    xgb_pack = build_model_pack(
        model=bull_xgb,
        calibrator=xgb_cal,
        features=XGB_FEATURES,
        target_col=TARGET_COL,
        name='bull_xgb_v2',
        extra={'base_start': BASE_START, 'base_end': BASE_END}
    )
    save_pickle(xgb_pack, BULL_XGB_PACK)

    # -----------------------------------------------------
    # Bull LGBM
    # -----------------------------------------------------
    bull_lgbm = LGBMClassifier(
        n_estimators=800,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=5,
        min_child_samples=30,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        force_col_wise=True
    )

    bull_lgbm.fit(
        train_df[LGBM_FEATURES], y_train,
        sample_weight=sample_weight,
        eval_set=[(valid_df[LGBM_FEATURES], y_valid)],
        eval_metric='auc',
        callbacks=[early_stopping(100), log_evaluation(100)]
    )

    lgbm_cal_raw = bull_lgbm.predict_proba(calib_df[LGBM_FEATURES])[:, 1]
    lgbm_cal = IsotonicRegression(out_of_bounds='clip').fit(lgbm_cal_raw, y_calib)

    lgbm_test_prob = lgbm_cal.transform(bull_lgbm.predict_proba(test_df[LGBM_FEATURES])[:, 1])
    lgbm_rep = test_df[['Date', 'Code', TARGET_COL]].copy()
    lgbm_rep['Score'] = lgbm_test_prob

    print_basic_report("Bull LGBM Test", y_test, lgbm_test_prob)
    print_topk_report("Bull LGBM Test", lgbm_rep, 'Score', TARGET_COL)

    lgbm_pack = build_model_pack(
        model=bull_lgbm,
        calibrator=lgbm_cal,
        features=LGBM_FEATURES,
        target_col=TARGET_COL,
        name='bull_lgbm_v2',
        extra={'base_start': BASE_START, 'base_end': BASE_END}
    )
    save_pickle(lgbm_pack, BULL_LGBM_PACK)

    print(f"✅ 저장 완료: {BULL_XGB_PACK}, {BULL_LGBM_PACK}")

if __name__ == "__main__":
    main()