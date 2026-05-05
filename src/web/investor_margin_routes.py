"""Kiwoom 기반 수급-익일 상관관계 + 미수 증거금 계산 뷰."""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

import pandas as pd
from flask import Blueprint, jsonify, request, render_template_string

from src.utils import kiwoom_utils
from src.web.investor_margin_analysis import FLOW_COLUMNS, FLOW_LABELS, prepare_flow_analysis


investor_margin_bp = Blueprint("investor_margin", __name__)


def _to_int(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    try:
        s = str(value).replace(",", "").replace("+", "")
        if s.strip() == "":
            return 0
        return int(float(s))
    except (TypeError, ValueError):
        return 0


def _to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    try:
        s = str(value).replace(",", "").replace("+", "")
        if s.strip() == "":
            return 0.0
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def _normalize_name(text: str) -> str:
    return "".join(ch for ch in str(text or "").replace(" ", "").upper())


def _is_code_like(raw: str) -> bool:
    normalized = kiwoom_utils.normalize_stock_code(raw)
    return normalized.isdigit() and len(normalized) == 6


@lru_cache(maxsize=32)
def _load_all_stocks_cached(token: str, market_types_key: str = "0,10") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    market_types = tuple(market_types_key.split(","))
    url = kiwoom_utils.get_api_url("/api/dostk/stkinfo")

    for market_tp in market_types:
        payload = {"mrkt_tp": str(market_tp)}
        results = kiwoom_utils.fetch_kiwoom_api_continuous(
            url=url,
            token=token,
            api_id="ka10099",
            payload=payload,
            use_continuous=True,
        )

        for res in results:
            for item in res.get("list", []) or []:
                code = kiwoom_utils.normalize_stock_code(
                    item.get("code")
                    or item.get("stk_cd")
                    or item.get("stock_code")
                    or ""
                )
                if not (code.isdigit() and len(code) == 6):
                    continue
                name = (
                    item.get("stk_nm")
                    or item.get("name")
                    or item.get("stock_name")
                    or ""
                )
                if code in seen:
                    continue
                seen.add(code)
                rows.append((code, str(name).strip()))

    rows = sorted(set(rows))
    return rows


def _search_stocks_by_name(query: str, token: str, limit: int = 40) -> list[tuple[str, str]]:
    if not query:
        return []
    stocks = _load_all_stocks_cached(token)
    if not stocks:
        return []

    q = _normalize_name(query)
    matched = [item for item in stocks if q in _normalize_name(item[1])]
    exact = [item for item in matched if _normalize_name(item[1]) == _normalize_name(query)]
    if exact:
        matched = exact
    return matched[:limit]


def _resolve_stock_code(
    stock_query: str,
    token: str,
    forced_code: str = "",
) -> tuple[str | None, str | None, list[tuple[str, str]]]:
    query = str(stock_query or "").strip()
    if not query:
        return None, None, []

    if forced_code and _is_code_like(forced_code):
        code = kiwoom_utils.normalize_stock_code(forced_code)
        try:
            info = kiwoom_utils.get_item_info_ka10100(token, code) or {}
            name = str(info.get("stk_nm") or "").strip() or None
        except Exception:
            name = None
        return code, name, [(code, name or "")]

    if _is_code_like(query):
        code = kiwoom_utils.normalize_stock_code(query)
        try:
            info = kiwoom_utils.get_item_info_ka10100(token, code) or {}
            name = str(info.get("stk_nm") or "").strip() or None
        except Exception:
            name = None
        return code, name, [(code, name or "")]

    candidates = _search_stocks_by_name(query, token)
    if not candidates:
        return None, None, []
    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1], candidates
    return None, None, candidates


def _load_investor_and_prices(token: str, code: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    investor_df = _load_extended_investor_daily(token, code)
    price_df = _load_extended_daily_prices(token, code)

    if investor_df is None:
        investor_df = pd.DataFrame()
    if price_df is None:
        price_df = pd.DataFrame()
    return investor_df.copy(), price_df.copy()


def _load_extended_investor_daily(token: str, code: str, target_rows: int = 140, max_pages: int = 8) -> pd.DataFrame:
    pages = []
    base_dt = ""
    for _ in range(max_pages):
        page = kiwoom_utils.get_investor_daily_ka10059_df(token, code, base_dt=base_dt or None)
        if page is None or page.empty:
            break
        pages.append(page.copy())
        combined = pd.concat(pages).sort_index()
        combined = combined[~combined.index.duplicated(keep="first")]
        if len(combined) >= target_rows:
            return combined.tail(target_rows)
        earliest = combined.index.min()
        if not hasattr(earliest, "strftime"):
            break
        base_dt = (earliest - timedelta(days=1)).strftime("%Y%m%d")
    if not pages:
        return pd.DataFrame()
    combined = pd.concat(pages).sort_index()
    combined = combined[~combined.index.duplicated(keep="first")]
    return combined.tail(target_rows)


def _load_extended_daily_prices(token: str, code: str, target_rows: int = 180, max_pages: int = 4) -> pd.DataFrame:
    pages = []
    end_date = ""
    for _ in range(max_pages):
        page = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code, end_date=end_date)
        if page is None or page.empty:
            break
        pages.append(page.copy())
        combined = pd.concat(pages).sort_index()
        combined = combined[~combined.index.duplicated(keep="first")]
        if len(combined) >= target_rows:
            return combined.tail(target_rows)
        earliest = combined.index.min()
        if not hasattr(earliest, "strftime"):
            break
        end_date = (earliest - timedelta(days=1)).strftime("%Y%m%d")
    if not pages:
        return pd.DataFrame()
    combined = pd.concat(pages).sort_index()
    combined = combined[~combined.index.duplicated(keep="first")]
    return combined.tail(target_rows)


