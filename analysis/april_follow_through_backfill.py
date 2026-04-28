"""Lightweight monthly backfill for soft-stop/follow-through candidate screening.

Reads saved trade_review snapshots and post_sell candidate/evaluation files only.
Avoids heavy foreground report builders so it can be used during intraday hours
for static periods such as "through yesterday".
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.engine.holding_exit_observation_report import (
    _build_same_symbol_reentry,
    _date_range,
    _entry_mode,
    _fill_quality,
    _is_post_fallback,
    _is_pyramid_activated,
    _is_valid_completed_trade,
    _load_post_sell_rows,
    _load_saved_snapshots,
    _safe_float,
    _safe_int,
    _trade_id,
    _trade_rows_from_snapshots,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _classify_soft_stop(row: dict[str, Any]) -> str:
    peak_profit = float(_safe_float(row.get("peak_profit"), 0.0) or 0.0)
    rebound_sell_10m = bool(row.get("rebound_above_sell_10m"))
    rebound_buy_10m = bool(row.get("rebound_above_buy_10m"))
    ai_drop_fast = False  # Filled only when deeper per-trade raw timeline is joined later.

    if rebound_buy_10m or rebound_sell_10m:
        return "whipsaw"
    if peak_profit <= 0.2 and not rebound_sell_10m and not rebound_buy_10m:
        return "good_cut_candidate"
    if ai_drop_fast:
        return "good_cut_candidate"
    return "ambiguous"


def _build_follow_through_candidates(
    *,
    valid_trades: list[dict[str, Any]],
    post_sell_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    post_sell_by_trade_id = {
        str(row.get("recommendation_id") or ""): row for row in post_sell_rows if row.get("recommendation_id")
    }
    candidates: list[dict[str, Any]] = []
    for trade in valid_trades:
        trade_id = _trade_id(trade)
        if not trade_id:
            continue
        post_sell = post_sell_by_trade_id.get(trade_id)
        if not post_sell:
            continue
        exit_rule = str(post_sell.get("exit_rule") or "")
        peak_profit = float(_safe_float(post_sell.get("peak_profit"), 0.0) or 0.0)
        held_sec = int(_safe_int(post_sell.get("held_sec"), 0))
        profit_rate = float(_safe_float(post_sell.get("profit_rate"), 0.0) or 0.0)
        entry_mode = _entry_mode(trade)
        if (
            entry_mode == "normal"
            and _is_post_fallback(trade)
            and not _is_pyramid_activated(trade)
            and _fill_quality(trade) == "full_fill"
            and exit_rule == "scalp_soft_stop_pct"
            and peak_profit <= 0.2
            and held_sec <= 300
        ):
            candidates.append(
                {
                    "recommendation_id": int(_safe_int(trade_id, 0)),
                    "code": str(trade.get("code") or ""),
                    "name": str(trade.get("name") or ""),
                    "buy_time": str(trade.get("buy_time") or ""),
                    "sell_time": str(trade.get("sell_time") or ""),
                    "entry_mode": entry_mode,
                    "fill_quality": _fill_quality(trade),
                    "peak_profit": round(peak_profit, 3),
                    "held_sec": held_sec,
                    "profit_rate": round(profit_rate, 3),
                    "rebound_above_sell_10m": bool(post_sell.get("rebound_above_sell_10m")),
                    "rebound_above_buy_10m": bool(post_sell.get("rebound_above_buy_10m")),
                    "mfe_10m_pct": round(float(_safe_float(post_sell.get("mfe_10m_pct"), 0.0) or 0.0), 3),
                    "close_ret_10m_pct": round(
                        float(_safe_float(post_sell.get("close_ret_10m_pct"), 0.0) or 0.0), 3
                    ),
                }
            )
    return sorted(candidates, key=lambda item: (item["held_sec"], item["profit_rate"]))


def build_monthly_backfill(*, month_start: str, target_date: str) -> dict[str, Any]:
    dates = _date_range(month_start, target_date)
    trade_snapshots, trade_snapshot_paths = _load_saved_snapshots("trade_review", dates)
    valid_trades = [row for row in _trade_rows_from_snapshots(trade_snapshots) if _is_valid_completed_trade(row)]
    post_sell_rows, post_sell_paths = _load_post_sell_rows(dates)
    same_symbol_reentry = _build_same_symbol_reentry(valid_trades)

    soft_stop_rows = [
        row for row in post_sell_rows if str(row.get("exit_rule") or "") == "scalp_soft_stop_pct"
    ]
    soft_stop_labels = Counter(_classify_soft_stop(row) for row in soft_stop_rows)
    follow_through_candidates = _build_follow_through_candidates(
        valid_trades=valid_trades,
        post_sell_rows=post_sell_rows,
    )

    return {
        "meta": {
            "month_start": month_start,
            "target_date": target_date,
            "dates": dates,
        },
        "input_summary": {
            "trade_review_snapshot_count": len(trade_snapshot_paths),
            "post_sell_file_count": len(post_sell_paths),
            "valid_completed_trades": len(valid_trades),
            "post_sell_rows": len(post_sell_rows),
            "soft_stop_rows": len(soft_stop_rows),
        },
        "source_paths": {
            "trade_review": trade_snapshot_paths,
            "post_sell": post_sell_paths,
        },
        "soft_stop_screening": {
            "labels": {
                "good_cut_candidate": int(soft_stop_labels.get("good_cut_candidate", 0)),
                "whipsaw": int(soft_stop_labels.get("whipsaw", 0)),
                "ambiguous": int(soft_stop_labels.get("ambiguous", 0)),
            },
            "top_cases": {
                "good_cut_candidate": [
                    {
                        "recommendation_id": int(_safe_int(row.get("recommendation_id"), 0)),
                        "code": str(row.get("stock_code") or ""),
                        "name": str(row.get("stock_name") or ""),
                        "profit_rate": round(float(_safe_float(row.get("profit_rate"), 0.0) or 0.0), 3),
                        "peak_profit": round(float(_safe_float(row.get("peak_profit"), 0.0) or 0.0), 3),
                        "held_sec": int(_safe_int(row.get("held_sec"), 0)),
                        "mfe_10m_pct": round(float(_safe_float(row.get("mfe_10m_pct"), 0.0) or 0.0), 3),
                        "close_ret_10m_pct": round(float(_safe_float(row.get("close_ret_10m_pct"), 0.0) or 0.0), 3),
                    }
                    for row in soft_stop_rows
                    if _classify_soft_stop(row) == "good_cut_candidate"
                ][:10],
                "whipsaw": [
                    {
                        "recommendation_id": int(_safe_int(row.get("recommendation_id"), 0)),
                        "code": str(row.get("stock_code") or ""),
                        "name": str(row.get("stock_name") or ""),
                        "profit_rate": round(float(_safe_float(row.get("profit_rate"), 0.0) or 0.0), 3),
                        "peak_profit": round(float(_safe_float(row.get("peak_profit"), 0.0) or 0.0), 3),
                        "held_sec": int(_safe_int(row.get("held_sec"), 0)),
                        "rebound_above_sell_10m": bool(row.get("rebound_above_sell_10m")),
                        "rebound_above_buy_10m": bool(row.get("rebound_above_buy_10m")),
                        "mfe_10m_pct": round(float(_safe_float(row.get("mfe_10m_pct"), 0.0) or 0.0), 3),
                    }
                    for row in soft_stop_rows
                    if _classify_soft_stop(row) == "whipsaw"
                ][:10],
            },
        },
        "follow_through_failure_screening": {
            "candidate_count": len(follow_through_candidates),
            "top_cases": follow_through_candidates[:20],
        },
        "same_symbol_reentry": {
            "total_reentries": int(same_symbol_reentry.get("total_reentries", 0)),
            "after_soft_stop_count": int(same_symbol_reentry.get("after_soft_stop_count", 0)),
            "after_soft_stop_next_loss_count": int(
                same_symbol_reentry.get("after_soft_stop_next_loss_count", 0)
            ),
        },
    }


def _write_markdown(summary: dict[str, Any], path: Path) -> None:
    soft_stop = summary["soft_stop_screening"]
    follow = summary["follow_through_failure_screening"]
    inputs = summary["input_summary"]
    lines = [
        "# April Follow-Through Backfill",
        "",
        f"- period: `{summary['meta']['month_start']} ~ {summary['meta']['target_date']}`",
        f"- trade_review_snapshots: `{inputs['trade_review_snapshot_count']}`",
        f"- post_sell_files: `{inputs['post_sell_file_count']}`",
        f"- valid_completed_trades: `{inputs['valid_completed_trades']}`",
        f"- post_sell_rows: `{inputs['post_sell_rows']}`",
        f"- soft_stop_rows: `{inputs['soft_stop_rows']}`",
        "",
        "## Soft Stop Screening",
        "",
        f"- good_cut_candidate: `{soft_stop['labels']['good_cut_candidate']}`",
        f"- whipsaw: `{soft_stop['labels']['whipsaw']}`",
        f"- ambiguous: `{soft_stop['labels']['ambiguous']}`",
        "",
        "## Follow-Through Failure Screening",
        "",
        f"- candidate_count: `{follow['candidate_count']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight monthly soft-stop/follow-through screening")
    parser.add_argument("--month-start", required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--output-dir", default="tmp/monthly_backfill")
    parser.add_argument("--label", default=None)
    args = parser.parse_args()

    summary = build_monthly_backfill(month_start=args.month_start, target_date=args.target_date)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    label = str(args.label or args.target_date).strip()
    json_path = output_dir / f"april_follow_through_backfill_{label}.json"
    md_path = output_dir / f"april_follow_through_backfill_{label}.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(summary, md_path)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "soft_stop_rows": summary["input_summary"]["soft_stop_rows"], "follow_through_candidates": summary["follow_through_failure_screening"]["candidate_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
