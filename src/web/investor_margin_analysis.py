from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


FLOW_COLUMNS = ["Foreign_Net", "Inst_Net", "Retail_Net"]
FLOW_LABELS = {
    "Foreign_Net": "외국인",
    "Inst_Net": "기관",
    "Retail_Net": "개인",
}


def prepare_flow_analysis(investor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict[str, Any]:
    if investor_df is None or investor_df.empty or price_df is None or price_df.empty:
        return {}

    flow_df = investor_df.copy()
    chart_df = price_df.copy()
    for col in FLOW_COLUMNS:
        if col not in flow_df.columns:
            flow_df[col] = 0
    for col in ["Open", "Close"]:
        if col not in chart_df.columns:
            return {}

    merged = (
        chart_df[["Open", "Close"]]
        .join(flow_df[FLOW_COLUMNS], how="inner")
        .sort_index()
    )
    if merged.empty:
        return {}

    merged["Next_Open"] = merged["Open"].shift(-1)
    merged["Next_Close"] = merged["Close"].shift(-1)
    merged["NextOpen_ReturnPct"] = ((merged["Next_Open"] - merged["Close"]) / merged["Close"]) * 100.0
    merged["NextClose_ReturnPct"] = ((merged["Next_Close"] - merged["Close"]) / merged["Close"]) * 100.0

    history = merged.dropna(subset=["NextOpen_ReturnPct", "NextClose_ReturnPct"]).copy()
    if history.empty or len(history) < 8:
        return {}

    latest = merged.iloc[-1].copy()
    feature_df = history[FLOW_COLUMNS].astype(float)
    means = feature_df.mean()
    stds = feature_df.std(ddof=0).replace(0, 1.0).fillna(1.0)
    z_history = (feature_df - means) / stds
    z_latest = ((latest[FLOW_COLUMNS].astype(float) - means) / stds).fillna(0.0)

    corr_open = _corr_map(history, "NextOpen_ReturnPct")
    corr_close = _corr_map(history, "NextClose_ReturnPct")
    model_open = _fit_linear_model(z_history, history["NextOpen_ReturnPct"], z_latest)
    model_close = _fit_linear_model(z_history, history["NextClose_ReturnPct"], z_latest)
    analog = _nearest_flow_analogs(history, z_history, z_latest)

    predicted_open = _blend_prediction(
        model_open.get("predicted_return_pct"),
        analog.get("avg_open_return_pct"),
    )
    predicted_close = _blend_prediction(
        model_close.get("predicted_return_pct"),
        analog.get("avg_close_return_pct"),
    )
    latest_close = float(latest.get("Close") or 0.0)
    predicted_open_price = latest_close * (1.0 + predicted_open / 100.0) if latest_close > 0 else 0.0
    predicted_close_price = latest_close * (1.0 + predicted_close / 100.0) if latest_close > 0 else 0.0

    score = (predicted_open * 0.35) + (predicted_close * 0.65)
    close_up_prob = float(analog.get("close_up_prob") or 0.0)
    if score >= 0.2 and close_up_prob >= 0.55:
        verdict = "상승 우세"
        tone = "up"
    elif score <= -0.2 and close_up_prob <= 0.45:
        verdict = "하락 우세"
        tone = "down"
    else:
        verdict = "중립"
        tone = "flat"

    driver_rows = []
    for col in FLOW_COLUMNS:
        driver_rows.append(
            {
                "key": col,
                "label": FLOW_LABELS[col],
                "raw": float(latest.get(col) or 0.0),
                "zscore": float(z_latest.get(col) or 0.0),
                "open_contribution_pct": float((model_open.get("contributions") or {}).get(col, 0.0)),
                "close_contribution_pct": float((model_close.get("contributions") or {}).get(col, 0.0)),
            }
        )
    driver_rows.sort(key=lambda item: abs(item["close_contribution_pct"]), reverse=True)

    recent = history.tail(20).copy()
    recent["Date"] = recent.index.strftime("%Y-%m-%d")
    recent["CompositeFlowScore"] = (
        z_history.loc[recent.index, "Foreign_Net"]
        + z_history.loc[recent.index, "Inst_Net"]
        - z_history.loc[recent.index, "Retail_Net"]
    )

    confirmed_last_date = history.index.max()
    latest_pending = None
    if len(merged.index) and len(history.index) and merged.index.max() != confirmed_last_date:
        pending_row = merged.loc[[merged.index.max()]].copy()
        pending_row["Date"] = pending_row.index.strftime("%Y-%m-%d")
        latest_pending = {
            "Date": str(pending_row["Date"].iloc[0]),
            "Close": float(pending_row["Close"].iloc[0] or 0.0),
            "Foreign_Net": float(pending_row["Foreign_Net"].iloc[0] or 0.0),
            "Inst_Net": float(pending_row["Inst_Net"].iloc[0] or 0.0),
            "Retail_Net": float(pending_row["Retail_Net"].iloc[0] or 0.0),
        }

    similar_rows = analog.get("rows", [])
    return {
        "history": history,
        "recent": recent,
        "sample_start_date": history.index.min().strftime("%Y-%m-%d") if hasattr(history.index.min(), "strftime") else str(history.index.min()),
        "sample_end_date": history.index.max().strftime("%Y-%m-%d") if hasattr(history.index.max(), "strftime") else str(history.index.max()),
        "latest_date": latest.name.strftime("%Y-%m-%d") if hasattr(latest.name, "strftime") else str(latest.name),
        "confirmed_last_date": confirmed_last_date.strftime("%Y-%m-%d") if hasattr(confirmed_last_date, "strftime") else str(confirmed_last_date),
        "latest_pending": latest_pending,
        "latest_close": latest_close,
        "latest_flows": {col: float(latest.get(col) or 0.0) for col in FLOW_COLUMNS},
        "latest_zscores": {col: float(z_latest.get(col) or 0.0) for col in FLOW_COLUMNS},
        "correlation": {
            "open": corr_open,
            "close": corr_close,
        },
        "models": {
            "open": model_open,
            "close": model_close,
        },
        "analog": analog,
        "prediction": {
            "verdict": verdict,
            "tone": tone,
            "score": float(score),
            "open_return_pct": float(predicted_open),
            "close_return_pct": float(predicted_close),
            "open_price": float(predicted_open_price),
            "close_price": float(predicted_close_price),
            "close_up_prob": close_up_prob,
            "open_up_prob": float(analog.get("open_up_prob") or 0.0),
        },
        "driver_rows": driver_rows,
        "similar_rows": similar_rows,
        "sample_count": int(len(history)),
    }


def _corr_map(history: pd.DataFrame, target_col: str) -> dict[str, float]:
    cols = FLOW_COLUMNS + [target_col]
    corr = history[cols].corr()[target_col]
    return {col: float(corr.get(col, 0.0)) for col in FLOW_COLUMNS}


def _fit_linear_model(z_history: pd.DataFrame, target: pd.Series, z_latest: pd.Series) -> dict[str, Any]:
    x = z_history[FLOW_COLUMNS].to_numpy(dtype=float)
    y = target.to_numpy(dtype=float)
    if len(x) == 0:
        return {
            "predicted_return_pct": 0.0,
            "r2": 0.0,
            "hit_rate": 0.0,
            "baseline_hit_rate": 0.0,
            "hit_edge": 0.0,
            "mae": 0.0,
            "mean_error": 0.0,
            "up_precision": 0.0,
            "down_precision": 0.0,
            "rmse": 0.0,
            "contributions": {col: 0.0 for col in FLOW_COLUMNS},
        }

    x_design = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(x_design, y, rcond=None)
    fitted = x_design @ beta
    residual = y - fitted
    ss_tot = float(((y - y.mean()) ** 2).sum())
    ss_res = float((residual ** 2).sum())
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    rmse = math.sqrt(float(np.mean(residual ** 2))) if len(residual) else 0.0
    mae = float(np.mean(np.abs(residual))) if len(residual) else 0.0
    mean_error = float(np.mean(residual)) if len(residual) else 0.0
    direction = _direction_metrics(fitted, y)

    latest_vec = z_latest[FLOW_COLUMNS].to_numpy(dtype=float)
    predicted = float(beta[0] + np.dot(latest_vec, beta[1:]))
    contributions = {
        FLOW_COLUMNS[idx]: float(beta[idx + 1] * latest_vec[idx])
        for idx in range(len(FLOW_COLUMNS))
    }

    return {
        "predicted_return_pct": predicted,
        "r2": float(r2),
        "hit_rate": float(direction["hit_rate"]),
        "baseline_hit_rate": float(direction["baseline_hit_rate"]),
        "hit_edge": float(direction["hit_edge"]),
        "mae": float(mae),
        "mean_error": float(mean_error),
        "up_precision": float(direction["up_precision"]),
        "down_precision": float(direction["down_precision"]),
        "rmse": float(rmse),
        "contributions": contributions,
    }


def _direction_metrics(fitted: np.ndarray, actual: np.ndarray) -> dict[str, float]:
    if len(actual) == 0:
        return {
            "hit_rate": 0.0,
            "baseline_hit_rate": 0.0,
            "hit_edge": 0.0,
            "up_precision": 0.0,
            "down_precision": 0.0,
        }

    predicted_up = fitted >= 0
    actual_up = actual >= 0
    hit_rate = float(np.mean(predicted_up == actual_up))
    up_share = float(np.mean(actual_up))
    baseline_hit_rate = max(up_share, 1.0 - up_share)
    predicted_down = ~predicted_up
    up_precision = float(np.mean(actual_up[predicted_up])) if bool(predicted_up.any()) else 0.0
    down_precision = float(np.mean((~actual_up)[predicted_down])) if bool(predicted_down.any()) else 0.0
    return {
        "hit_rate": hit_rate,
        "baseline_hit_rate": baseline_hit_rate,
        "hit_edge": hit_rate - baseline_hit_rate,
        "up_precision": up_precision,
        "down_precision": down_precision,
    }


def _nearest_flow_analogs(
    history: pd.DataFrame,
    z_history: pd.DataFrame,
    z_latest: pd.Series,
) -> dict[str, Any]:
    x = z_history[FLOW_COLUMNS].to_numpy(dtype=float)
    latest_vec = z_latest[FLOW_COLUMNS].to_numpy(dtype=float)
    if len(x) == 0:
        return {
            "sample_count": 0,
            "open_up_prob": 0.0,
            "close_up_prob": 0.0,
            "avg_open_return_pct": 0.0,
            "avg_close_return_pct": 0.0,
            "rows": [],
        }

    distances = np.sqrt(((x - latest_vec) ** 2).sum(axis=1))
    analog_df = history.copy()
    analog_df["Distance"] = distances
    sample_count = max(6, min(15, len(analog_df)))
    analog_df = analog_df.sort_values("Distance").head(sample_count)

    rows = []
    for idx, row in analog_df.iterrows():
        rows.append(
            {
                "Date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
                "Distance": float(row.get("Distance") or 0.0),
                "NextOpen_ReturnPct": float(row.get("NextOpen_ReturnPct") or 0.0),
                "NextClose_ReturnPct": float(row.get("NextClose_ReturnPct") or 0.0),
            }
        )

    return {
        "sample_count": int(len(analog_df)),
        "open_up_prob": float((analog_df["NextOpen_ReturnPct"] >= 0).mean()) if len(analog_df) else 0.0,
        "close_up_prob": float((analog_df["NextClose_ReturnPct"] >= 0).mean()) if len(analog_df) else 0.0,
        "avg_open_return_pct": float(analog_df["NextOpen_ReturnPct"].mean()) if len(analog_df) else 0.0,
        "avg_close_return_pct": float(analog_df["NextClose_ReturnPct"].mean()) if len(analog_df) else 0.0,
        "rows": rows,
    }


def _blend_prediction(model_pred: float | None, analog_pred: float | None) -> float:
    model_val = float(model_pred or 0.0)
    analog_val = float(analog_pred or 0.0)
    return (model_val * 0.5) + (analog_val * 0.5)