def _prepare_flow_return_correlation(
    investor_df: pd.DataFrame,
    price_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    if investor_df.empty or price_df.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    required_cols = ["Foreign_Net", "Inst_Net", "Retail_Net"]
    for col in required_cols:
        if col not in investor_df.columns:
            investor_df[col] = 0

    merged = (
        price_df[["Close"]]
        .join(investor_df[required_cols], how="inner")
        .sort_index()
    )
    if merged.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    merged["Next_Close"] = merged["Close"].shift(-1)
    merged["NextDay_ReturnPct"] = ((merged["Next_Close"] - merged["Close"]) / merged["Close"]) * 100.0
    merged = merged.dropna(subset=["NextDay_ReturnPct"])
    if merged.empty:
        return merged, pd.Series(dtype=float)

    corr = merged[["Foreign_Net", "Inst_Net", "Retail_Net", "NextDay_ReturnPct"]].corr()[
        "NextDay_ReturnPct"
    ]
    corr = corr.loc[["Foreign_Net", "Inst_Net", "Retail_Net"]]
    return merged, corr


def _current_price_from_kiwoom(token: str, code: str) -> tuple[int, str]:
    price = 0
    reason = ""
    try:
        info = kiwoom_utils.get_item_info_ka10100(token, code)
    except Exception:
        info = None

    if info:
        for key in ["cur_prc", "past_curr_prc", "close_prc", "curPrice", "stck_prc", "현재가", "Close"]:
            if key in info:
                v = _to_int(info[key])
                if v > 0:
                    price = v
                    reason = f"kiwoom 기본정보 필드 사용: {key}"
                    break

    if price <= 0:
        try:
            price_df = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
            if price_df is not None and not price_df.empty:
                latest_close = _to_int(price_df["Close"].iloc[-1])
                if latest_close > 0:
                    price = latest_close
                    reason = "일봉 마지막 종가 사용"
        except Exception:
            price = 0

    return price, reason


def _load_credit_balance_rate(token: str, code: str) -> int:
    """ka10013 remn_rt is credit balance ratio, not margin requirement rate."""
    margin_df = kiwoom_utils.get_margin_daily_ka10013_df(token, code)
    if margin_df is None or margin_df.empty:
        return 0
    if "Margin_Rate" not in margin_df.columns:
        return 0
    raw = _to_float(margin_df["Margin_Rate"].iloc[-1])
    return int(round(raw)) if raw > 0 else 0


def _load_margin_requirement_info(token: str, code: str, current_price: int) -> dict[str, Any]:
    return kiwoom_utils.get_orderable_by_margin_kt00011(token, code, unit_price=current_price) or {}


def _format_number(v: Any) -> str:
    try:
        return f"{int(round(float(v))):,}"
    except (TypeError, ValueError):
        return "-"


def _format_pct(v: float) -> str:
    if v is None or pd.isna(v):
        return "-"
    try:
        num = float(v)
    except (TypeError, ValueError):
        return "-"
    sign = "+" if num >= 0 else ""
    return f"{sign}{num:.2f}%"


def _format_ratio(v: float) -> str:
    return f"{float(v or 0.0) * 100:.1f}%"


def _tone_from_value(value: float, positive_cutoff: float = 0.0, negative_cutoff: float = 0.0) -> str:
    if value > positive_cutoff:
        return "up"
    if value < negative_cutoff:
        return "down"
    return "flat"


def _build_corr_rows(corr_map: dict[str, float]) -> list[dict[str, Any]]:
    max_abs = max(0.05, max(abs(float(corr_map.get(col, 0.0))) for col in FLOW_COLUMNS))
    rows = []
    for col in FLOW_COLUMNS:
        value = float(corr_map.get(col, 0.0))
        rows.append(
            {
                "label": FLOW_LABELS[col],
                "display": f"{value:+.4f}",
                "tone": _tone_from_value(value, 0.02, -0.02),
                "side": "pos" if value >= 0 else "neg",
                "width_pct": min(100.0, (abs(value) / max_abs) * 100.0),
            }
        )
    return rows


def _build_driver_rows(driver_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_abs = max(0.5, max(abs(float(row.get("zscore") or 0.0)) for row in driver_rows)) if driver_rows else 1.0
    rows = []
    for row in driver_rows:
        zscore = float(row.get("zscore") or 0.0)
        close_contrib = float(row.get("close_contribution_pct") or 0.0)
        rows.append(
            {
                "label": row.get("label"),
                "raw": _format_number(row.get("raw")),
                "zscore": f"{zscore:+.2f}",
                "close_contribution": _format_pct(close_contrib),
                "tone": _tone_from_value(close_contrib, 0.02, -0.02),
                "side": "pos" if zscore >= 0 else "neg",
                "width_pct": min(100.0, (abs(zscore) / max_abs) * 100.0),
            }
        )
    return rows


def _build_recent_return_bars(recent_df: pd.DataFrame) -> list[dict[str, Any]]:
    if recent_df is None or recent_df.empty:
        return []
    max_abs = max(
        0.2,
        float(
            recent_df[["NextOpen_ReturnPct", "NextClose_ReturnPct"]]
            .abs()
            .max()
            .max()
            or 0.2
        ),
    )
    bars = []
    for _, row in recent_df.tail(20).iterrows():
        open_ret = float(row.get("NextOpen_ReturnPct") or 0.0)
        close_ret = float(row.get("NextClose_ReturnPct") or 0.0)
        bars.append(
            {
                "date": str(row.get("Date")),
                "open_height": max(4, int((abs(open_ret) / max_abs) * 108)),
                "close_height": max(4, int((abs(close_ret) / max_abs) * 108)),
                "open_tone": _tone_from_value(open_ret, 0.0, 0.0),
                "close_tone": _tone_from_value(close_ret, 0.0, 0.0),
                "open_display": _format_pct(open_ret),
                "close_display": _format_pct(close_ret),
            }
        )
    return bars


def _build_common_context() -> dict[str, object]:
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@investor_margin_bp.route("/api/investor-margin")
def investor_margin_api():
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        return jsonify({"ok": False, "error": "Kiwoom token not available"})

    mode = request.args.get("mode", "flow")
    stock_query = (request.args.get("stock_query") or "").strip()
    stock_code = (request.args.get("stock_code") or "").strip()
    quantity = request.args.get("quantity", "10").strip()
    try:
        qty = max(1, int(float(quantity)))
    except (TypeError, ValueError):
        qty = 10

    result: dict[str, Any] = {
        "ok": True,
        "mode": mode,
        "stock_query": stock_query,
        "stock_code": stock_code,
        "quantity": qty,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if mode == "margin":
        code, name_guess, candidates = _resolve_stock_code(stock_query, token, stock_code)
        if code is None:
            if candidates:
                result.update({"ok": False, "reason": "multiple_candidates", "candidates": candidates})
            else:
                result.update({"ok": False, "error": "stock_not_found"})
            return jsonify(result)
        current_price, price_source = _current_price_from_kiwoom(token, code)
        margin_info = _load_margin_requirement_info(token, code, current_price)
        if margin_info.get("error"):
            result.update(
                {
                    "code": code,
                    "name": name_guess,
                    "current_price": current_price,
                    "price_source": price_source,
                    "error": str(margin_info.get("error")),
                }
            )
            return jsonify(result)
        applied_margin_rate = int(margin_info.get("applied_margin_rate") or 0)
        stock_margin_rate = int(margin_info.get("stock_margin_rate") or 0)
        required_margin = int(current_price * qty * applied_margin_rate / 100) if current_price > 0 and applied_margin_rate > 0 else 0
        result.update(
            {
                "code": code,
                "name": name_guess,
                "current_price": current_price,
                "price_source": price_source,
                "stock_margin_rate": stock_margin_rate,
                "applied_margin_rate": applied_margin_rate,
                "required_margin": required_margin,
                "orderable_qty_for_applied_rate": ((margin_info.get("tiers") or {}).get(applied_margin_rate) or {}).get("orderable_qty", 0),
                "orderable_amount_for_applied_rate": ((margin_info.get("tiers") or {}).get(applied_margin_rate) or {}).get("orderable_amount", 0),
            }
        )
        return jsonify(result)

    code, name_guess, candidates = _resolve_stock_code(stock_query, token, stock_code)
    if code is None:
        if candidates:
            result.update({"ok": False, "reason": "multiple_candidates", "candidates": candidates})
        else:
            result.update({"ok": False, "error": "stock_not_found"})
        return jsonify(result)
    investor_df, price_df = _load_investor_and_prices(token, code)
    analysis = prepare_flow_analysis(investor_df, price_df)
    if not analysis:
        result.update({"ok": False, "error": "not_enough_overlap", "code": code, "name": name_guess})
        return jsonify(result)
    recent = analysis["recent"].tail(20).reset_index(drop=True).copy()
    result.update(
        {
            "code": code,
            "name": name_guess,
            "correlation": {
                "open": analysis["correlation"]["open"],
                "close": analysis["correlation"]["close"],
            },
            "prediction": analysis["prediction"],
            "model_quality": {
                "open": {
                    "r2": analysis["models"]["open"]["r2"],
                    "hit_rate": analysis["models"]["open"]["hit_rate"],
                    "baseline_hit_rate": analysis["models"]["open"]["baseline_hit_rate"],
                    "hit_edge": analysis["models"]["open"]["hit_edge"],
                    "mae": analysis["models"]["open"]["mae"],
                    "up_precision": analysis["models"]["open"]["up_precision"],
                    "down_precision": analysis["models"]["open"]["down_precision"],
                },
                "close": {
                    "r2": analysis["models"]["close"]["r2"],
                    "hit_rate": analysis["models"]["close"]["hit_rate"],
                    "baseline_hit_rate": analysis["models"]["close"]["baseline_hit_rate"],
                    "hit_edge": analysis["models"]["close"]["hit_edge"],
                    "mae": analysis["models"]["close"]["mae"],
                    "up_precision": analysis["models"]["close"]["up_precision"],
                    "down_precision": analysis["models"]["close"]["down_precision"],
                },
            },
            "sample_rows": recent.to_dict(orient="records"),
            "sample_count": int(analysis["sample_count"]),
        }
    )
    return jsonify(result)


@investor_margin_bp.route("/investor-margin")
def investor_margin_view():
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        return render_template_string(
            "<div style='padding:16px;font-family:Pretendard,Noto Sans KR,sans-serif;'>"
            "<h2>Kiwoom 인증 실패</h2><p>키움 토큰 획득에 실패했습니다.</p>"
            "</div>"
        )

    mode = (request.values.get("mode") or "flow").strip() or "flow"
    stock_query = (request.values.get("stock_query") or "").strip()
    stock_code = (request.values.get("stock_code") or "").strip()
    qty_text = (request.values.get("quantity") or "10").strip()
    try:
        quantity = max(1, int(float(qty_text)))
    except (TypeError, ValueError):
        quantity = 10

    flow_result = None
    margin_result = None
    if mode == "margin" and stock_query:
        margin_result = _build_margin_result(token, stock_query, stock_code, quantity)
    elif stock_query:
        flow_result = _build_flow_result(token, stock_query, stock_code)

    template = """
    <!doctype html>
    <html lang=\"ko\">
    <head>
      <meta charset=\"utf-8\">
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
      <title>KORStockScan 수급-미수 통합 화면</title>
      <style>
        :root {
          --bg: #f4f7ef;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
          --warn: #b7791f;
          --bad: #b83232;
        }
        body {
          margin: 0;
          background: linear-gradient(180deg, #eef6ef 0%, var(--bg) 100%);
          color: var(--ink);
          font-family: \"Pretendard\", \"Noto Sans KR\", sans-serif;
        }
        .wrap { max-width: 1120px; margin: 0 auto; padding: 24px 16px 40px; }
        .hero { background: linear-gradient(135deg, #183153, #1d7a52); color: #fff; padding: 20px; border-radius: 20px; }
        .hero h1 { margin: 0 0 8px; }
        .toolbar { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
        .toolbar a { color: #fff; text-decoration: none; padding: 8px 12px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.4); }
        .toolbar a.active { background: rgba(255,255,255,0.2); }
        .panel { margin-top: 18px; background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 16px; }
        form { display: grid; gap: 8px; grid-template-columns: 1fr 130px auto; align-items: end; }
        .wide { grid-template-columns: 1fr auto; }
        .section { margin-top: 16px; }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; }
        .chip { background: #e7efe5; padding: 6px 10px; border-radius: 999px; font-size: 12px; }
        input, button, select {
          border: 1px solid var(--line);
          border-radius: 10px;
          padding: 10px 12px;
          font-size: 14px;
          background: white;
        }
        button { background: var(--accent); color: #fff; border-color: var(--accent); cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border-top: 1px solid var(--line); padding: 9px 8px; text-align: left; font-size: 13px; }
        th { color: var(--muted); text-transform: uppercase; font-size: 12px; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 10px; }
        .corr-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 8px; }
        .corr-item { background: #f6faf5; border: 1px solid var(--line); border-radius: 12px; padding: 10px; }
        .corr-label { color: var(--muted); font-size: 12px; }
        .corr-value { font-size: 22px; font-weight: 700; margin-top: 4px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin-top: 12px; }
        .metric-card { background: #f6faf5; border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
        .metric-title { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .metric-value { font-size: 22px; font-weight: 800; }
        .dual-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
        .chart-card { background: #f9fcf8; border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
        .chart-card h4 { margin: 0 0 10px; font-size: 15px; }
        .corr-row { display: grid; grid-template-columns: 56px 1fr 64px; gap: 10px; align-items: center; margin-top: 8px; }
        .corr-row:first-child { margin-top: 0; }
        .corr-name { font-size: 12px; color: var(--muted); }
        .corr-track { position: relative; height: 18px; border-radius: 999px; background: #eef3ec; overflow: hidden; }
        .corr-track::before { content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: #c9d5ca; }
        .corr-bar { position: absolute; top: 3px; height: 12px; border-radius: 999px; }
        .corr-bar.pos { left: 50%; background: #1d7a52; }
        .corr-bar.neg { right: 50%; background: #b83232; }
        .tone-up { color: var(--accent); }
        .tone-down { color: var(--bad); }
        .tone-flat { color: var(--warn); }
        .driver-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
        .driver-card { background: #f9fcf8; border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
        .driver-head { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
        .driver-name { font-weight: 700; }
        .driver-raw { color: var(--muted); font-size: 12px; margin-top: 6px; }
        .z-track { position: relative; height: 16px; border-radius: 999px; background: #eef3ec; margin-top: 10px; overflow: hidden; }
        .z-track::before { content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: #c9d5ca; }
        .z-bar { position: absolute; top: 2px; height: 12px; border-radius: 999px; }
        .z-bar.pos { left: 50%; background: #1d7a52; }
        .z-bar.neg { right: 50%; background: #b83232; }
        .spark-card { margin-top: 14px; background: #f9fcf8; border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
        .spark-card h4 { margin: 0 0 10px; font-size: 15px; }
        .spark-chart { display: flex; align-items: flex-end; gap: 4px; height: 150px; }
        .spark-col { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 6px; }
        .spark-bars { width: 100%; height: 116px; display: flex; align-items: flex-end; justify-content: center; gap: 2px; }
        .spark-bar { width: 44%; min-height: 4px; border-radius: 6px 6px 0 0; }
        .spark-bar.open.up { background: #1d7a52; }
        .spark-bar.open.down { background: #b83232; }
        .spark-bar.open.flat { background: #b7791f; }
        .spark-bar.close.up { background: #0f4b80; }
        .spark-bar.close.down { background: #7e2940; }
        .spark-bar.close.flat { background: #8c6a1f; }
        .spark-date { font-size: 10px; color: var(--muted); transform: rotate(-35deg); white-space: nowrap; }
        .legend { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; color: var(--muted); font-size: 12px; }
        .legend span::before { content: " "; display: inline-block; width: 10px; height: 10px; border-radius: 999px; margin-right: 6px; vertical-align: middle; }
        .legend-open::before { background: #1d7a52; }
        .legend-close::before { background: #0f4b80; }
        .warn { color: var(--warn); }
        .bad { color: var(--bad); }
        @media (max-width: 900px) {
          .dual-grid { grid-template-columns: 1fr; }
          .driver-grid { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class=\"wrap\">
        <div class=\"hero\">
          <h1>수급 · 미수 증거금 통합 화면</h1>
          <p>기존 통합대시보드에서 외국인/기관/개인 수급과 익일 수익률 상관관계, 미수 증거금을 한 화면에서 확인합니다.</p>
          <div class=\"toolbar\">
            <a href=\"/investor-margin?mode=flow\" class=\"{% if mode == 'flow' %}active{% endif %}\">수급 분석</a>
            <a href=\"/investor-margin?mode=margin\" class=\"{% if mode == 'margin' %}active{% endif %}\">미수 증거금 계산</a>
            <a href=\"/dashboard?tab=investor-margin\" target=\"_self\">대시보드 탭으로 이동</a>
          </div>
        </div>

        <div class=\"panel\">
          <form method=\"GET\" action=\"/investor-margin\" class=\"{% if mode == 'flow' %}wide{% endif %}\">
            <input type=\"hidden\" name=\"mode\" value=\"flow\">
            <label>
              종목명/코드
              <input type=\"text\" name=\"stock_query\" placeholder=\"예: 삼성전자 또는 005930\" value=\"{{ stock_query }}\" required>
            </label>
            <button type=\"submit\">수급 상관분석 실행</button>
          </form>

          {% if flow_candidates %}
            <div class=\"meta\">동일 키워드 다수 매칭: 선택 후 다시 실행해 주세요.</div>
            <div class=\"chips\">
              {% for code, name in flow_candidates %}
                <a class=\"chip\" href=\"/investor-margin?mode=flow&stock_query={{ stock_query }}&stock_code={{ code }}\">{{ code }} {{ name }}</a>
              {% endfor %}
            </div>
          {% endif %}

          {% if flow_result %}
            <div class=\"section\">
              <h3>대상 종목: {{ flow_result.code }}{% if flow_result.name %} {{ flow_result.name }}{% endif %}</h3>
              <div class=\"chips\">
                <div class=\"chip\">표본일수: {{ flow_result.sample_count }}</div>
                <div class=\"chip\">통계 표본기간: {{ flow_result.sample_start_date }}~{{ flow_result.sample_end_date }}</div>
                <div class=\"chip\">최신 수급일: {{ flow_result.latest_date }}</div>
                <div class=\"chip\">익일 결과 확정 마지막 일자: {{ flow_result.confirmed_last_date }}</div>
                <div class=\"chip\">유사 수급 표본: {{ flow_result.similar_sample_count }}일</div>
                <div class=\"chip\">생성시각: {{ generated_at }}</div>
              </div>
              <div class=\"metric-grid\">
                <div class=\"metric-card\">
                  <div class=\"metric-title\">수급만 기준 판정</div>
                  <div class=\"metric-value tone-{{ flow_result.verdict_tone }}\">{{ flow_result.verdict }}</div>
                </div>
                <div class=\"metric-card\">
                  <div class=\"metric-title\">추정 시가</div>
                  <div class=\"metric-value\">{{ flow_result.predicted_open_price }}</div>
                  <div class=\"meta\">{{ flow_result.predicted_open_return }} / 상승확률 {{ flow_result.open_up_prob }}</div>
                </div>
                <div class=\"metric-card\">
                  <div class=\"metric-title\">추정 종가</div>
                  <div class=\"metric-value\">{{ flow_result.predicted_close_price }}</div>
                  <div class=\"meta\">{{ flow_result.predicted_close_return }} / 상승확률 {{ flow_result.close_up_prob }}</div>
                </div>
                <div class=\"metric-card\">
                  <div class=\"metric-title\">통계 적중률 / R²</div>
                  <div class=\"metric-value\">{{ flow_result.close_model_hit_rate }}</div>
                  <div class=\"meta\">종가모델 R² {{ flow_result.close_model_r2 }} / 시가모델 적중률 {{ flow_result.open_model_hit_rate }}</div>
                </div>
                <div class=\"metric-card\">
                  <div class=\"metric-title\">기준 대비 적중률 개선</div>
                  <div class=\"metric-value tone-{{ flow_result.close_hit_edge_tone }}\">{{ flow_result.close_hit_edge }}</div>
                  <div class=\"meta\">단순 기준 {{ flow_result.close_baseline_hit_rate }} / 시가 개선 {{ flow_result.open_hit_edge }}</div>
                </div>
                <div class=\"metric-card\">
                  <div class=\"metric-title\">평균 절대오차(MAE)</div>
                  <div class=\"metric-value\">{{ flow_result.close_model_mae }}</div>
                  <div class=\"meta\">시가 MAE {{ flow_result.open_model_mae }} / 수익률 %p 기준</div>
                </div>
                <div class=\"metric-card\">
                  <div class=\"metric-title\">방향 정밀도</div>
                  <div class=\"metric-value\">{{ flow_result.close_up_precision }}</div>
                  <div class=\"meta\">하락 예측 정밀도 {{ flow_result.close_down_precision }}</div>
                </div>
              </div>
              <div class=\"meta\">추정 시가/종가는 과거 일별 수급과 다음날 시가·종가 관계를 이용한 flow-only 추정치입니다. 실시간 뉴스나 장중 수급 변화는 반영하지 않습니다.</div>
              {% if flow_result.latest_pending %}
                <div class=\"meta\">최신 수급일 `{{ flow_result.latest_date }}`은 다음 거래일 시가/종가가 아직 없어 아래 확정 표본에서는 제외됩니다.</div>
              {% endif %}
            </div>
            {% if flow_result.latest_pending %}
            <div class=\"section\">
              <h3>최신 미확정 수급</h3>
              <table>
                <thead>
                  <tr><th>일자</th><th>외국인</th><th>기관</th><th>개인</th><th>종가</th><th>상태</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{{ flow_result.latest_pending.Date }}</td>
                    <td>{{ flow_result.latest_pending.Foreign_Net }}</td>
                    <td>{{ flow_result.latest_pending.Inst_Net }}</td>
                    <td>{{ flow_result.latest_pending.Retail_Net }}</td>
                    <td>{{ flow_result.latest_pending.Close }}</td>
                    <td>익일 데이터 대기</td>
                  </tr>
                </tbody>
              </table>
            </div>
            {% endif %}
            <div class=\"section\">
              <div class=\"dual-grid\">
                <div class=\"chart-card\">
                  <h4>수급 vs 다음날 시가 상관도</h4>
                  {% for row in flow_result.corr_open_rows %}
                    <div class=\"corr-row\">
                      <div class=\"corr-name\">{{ row.label }}</div>
                      <div class=\"corr-track\">
                        <div class=\"corr-bar {{ row.side }}\" style=\"width: {{ '%.1f'|format(row.width_pct) }}%;\"></div>
                      </div>
                      <div class=\"corr-name tone-{{ row.tone }}\">{{ row.display }}</div>
                    </div>
                  {% endfor %}
                </div>
                <div class=\"chart-card\">
                  <h4>수급 vs 다음날 종가 상관도</h4>
                  {% for row in flow_result.corr_close_rows %}
                    <div class=\"corr-row\">
                      <div class=\"corr-name\">{{ row.label }}</div>
                      <div class=\"corr-track\">
                        <div class=\"corr-bar {{ row.side }}\" style=\"width: {{ '%.1f'|format(row.width_pct) }}%;\"></div>
                      </div>
                      <div class=\"corr-name tone-{{ row.tone }}\">{{ row.display }}</div>
                    </div>
                  {% endfor %}
                </div>
              </div>
            </div>
            <div class=\"section\">
              <h3>오늘 수급 위치</h3>
              <div class=\"driver-grid\">
                {% for row in flow_result.driver_rows %}
                  <div class=\"driver-card\">
                    <div class=\"driver-head\">
                      <div class=\"driver-name\">{{ row.label }}</div>
                      <div class=\"tone-{{ row.tone }}\">종가 기여 {{ row.close_contribution }}</div>
                    </div>
                    <div class=\"driver-raw\">순매수 {{ row.raw }} / z-score {{ row.zscore }}</div>
                    <div class=\"z-track\">
                      <div class=\"z-bar {{ row.side }}\" style=\"width: {{ '%.1f'|format(row.width_pct) }}%;\"></div>
                    </div>
                  </div>
                {% endfor %}
              </div>
            </div>
            <div class=\"section\">
              <div class=\"spark-card\">
                <h4>최근 20개 표본의 익일 시가/종가 수익률 그래프</h4>
                <div class=\"spark-chart\">
                  {% for row in flow_result.recent_return_bars %}
                    <div class=\"spark-col\">
                      <div class=\"spark-bars\">
                        <div class=\"spark-bar open {{ row.open_tone }}\" style=\"height: {{ row.open_height }}px;\" title=\"시가 {{ row.open_display }}\"></div>
                        <div class=\"spark-bar close {{ row.close_tone }}\" style=\"height: {{ row.close_height }}px;\" title=\"종가 {{ row.close_display }}\"></div>
                      </div>
                      <div class=\"spark-date\">{{ row.date[5:] }}</div>
                    </div>
                  {% endfor %}
                </div>
                <div class=\"legend\">
                  <span class=\"legend-open\">익일 시가 수익률</span>
                  <span class=\"legend-close\">익일 종가 수익률</span>
                </div>
              </div>
            </div>
            <div class=\"section\">
              <h3>유사 수급 표본</h3>
              <table>
                <thead>
                  <tr><th>일자</th><th>거리</th><th>익일 시가 수익률</th><th>익일 종가 수익률</th></tr>
                </thead>
                <tbody>
                  {% for row in flow_result.similar_rows %}
                    <tr>
                      <td>{{ row.Date }}</td>
                      <td>{{ row.Distance }}</td>
                      <td>{{ row.NextOpen_ReturnPct }}</td>
                      <td>{{ row.NextClose_ReturnPct }}</td>
                    </tr>
                  {% else %}
                    <tr><td colspan=\"4\" class=\"meta\">유사 수급 표본이 없습니다.</td></tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
            <div class=\"section\">
              <h3>최근 익일 결과 확정 표본 (최근 20일)</h3>
              <table>
                <thead>
                  <tr><th>일자</th><th>외국인</th><th>기관</th><th>개인</th><th>종가</th><th>익일시가</th><th>익일시가수익률</th><th>익일종가</th><th>익일종가수익률</th></tr>
                </thead>
                <tbody>
                  {% for row in flow_result.sample_rows %}
                    <tr>
                      <td>{{ row.Date }}</td>
                      <td>{{ row.Foreign_Net }}</td>
                      <td>{{ row.Inst_Net }}</td>
                      <td>{{ row.Retail_Net }}</td>
                      <td>{{ row.Close }}</td>
                      <td>{{ row.Next_Open }}</td>
                      <td>{{ row.NextOpen_ReturnPct }}</td>
                      <td>{{ row.Next_Close }}</td>
                      <td>{{ row.NextClose_ReturnPct }}</td>
                    </tr>
                  {% else %}
                    <tr><td colspan=\"9\" class=\"meta\">표시할 데이터가 없습니다.</td></tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          {% elif flow_error %}
            <div class=\"section bad\">{{ flow_error }}</div>
          {% endif %}
        </div>

        <div class=\"panel\">
          <form method=\"GET\" action=\"/investor-margin\">
            <input type=\"hidden\" name=\"mode\" value=\"margin\">
            <label>
              종목명/코드
              <input type=\"text\" name=\"stock_query\" placeholder=\"예: 삼성전자 또는 005930\" value=\"{{ stock_query }}\" required>
            </label>
            <label>
              수량
              <input type=\"number\" name=\"quantity\" min=\"1\" step=\"1\" value=\"{{ quantity }}\">
            </label>
            <button type=\"submit\">미수 증거금 계산</button>
          </form>

          {% if margin_candidates %}
            <div class=\"meta\">동일 키워드 다수 매칭: 선택 후 다시 실행해 주세요.</div>
            <div class=\"chips\">
              {% for code, name in margin_candidates %}
                <a class=\"chip\" href=\"/investor-margin?mode=margin&stock_query={{ stock_query }}&stock_code={{ code }}&quantity={{ quantity }}\">{{ code }} {{ name }}</a>
              {% endfor %}
            </div>
          {% endif %}

          {% if margin_error %}
            <div class=\"section bad\">{{ margin_error }}</div>
          {% elif margin_result %}
            <div class=\"section\">
              <h3>미수 증거금 산출</h3>
              <div class=\"meta\">{{ margin_result.code }}{% if margin_result.name %} {{ margin_result.name }}{% endif %}</div>
              <table>
                <tbody>
                  <tr><th>현재가</th><td>{{ margin_result.current_price }}</td></tr>
                  <tr><th>현재가 출처</th><td>{{ margin_result.price_source }}</td></tr>
                  <tr><th>입력 수량</th><td>{{ quantity }}주</td></tr>
                  <tr><th>종목 증거금율</th><td>{{ margin_result.stock_margin_rate }}%</td></tr>
                  <tr><th>적용 증거금율</th><td>{{ margin_result.applied_margin_rate }}%</td></tr>
                  <tr><th>필요 증거금</th><td><strong>{{ margin_result.required_margin }}</strong></td></tr>
                  <tr><th>해당 증거금율 주문가능수량</th><td>{{ margin_result.orderable_qty }}</td></tr>
                  <tr><th>해당 증거금율 주문가능금액</th><td>{{ margin_result.orderable_amount }}</td></tr>
                </tbody>
              </table>
              <div class=\"meta\">계산 기준은 `kt00011`의 `aplc_rt`입니다. `stk_profa_rt`는 종목 기본 증거금율이고, 실제 계산에는 계좌 적용값이 우선합니다.</div>
            </div>
          {% endif %}
        </div>

        <div class=\"meta\">생성 시각: {{ generated_at }}</div>
      </div>
    </body>
    </html>
    """

    return render_template_string(
        template,
        mode=mode,
        stock_query=stock_query,
        stock_code=stock_code,
        quantity=quantity,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        flow_result=flow_result,
        margin_result=margin_result,
        flow_candidates=flow_result["candidates"] if flow_result and flow_result.get("candidates") else None,
        margin_candidates=margin_result["candidates"] if margin_result and margin_result.get("candidates") else None,
        flow_error=flow_result.get("error") if flow_result else None,
        margin_error=margin_result.get("error") if margin_result else None,
    )


def _build_flow_result(token: str, stock_query: str, stock_code: str) -> dict[str, Any]:
    code, name_guess, candidates = _resolve_stock_code(stock_query, token, stock_code)
    if code is None:
        if candidates:
            return {"code": "", "candidates": candidates, "error": "종목명 검색 결과가 다수입니다. 후보를 선택하세요."}
        return {"code": "", "error": "종목을 찾지 못했습니다."}

    investor_df, price_df = _load_investor_and_prices(token, code)
    if investor_df.empty:
        return {"code": code, "name": name_guess, "error": "수급 데이터(ka10059)가 비어 있습니다."}
    if price_df.empty:
        return {"code": code, "name": name_guess, "error": "일봉 가격 데이터(ka10081)가 비어 있습니다."}

    analysis = prepare_flow_analysis(investor_df, price_df)
    if not analysis:
        return {"code": code, "name": name_guess, "error": "겹치는 날짜 기준 계산 데이터가 부족합니다."}

    rows = analysis["recent"].tail(20).copy()
    if rows.empty:
        return {"code": code, "name": name_guess, "error": "표시 가능한 표본이 없습니다."}

    rows = rows.reset_index(drop=True)
    rows["Close"] = rows["Close"].map(_format_number)
    rows["Next_Open"] = rows["Next_Open"].map(_format_number)
    rows["Next_Close"] = rows["Next_Close"].map(_format_number)
    rows["Foreign_Net"] = rows["Foreign_Net"].map(_format_number)
    rows["Inst_Net"] = rows["Inst_Net"].map(_format_number)
    rows["Retail_Net"] = rows["Retail_Net"].map(_format_number)
    rows["NextOpen_ReturnPct"] = rows["NextOpen_ReturnPct"].map(_format_pct)
    rows["NextClose_ReturnPct"] = rows["NextClose_ReturnPct"].map(_format_pct)

    similar_rows = []
    for row in analysis["similar_rows"][:8]:
        similar_rows.append(
            {
                "Date": row["Date"],
                "Distance": f"{float(row['Distance']):.2f}",
                "NextOpen_ReturnPct": _format_pct(row["NextOpen_ReturnPct"]),
                "NextClose_ReturnPct": _format_pct(row["NextClose_ReturnPct"]),
            }
        )

    return {
        "code": code,
        "name": name_guess,
        "sample_count": int(analysis["sample_count"]),
        "sample_start_date": analysis["sample_start_date"],
        "sample_end_date": analysis["sample_end_date"],
        "latest_date": analysis["latest_date"],
        "confirmed_last_date": analysis["confirmed_last_date"],
        "latest_pending": {
            "Date": analysis["latest_pending"]["Date"],
            "Close": _format_number(analysis["latest_pending"]["Close"]),
            "Foreign_Net": _format_number(analysis["latest_pending"]["Foreign_Net"]),
            "Inst_Net": _format_number(analysis["latest_pending"]["Inst_Net"]),
            "Retail_Net": _format_number(analysis["latest_pending"]["Retail_Net"]),
        } if analysis.get("latest_pending") else None,
        "sample_rows": rows.to_dict(orient="records"),
        "verdict": analysis["prediction"]["verdict"],
        "verdict_tone": analysis["prediction"]["tone"],
        "predicted_open_price": f"{int(round(analysis['prediction']['open_price'])):,}원",
        "predicted_close_price": f"{int(round(analysis['prediction']['close_price'])):,}원",
        "predicted_open_return": _format_pct(analysis["prediction"]["open_return_pct"]),
        "predicted_close_return": _format_pct(analysis["prediction"]["close_return_pct"]),
        "open_up_prob": _format_ratio(analysis["prediction"]["open_up_prob"]),
        "close_up_prob": _format_ratio(analysis["prediction"]["close_up_prob"]),
        "open_model_hit_rate": _format_ratio(analysis["models"]["open"]["hit_rate"]),
        "close_model_hit_rate": _format_ratio(analysis["models"]["close"]["hit_rate"]),
        "open_baseline_hit_rate": _format_ratio(analysis["models"]["open"]["baseline_hit_rate"]),
        "close_baseline_hit_rate": _format_ratio(analysis["models"]["close"]["baseline_hit_rate"]),
        "open_hit_edge": _format_pct(analysis["models"]["open"]["hit_edge"] * 100.0),
        "close_hit_edge": _format_pct(analysis["models"]["close"]["hit_edge"] * 100.0),
        "close_hit_edge_tone": _tone_from_value(float(analysis["models"]["close"]["hit_edge"]), 0.0, 0.0),
        "open_model_mae": _format_pct(analysis["models"]["open"]["mae"]),
        "close_model_mae": _format_pct(analysis["models"]["close"]["mae"]),
        "open_up_precision": _format_ratio(analysis["models"]["open"]["up_precision"]),
        "open_down_precision": _format_ratio(analysis["models"]["open"]["down_precision"]),
        "close_up_precision": _format_ratio(analysis["models"]["close"]["up_precision"]),
        "close_down_precision": _format_ratio(analysis["models"]["close"]["down_precision"]),
        "open_model_r2": f"{float(analysis['models']['open']['r2']):.2f}",
        "close_model_r2": f"{float(analysis['models']['close']['r2']):.2f}",
        "corr_open_rows": _build_corr_rows(analysis["correlation"]["open"]),
        "corr_close_rows": _build_corr_rows(analysis["correlation"]["close"]),
        "driver_rows": _build_driver_rows(analysis["driver_rows"]),
        "recent_return_bars": _build_recent_return_bars(analysis["recent"]),
        "similar_sample_count": int(analysis["analog"]["sample_count"]),
        "similar_rows": similar_rows,
    }


def _build_margin_result(token: str, stock_query: str, stock_code: str, quantity: int) -> dict[str, Any]:
    code, name_guess, candidates = _resolve_stock_code(stock_query, token, stock_code)
    if code is None:
        if candidates:
            return {"code": "", "candidates": candidates, "error": "종목명 검색 결과가 다수입니다. 후보를 선택하세요."}
        return {"code": "", "error": "종목을 찾지 못했습니다."}

    current_price, price_source = _current_price_from_kiwoom(token, code)
    if current_price <= 0:
        return {"code": code, "name": name_guess, "error": "현재가를 조회하지 못했습니다."}

    margin_info = _load_margin_requirement_info(token, code, current_price)
    if margin_info.get("error"):
        return {
            "code": code,
            "name": name_guess,
            "current_price": f"{current_price:,}원",
            "price_source": price_source or "-",
            "error": str(margin_info.get("error")),
        }
    applied_margin_rate = int(margin_info.get("applied_margin_rate") or 0)
    stock_margin_rate = int(margin_info.get("stock_margin_rate") or 0)
    if applied_margin_rate <= 0:
        return {
            "code": code,
            "name": name_guess,
            "current_price": f"{current_price:,}원",
            "price_source": price_source or "-",
            "error": "kt00011에서 적용 증거금율을 조회하지 못했습니다.",
        }

    required_margin = int(current_price * quantity * applied_margin_rate / 100.0)
    orderable_tier = ((margin_info.get("tiers") or {}).get(applied_margin_rate) or {})
    return {
        "code": code,
        "name": name_guess,
        "current_price": f"{current_price:,}원",
        "price_source": price_source or "-",
        "stock_margin_rate": stock_margin_rate,
        "applied_margin_rate": applied_margin_rate,
        "required_margin": f"{required_margin:,}원",
        "orderable_qty": f"{int(orderable_tier.get('orderable_qty', 0)):,}주",
        "orderable_amount": f"{int(orderable_tier.get('orderable_amount', 0)):,}원",
        "credit_balance_rate": _load_credit_balance_rate(token, code),
    }
