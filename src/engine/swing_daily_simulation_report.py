"""Daily swing recommendation simulation report.

The report is advisory only. It simulates the official swing recommendation CSV
with the same next-session open entry and path-based TP/SL convention used by
the v2 backtest, while keeping fallback diagnostics out of the simulated book.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine, text

from src.engine import kiwoom_orders
from src.model.common_v2 import RECO_PATH
from src.utils.constants import DATA_DIR, POSTGRES_URL, TRADING_RULES


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_daily_simulation"
LIVE_SELECTION_MODES = {"SELECTED", "META_V2", "META_FALLBACK", "EOD_TOP5", ""}
DIAGNOSTIC_SELECTION_MODES = {"EMPTY", "FALLBACK_DIAGNOSTIC", "DIAGNOSTIC_ONLY"}


def _date_text(value: str | date | datetime | pd.Timestamp | None) -> str:
    if value is None:
        return str(pd.Timestamp.now(tz="Asia/Seoul").date())
    return str(pd.to_datetime(value).date())


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(value)
    except Exception:
        return default


def load_recommendations(path: str | Path = RECO_PATH, target_date: str | None = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    if df.empty:
        return df
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        if target_date:
            df = df[df["date"] == pd.to_datetime(target_date).normalize()].copy()
    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(6)
    return df.reset_index(drop=True)


def filter_live_recommendations(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if df.empty:
        return df.copy(), {"input_rows": 0, "live_rows": 0, "diagnostic_rows": 0, "selection_modes": {}}

    out = df.copy()
    if "selection_mode" not in out.columns:
        out["selection_mode"] = ""
    modes = out["selection_mode"].fillna("").astype(str).str.upper()
    live_mask = ~modes.isin(DIAGNOSTIC_SELECTION_MODES)
    live = out[live_mask].copy()
    return live.reset_index(drop=True), {
        "input_rows": int(len(out)),
        "live_rows": int(len(live)),
        "diagnostic_rows": int((~live_mask).sum()),
        "selection_modes": modes.replace("", "LEGACY_UNTAGGED").value_counts().to_dict(),
    }


def fetch_quote_rows(codes: Iterable[str], start_date: str, db_url: str = POSTGRES_URL) -> pd.DataFrame:
    codes = sorted({str(code).zfill(6) for code in codes if str(code).strip()})
    if not codes:
        return pd.DataFrame()
    engine = create_engine(db_url)
    query = text(
        """
        SELECT quote_date, stock_code, stock_name, open_price, high_price, low_price, close_price
        FROM daily_stock_quotes
        WHERE stock_code = ANY(:codes)
          AND quote_date > :start_date
        ORDER BY stock_code ASC, quote_date ASC
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"codes": codes, "start_date": start_date})
    if df.empty:
        return df
    df["quote_date"] = pd.to_datetime(df["quote_date"], errors="coerce").dt.normalize()
    df["stock_code"] = df["stock_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(6)
    return df


def _normalize_strategy(row: pd.Series | dict) -> str:
    raw = str((row.get("strategy") if hasattr(row, "get") else "") or "").upper().strip()
    if raw in {"KOSDAQ_ML", "KOSPI_ML"}:
        return raw
    return "KOSPI_ML"


def _runtime_swing_thresholds(strategy: str, bull_regime: int) -> dict:
    if strategy == "KOSDAQ_ML":
        return {
            "max_gap_pct": float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSDAQ", 3.0) or 3.0),
            "ratio_min": float(getattr(TRADING_RULES, "INVEST_RATIO_KOSDAQ_MIN", 0.05) or 0.05),
            "ratio_max": float(getattr(TRADING_RULES, "INVEST_RATIO_KOSDAQ_MAX", 0.15) or 0.15),
            "buy_score_threshold": int(getattr(TRADING_RULES, "BUY_SCORE_KOSDAQ_THRESHOLD", 80) or 80),
            "target_pct": float(getattr(TRADING_RULES, "KOSDAQ_TARGET", 4.0) or 4.0),
            "max_hold_days": int(getattr(TRADING_RULES, "KOSDAQ_HOLDING_DAYS", 3) or 3),
        }
    return {
        "max_gap_pct": float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSPI", 3.5) or 3.5),
        "ratio_min": float(getattr(TRADING_RULES, "INVEST_RATIO_KOSPI_MIN", 0.10) or 0.10),
        "ratio_max": float(getattr(TRADING_RULES, "INVEST_RATIO_KOSPI_MAX", 0.40) or 0.40),
        "buy_score_threshold": int(getattr(TRADING_RULES, "BUY_SCORE_THRESHOLD", 75) or 75),
        "target_pct": float(getattr(TRADING_RULES, "RALLY_TARGET_PCT", 5.0) or 5.0),
        "max_hold_days": int(getattr(TRADING_RULES, "HOLDING_DAYS", 4) or 4),
    }


def _runtime_score_proxy(row: pd.Series | dict) -> float:
    """Daily-data proxy for radar.analyze_signal_integrated score.

    Live runtime uses tick/orderbook/radar metrics that are not fully replayable
    from daily quotes. This proxy preserves the same threshold surface and keeps
    its provenance explicit in the report.
    """
    hybrid_mean = _safe_float(row.get("hybrid_mean"), 0.0)
    floor_used = _safe_float(row.get("floor_used"), 0.35)
    score_rank = max(_safe_int(row.get("score_rank"), 99), 1)
    rank_bonus = max(0.0, 18.0 - min(score_rank, 18)) * 0.6
    floor_edge = max(0.0, hybrid_mean - max(floor_used, 0.0)) * 120.0
    return max(0.0, min(100.0, 72.0 + floor_edge + rank_bonus))


def _runtime_entry_dry_run(row: pd.Series, entry_quote: pd.Series, *, simulation_cash_krw: int) -> dict:
    strategy = _normalize_strategy(row)
    bull_regime = _safe_int(row.get("bull_regime"), 0)
    thresholds = _runtime_swing_thresholds(strategy, bull_regime)
    curr_price = _safe_float(entry_quote.get("open_price"), 0.0)
    signal_close = _safe_float(row.get("close"), 0.0)
    fluctuation = ((curr_price / signal_close) - 1.0) * 100.0 if curr_price > 0 and signal_close > 0 else 0.0
    runtime_score = _runtime_score_proxy(row)
    buy_threshold = float(thresholds["buy_score_threshold"])

    result = {
        "strategy": strategy,
        "entry_guard": "PENDING",
        "entry_guard_reason": "",
        "entry_runtime_score_proxy": runtime_score,
        "entry_runtime_score_source": "daily_proxy_from_hybrid_mean_score_rank",
        "buy_score_threshold": buy_threshold,
        "gap_pct": fluctuation,
        "max_gap_pct": thresholds["max_gap_pct"],
        "gatekeeper_mode": "dry_run_assumed_pass",
        "market_regime_mode": "dry_run_from_bull_regime",
        "actual_order_submitted": False,
        "order_type_code": "6",
        "order_type_desc": "최유리지정가",
        "request_price": 0,
        "assumed_fill_price": curr_price,
        "target_pct": thresholds["target_pct"],
        "max_hold_days": thresholds["max_hold_days"],
    }
    if curr_price <= 0:
        return {**result, "entry_guard": "BLOCKED_BAD_ENTRY_PRICE", "entry_guard_reason": "open_price<=0"}
    if fluctuation >= thresholds["max_gap_pct"]:
        return {**result, "entry_guard": "BLOCKED_SWING_GAP", "entry_guard_reason": "gap>=runtime_threshold"}
    if runtime_score < buy_threshold:
        return {**result, "entry_guard": "BLOCKED_RUNTIME_SCORE", "entry_guard_reason": "score_proxy<buy_threshold"}
    if bull_regime <= 0:
        return {**result, "entry_guard": "BLOCKED_MARKET_REGIME", "entry_guard_reason": "bull_regime=0"}

    score_weight = max(0.0, min(1.0, (runtime_score - buy_threshold) / max(1.0, 100.0 - buy_threshold)))
    ratio = thresholds["ratio_min"] + score_weight * (thresholds["ratio_max"] - thresholds["ratio_min"])
    target_budget, safe_budget, qty, safety_ratio = kiwoom_orders.describe_buy_capacity(
        curr_price,
        simulation_cash_krw,
        ratio,
        max_budget=0,
    )
    result.update(
        {
            "entry_guard": "PASS_DRY_RUN",
            "entry_guard_reason": "gap/runtime_score/market_regime pass; gatekeeper assumed pass without AI transport",
            "ratio": ratio,
            "simulation_cash_krw": int(simulation_cash_krw),
            "target_budget": target_budget,
            "safe_budget": safe_budget,
            "safety_ratio": safety_ratio,
            "buy_qty": qty,
        }
    )
    if qty <= 0:
        result.update({"entry_guard": "BLOCKED_ZERO_QTY", "entry_guard_reason": "describe_buy_capacity returned 0"})
    return result


def _resolve_runtime_exit(day: pd.Series, *, entry_price: float, peak_price: float, hold_day: int, max_hold_days: int, strategy: str, bull_regime: int):
    open_p = _safe_float(day.get("open_price"), 0.0)
    high_p = _safe_float(day.get("high_price"), 0.0)
    low_p = _safe_float(day.get("low_price"), 0.0)
    close_p = _safe_float(day.get("close_price"), 0.0)
    thresholds = _runtime_swing_thresholds(strategy, bull_regime)
    stop_loss_pct = (
        float(getattr(TRADING_RULES, "STOP_LOSS_BULL", -3.0) or -3.0)
        if bull_regime == 1
        else float(getattr(TRADING_RULES, "STOP_LOSS_BEAR", -3.0) or -3.0)
    )
    stop_price = entry_price * (1.0 + stop_loss_pct / 100.0)
    target_price = entry_price * (1.0 + float(thresholds["target_pct"]) / 100.0)
    trailing_start = float(getattr(TRADING_RULES, "TRAILING_START_PCT", 2.5) or 2.5)
    trailing_drawdown = float(getattr(TRADING_RULES, "TRAILING_DRAWDOWN_PCT", 0.5) or 0.5)
    updated_peak = max(peak_price, high_p, open_p, close_p)
    trailing_armed = ((updated_peak / entry_price) - 1.0) * 100.0 >= trailing_start
    trailing_stop = updated_peak * (1.0 - trailing_drawdown / 100.0)

    if open_p <= stop_price:
        return open_p, "PRESET_HARD_STOP_GAP", updated_peak
    if open_p >= target_price:
        return open_p, "PRESET_TARGET_GAP", updated_peak
    if low_p <= stop_price:
        return stop_price, "PRESET_HARD_STOP", updated_peak
    if high_p >= target_price:
        return target_price, "PRESET_TARGET", updated_peak
    if trailing_armed and low_p <= trailing_stop:
        return trailing_stop, "TRAILING_STOP", updated_peak
    if hold_day >= max_hold_days:
        return close_p, "TIME_STOP", updated_peak
    return None, "", updated_peak


def simulate_swing_recommendations(
    recommendations: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    target_date: str | None = None,
    simulation_cash_krw: int = 10_000_000,
    roundtrip_fee_rate: float = 0.0023,
) -> list[dict]:
    if recommendations.empty:
        return []
    quote_df = quotes.copy()
    if not quote_df.empty:
        quote_df["quote_date"] = pd.to_datetime(quote_df["quote_date"], errors="coerce").dt.normalize()
    rows = []
    as_of = pd.to_datetime(target_date).normalize() if target_date else None

    for _, row in recommendations.iterrows():
        signal_date = pd.to_datetime(row.get("date"), errors="coerce").normalize()
        code = str(row.get("code") or row.get("stock_code") or "").zfill(6)
        if quote_df.empty or "stock_code" not in quote_df.columns or "quote_date" not in quote_df.columns:
            future = pd.DataFrame()
        else:
            future = quote_df[quote_df["stock_code"] == code].copy()
        if pd.notna(signal_date) and not future.empty:
            future = future[future["quote_date"] > signal_date]
        if not future.empty:
            future = future.sort_values("quote_date").head(6)

        base = {
            "signal_date": _date_text(signal_date) if pd.notna(signal_date) else "",
            "code": code,
            "name": str(row.get("name") or row.get("stock_name") or ""),
            "selection_mode": str(row.get("selection_mode") or "LEGACY_UNTAGGED"),
            "score_rank": _safe_int(row.get("score_rank"), 0),
            "hybrid_mean": _safe_float(row.get("hybrid_mean"), 0.0),
            "meta_score": _safe_float(row.get("meta_score", row.get("score")), 0.0),
            "floor_used": _safe_float(row.get("floor_used"), 0.0),
            "bull_regime": _safe_int(row.get("bull_regime"), 0),
        }

        if future.empty:
            rows.append({
                **base,
                "status": "PENDING_ENTRY",
                "entry_guard": "WAITING_FOR_NEXT_SESSION_QUOTE",
                "entry_guard_reason": "no quote after signal_date yet",
                "actual_order_submitted": False,
                "exit_reason": "",
                "net_ret": None,
            })
            continue

        entry = future.iloc[0]
        entry_date = entry["quote_date"]
        entry_decision = _runtime_entry_dry_run(row, entry, simulation_cash_krw=simulation_cash_krw)
        buy_price = _safe_float(entry_decision.get("assumed_fill_price"), 0.0)
        if buy_price <= 0:
            rows.append({
                **base,
                **entry_decision,
                "status": entry_decision.get("entry_guard", "SKIPPED_BAD_ENTRY_PRICE"),
                "entry_date": _date_text(entry_date),
                "net_ret": None,
            })
            continue
        if as_of is not None and entry_date > as_of:
            rows.append({
                **base,
                **entry_decision,
                "status": "PLANNED_ENTRY",
                "entry_date": _date_text(entry_date),
                "buy_price": buy_price,
                "exit_reason": "",
                "net_ret": None,
            })
            continue
        if entry_decision.get("entry_guard") != "PASS_DRY_RUN":
            rows.append({
                **base,
                **entry_decision,
                "status": entry_decision.get("entry_guard", "BLOCKED_ENTRY"),
                "entry_date": _date_text(entry_date),
                "buy_price": buy_price,
                "exit_reason": "",
                "net_ret": None,
            })
            continue

        exit_price = None
        exit_reason = ""
        hold_days = 0
        peak_price = buy_price
        max_hold_days = int(entry_decision.get("max_hold_days") or 4)

        for idx, day in future.iterrows():
            hold_days += 1
            if as_of is not None and day["quote_date"] > as_of:
                break
            exit_price, exit_reason, peak_price = _resolve_runtime_exit(
                day,
                entry_price=buy_price,
                peak_price=peak_price,
                hold_day=hold_days,
                max_hold_days=max_hold_days,
                strategy=str(entry_decision.get("strategy") or "KOSPI_ML"),
                bull_regime=base["bull_regime"],
            )
            if exit_price is not None:
                exit_date = day["quote_date"]
                break
        else:
            exit_date = None

        if exit_price is None:
            latest = future[future["quote_date"] <= as_of].tail(1) if as_of is not None else future.tail(1)
            mark_price = _safe_float(latest.iloc[0].get("close_price"), buy_price) if not latest.empty else buy_price
            rows.append({
                **base,
                **entry_decision,
                "status": "OPEN_SIM",
                "entry_date": _date_text(entry_date),
                "buy_price": buy_price,
                "mark_price": mark_price,
                "unrealized_ret": (mark_price / buy_price) - 1.0,
                "hold_days": hold_days,
                "exit_reason": "",
                "net_ret": None,
            })
            continue

        gross_ret = (exit_price / buy_price) - 1.0
        rows.append({
            **base,
            **entry_decision,
            "status": "CLOSED_SIM",
            "entry_date": _date_text(entry_date),
            "exit_date": _date_text(exit_date),
            "hold_days": hold_days,
            "buy_price": buy_price,
            "exit_price": exit_price,
            "gross_ret": gross_ret,
            "net_ret": gross_ret - roundtrip_fee_rate,
            "exit_reason": exit_reason,
        })

    return rows


def summarize_simulation(sim_rows: list[dict]) -> dict:
    if not sim_rows:
        return {
            "simulated_count": 0,
            "closed_count": 0,
            "planned_or_open_count": 0,
            "win_rate": 0.0,
            "avg_net_ret": 0.0,
            "median_net_ret": 0.0,
            "sum_net_ret": 0.0,
            "status_counts": {},
            "exit_reason_counts": {},
        }
    df = pd.DataFrame(sim_rows)
    closed = df[df["status"] == "CLOSED_SIM"].copy()
    net = pd.to_numeric(closed.get("net_ret", pd.Series(dtype=float)), errors="coerce").dropna()
    return {
        "simulated_count": int(len(df)),
        "closed_count": int(len(closed)),
        "planned_or_open_count": int((df["status"] != "CLOSED_SIM").sum()),
        "win_rate": float((net > 0).mean()) if len(net) else 0.0,
        "avg_net_ret": float(net.mean()) if len(net) else 0.0,
        "median_net_ret": float(net.median()) if len(net) else 0.0,
        "sum_net_ret": float(net.sum()) if len(net) else 0.0,
        "status_counts": dict(Counter(df["status"].fillna("UNKNOWN"))),
        "exit_reason_counts": dict(Counter(closed.get("exit_reason", pd.Series(dtype=str)).fillna("UNKNOWN"))),
    }


def summarize_backtest(path: str | Path | None = None) -> dict:
    p = Path(path or Path(DATA_DIR) / "backtest_trades_v2.csv")
    if not p.exists():
        return {"available": False, "path": str(p)}
    df = pd.read_csv(p)
    if df.empty or "net_ret" not in df.columns:
        return {"available": False, "path": str(p), "rows": int(len(df))}
    net = pd.to_numeric(df["net_ret"], errors="coerce").dropna()
    out = {
        "available": True,
        "path": str(p),
        "rows": int(len(df)),
        "win_rate": float((net > 0).mean()) if len(net) else 0.0,
        "avg_net_ret": float(net.mean()) if len(net) else 0.0,
        "median_net_ret": float(net.median()) if len(net) else 0.0,
        "sum_net_ret": float(net.sum()) if len(net) else 0.0,
    }
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce")
        out["date_min"] = _date_text(dates.min()) if dates.notna().any() else ""
        out["date_max"] = _date_text(dates.max()) if dates.notna().any() else ""
    return out


def build_swing_daily_simulation_report(
    target_date: str | date | datetime | None = None,
    *,
    recommendation_path: str | Path = RECO_PATH,
    recommendation_rows: pd.DataFrame | None = None,
    quote_rows: pd.DataFrame | None = None,
    db_url: str = POSTGRES_URL,
    backtest_path: str | Path | None = None,
    simulation_cash_krw: int = 10_000_000,
) -> dict:
    date_key = _date_text(target_date)
    rec_df = recommendation_rows if recommendation_rows is not None else load_recommendations(recommendation_path, date_key)
    live_rec_df, rec_summary = filter_live_recommendations(rec_df)

    if quote_rows is None and not live_rec_df.empty:
        min_signal_date = _date_text(live_rec_df["date"].min())
        quote_rows = fetch_quote_rows(live_rec_df["code"], min_signal_date, db_url=db_url)
    elif quote_rows is None:
        quote_rows = pd.DataFrame()

    sim_rows = simulate_swing_recommendations(
        live_rec_df,
        quote_rows,
        target_date=date_key,
        simulation_cash_krw=simulation_cash_krw,
    )
    return {
        "schema_version": 1,
        "report_type": "swing_daily_simulation",
        "target_date": date_key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_change": False,
        "recommendation_path": str(recommendation_path),
        "recommendation_summary": rec_summary,
        "simulation_params": {
            "mode": "runtime_order_dry_run_daily_proxy",
            "entry": "runtime guard dry-run, no broker order submit",
            "entry_order_type_code": "6",
            "entry_order_type_desc": "최유리지정가",
            "assumed_fill": "daily open after runtime guard pass",
            "simulation_cash_krw": int(simulation_cash_krw),
            "max_gap_pct_kospi": float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSPI", 3.5) or 3.5),
            "max_gap_pct_kosdaq": float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSDAQ", 3.0) or 3.0),
            "stop_loss_bull": float(getattr(TRADING_RULES, "STOP_LOSS_BULL", -3.0) or -3.0),
            "stop_loss_bear": float(getattr(TRADING_RULES, "STOP_LOSS_BEAR", -3.0) or -3.0),
            "trailing_start_pct": float(getattr(TRADING_RULES, "TRAILING_START_PCT", 2.5) or 2.5),
            "trailing_drawdown_pct": float(getattr(TRADING_RULES, "TRAILING_DRAWDOWN_PCT", 0.5) or 0.5),
            "roundtrip_fee_rate": 0.0023,
            "parity_notes": [
                "Uses runtime constants and quantity calculation.",
                "Does not submit broker orders.",
                "Gatekeeper AI/tick/orderbook inputs are not replayable from daily quotes; report marks gatekeeper_mode=dry_run_assumed_pass.",
            ],
        },
        "simulation_summary": summarize_simulation(sim_rows),
        "model_backtest_summary": summarize_backtest(backtest_path),
        "simulated_trades": sim_rows,
    }


def render_markdown(report: dict) -> str:
    sim = report["simulation_summary"]
    rec = report["recommendation_summary"]
    backtest = report["model_backtest_summary"]
    lines = [
        f"# Swing Daily Simulation - {report['target_date']}",
        "",
        f"- runtime_change: `{report['runtime_change']}`",
        f"- recommendation_rows: `{rec.get('input_rows')}` / live `{rec.get('live_rows')}` / diagnostic `{rec.get('diagnostic_rows')}`",
        f"- simulated_count: `{sim.get('simulated_count')}`",
        f"- closed_count: `{sim.get('closed_count')}`",
        f"- planned_or_open_count: `{sim.get('planned_or_open_count')}`",
        f"- closed win_rate: `{sim.get('win_rate', 0.0):.2%}`",
        f"- closed avg_net_ret: `{sim.get('avg_net_ret', 0.0):.2%}`",
        "",
        "## Model Backtest Snapshot",
        "",
    ]
    if backtest.get("available"):
        lines.extend([
            f"- range: `{backtest.get('date_min')}` ~ `{backtest.get('date_max')}`",
            f"- trades: `{backtest.get('rows')}`",
            f"- win_rate: `{backtest.get('win_rate', 0.0):.2%}`",
            f"- avg_net_ret: `{backtest.get('avg_net_ret', 0.0):.2%}`",
            f"- sum_net_ret: `{backtest.get('sum_net_ret', 0.0):.2%}`",
        ])
    else:
        lines.append("- unavailable")

    params = report.get("simulation_params") or {}
    lines.extend([
        "",
        "## Runtime Dry-Run Policy",
        "",
        f"- mode: `{params.get('mode')}`",
        f"- entry: `{params.get('entry')}`",
        f"- order_type: `{params.get('entry_order_type_desc')}` (`{params.get('entry_order_type_code')}`)",
        f"- simulation_cash_krw: `{params.get('simulation_cash_krw')}`",
        "",
        "## Simulated Trades",
        "",
        "| code | name | status | guard | qty | entry | exit | net_ret | reason |",
        "| --- | --- | --- | --- | ---: | --- | --- | ---: | --- |",
    ])
    for row in report.get("simulated_trades", []):
        net_ret = row.get("net_ret")
        net_txt = "" if net_ret is None else f"{float(net_ret):.2%}"
        lines.append(
            f"| `{row.get('code')}` | {row.get('name', '')} | `{row.get('status')}` | "
            f"`{row.get('entry_guard', '-')}` | {int(row.get('buy_qty') or 0)} | "
            f"{row.get('entry_date', '')} | {row.get('exit_date', '')} | {net_txt} | {row.get('exit_reason', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_swing_daily_simulation_report(
    target_date: str | date | datetime | None = None,
    *,
    output_dir: str | Path | None = None,
    **kwargs,
) -> dict:
    date_key = _date_text(target_date)
    report = build_swing_daily_simulation_report(date_key, **kwargs)
    out_dir = Path(output_dir) if output_dir is not None else REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"swing_daily_simulation_{date_key}.json"
    md_path = out_dir / f"swing_daily_simulation_{date_key}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    report["paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily swing recommendation simulation report")
    parser.add_argument("--date", default=_date_text(None))
    parser.add_argument("--recommendation-path", default=RECO_PATH)
    args = parser.parse_args()
    report = write_swing_daily_simulation_report(args.date, recommendation_path=args.recommendation_path)
    print(json.dumps(report.get("paths", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
