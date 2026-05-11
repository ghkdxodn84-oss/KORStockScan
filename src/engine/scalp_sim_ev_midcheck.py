"""Build an intraday EV snapshot for the scalp live simulator."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR


SYNTHETIC_NAMES = {"TEST", "DUMMY", "MOCK"}


def _as_float(value, default=None):
    try:
        if value is None:
            return default
        numeric = float(str(value).replace("%", "").replace("+", "").strip())
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _is_synthetic_event(row: dict) -> bool:
    name = str(row.get("stock_name") or "").strip().upper()
    code = str(row.get("stock_code") or "").strip()[:6]
    return name in SYNTHETIC_NAMES or code == "123456"


def _percentile(values: list[float], pct: float):
    if not values:
        return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct / 100
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] * (hi - k) + ordered[hi] * (k - lo)


def _metrics(values: list[float]) -> dict:
    if not values:
        return {
            "sample": 0,
            "sum_profit_pct": 0.0,
            "avg_profit_pct": None,
            "median_profit_pct": None,
            "win_rate_pct": None,
            "loss_rate_pct": None,
            "gross_win_pct": 0.0,
            "gross_loss_pct": 0.0,
            "min_profit_pct": None,
            "max_profit_pct": None,
            "p25_profit_pct": None,
            "p75_profit_pct": None,
            "p90_profit_pct": None,
        }
    return {
        "sample": len(values),
        "sum_profit_pct": round(sum(values), 4),
        "avg_profit_pct": round(statistics.mean(values), 4),
        "median_profit_pct": round(statistics.median(values), 4),
        "win_rate_pct": round(100 * sum(v > 0 for v in values) / len(values), 2),
        "loss_rate_pct": round(100 * sum(v < 0 for v in values) / len(values), 2),
        "gross_win_pct": round(sum(v for v in values if v > 0), 4),
        "gross_loss_pct": round(sum(v for v in values if v < 0), 4),
        "min_profit_pct": round(min(values), 4),
        "max_profit_pct": round(max(values), 4),
        "p25_profit_pct": round(_percentile(values, 25), 4),
        "p75_profit_pct": round(_percentile(values, 75), 4),
        "p90_profit_pct": round(_percentile(values, 90), 4),
    }


def build_report(target_date: str) -> dict:
    path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    rows = _load_jsonl(path)
    sim_counts: Counter[str] = Counter()
    completed: list[dict] = []
    expired: list[dict] = []
    real_completed: list[dict] = []
    latest = None
    synthetic_excluded = 0

    for row in rows:
        latest = row.get("emitted_at") or latest
        stage = str(row.get("stage") or "")
        fields = row.get("fields") or {}
        is_sim = stage.startswith("scalp_sim_") or fields.get("simulation_book") == "scalp_ai_buy_all"
        if is_sim and _is_synthetic_event(row):
            synthetic_excluded += 1
            continue
        if is_sim:
            sim_counts[stage] += 1
        if stage == "scalp_sim_sell_order_assumed_filled" and is_sim:
            completed.append(
                {
                    "emitted_at": row.get("emitted_at"),
                    "stock_name": row.get("stock_name"),
                    "stock_code": row.get("stock_code"),
                    "profit_rate": _as_float(fields.get("profit_rate")),
                    "buy_price": _as_float(fields.get("buy_price")),
                    "assumed_fill_price": _as_float(fields.get("assumed_fill_price")),
                    "sell_reason_type": fields.get("sell_reason_type"),
                    "exit_rule": fields.get("exit_rule"),
                    "exit_decision_source": fields.get("exit_decision_source"),
                    "simulation_fill_policy": fields.get("simulation_fill_policy"),
                    "sim_parent_record_id": fields.get("sim_parent_record_id"),
                }
            )
        if stage == "scalp_sim_entry_expired" and is_sim:
            expired.append(
                {
                    "emitted_at": row.get("emitted_at"),
                    "stock_name": row.get("stock_name"),
                    "stock_code": row.get("stock_code"),
                    "limit_price": fields.get("limit_price"),
                    "sim_parent_record_id": fields.get("sim_parent_record_id"),
                }
            )
        if stage == "sell_completed" and not _is_synthetic_event(row):
            real_completed.append(
                {
                    "emitted_at": row.get("emitted_at"),
                    "stock_name": row.get("stock_name"),
                    "stock_code": row.get("stock_code"),
                    "profit_rate": _as_float(fields.get("profit_rate")),
                    "exit_rule": fields.get("exit_rule"),
                }
            )

    profit_values = [row["profit_rate"] for row in completed if row["profit_rate"] is not None]
    return {
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(path),
        "latest_event_at": latest,
        "synthetic_excluded": synthetic_excluded,
        "sim_counts": dict(sorted(sim_counts.items())),
        "metrics": _metrics(profit_values),
        "completed": sorted(completed, key=lambda row: row["profit_rate"] if row["profit_rate"] is not None else -999, reverse=True),
        "expired": expired,
        "real_completed": real_completed,
        "judgement": "positive_ev_midcheck" if profit_values and statistics.mean(profit_values) > 0 else "non_positive_or_no_sample",
        "runtime_mutation": False,
    }


def _fmt_pct(value) -> str:
    if value is None:
        return "-"
    return f"{float(value):+.2f}%"


def write_outputs(report: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = report["target_date"]
    json_path = output_dir / f"scalp_sim_ev_midcheck_{target_date}.json"
    md_path = output_dir / f"scalp_sim_ev_midcheck_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    m = report["metrics"]
    lines = [
        f"# Scalp Sim EV Midcheck {target_date}",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- latest_event_at: `{report.get('latest_event_at') or '-'}`",
        f"- source: `{report['source_path']}`",
        f"- judgement: `{report['judgement']}`",
        f"- runtime_mutation: `{str(report['runtime_mutation']).lower()}`",
        f"- synthetic_excluded: `{report['synthetic_excluded']}`",
        "",
        "## Summary",
        "",
        f"- completed: `{m['sample']}`",
        f"- sum_profit_pct: `{_fmt_pct(m['sum_profit_pct'])}`",
        f"- avg_profit_pct: `{_fmt_pct(m['avg_profit_pct'])}`",
        f"- median_profit_pct: `{_fmt_pct(m['median_profit_pct'])}`",
        f"- win_rate_pct: `{m['win_rate_pct'] if m['win_rate_pct'] is not None else '-'}%`",
        f"- gross_win_pct: `{_fmt_pct(m['gross_win_pct'])}`",
        f"- gross_loss_pct: `{_fmt_pct(m['gross_loss_pct'])}`",
        "",
        "## Sim Stage Counts",
        "",
    ]
    for stage, count in report["sim_counts"].items():
        lines.append(f"- `{stage}`: `{count}`")
    lines.extend(["", "## Completed Rows", "", "| 종목 | 수익률 | exit_rule | source |", "| --- | ---: | --- | --- |"])
    for row in report["completed"]:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {_fmt_pct(row['profit_rate'])} | "
            f"{row.get('exit_rule') or '-'} | {row.get('exit_decision_source') or '-'} |"
        )
    lines.extend(["", "## Expired Entries", "", "| 종목 | limit_price | parent |", "| --- | ---: | --- |"])
    for row in report["expired"]:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {row.get('limit_price') or '-'} | "
            f"{row.get('sim_parent_record_id') or '-'} |"
        )
    lines.extend(["", "## Real Completed Reference", "", "| 종목 | 수익률 | exit_rule |", "| --- | ---: | --- |"])
    for row in report["real_completed"]:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {_fmt_pct(row['profit_rate'])} | "
            f"{row.get('exit_rule') or '-'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build scalp simulator intraday EV midcheck report.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument(
        "--output-dir",
        default=str(DATA_DIR / "report" / "scalp_simulator"),
    )
    args = parser.parse_args(argv)
    report = build_report(args.date)
    json_path, md_path = write_outputs(report, Path(args.output_dir))
    print(f"[SCALP_SIM_EV_MIDCHECK] json={json_path} md={md_path} judgement={report['judgement']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
