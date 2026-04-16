"""Report `ADD_BLOCKED reason=add_judgment_locked` distribution for monitoring axis #5."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.log_archive_service import iter_target_log_lines, save_monitor_snapshot
from src.utils.constants import DATA_DIR, LOGS_DIR


_ADD_BLOCKED_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[ADD_BLOCKED\] "
    r"(?P<name>.+?)\((?P<code>\d+)\) "
    r"strategy=(?P<strategy>[^\s]+) "
    r"reason=(?P<reason>[^\s]+)"
)
_HOLDING_REVIEW_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[HOLDING_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>\d+)\) stage=ai_holding_review(?P<rest>.*)$"
)
_FIELD_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _parse_since_datetime(target_date: str, since_time: str | None) -> datetime | None:
    if not since_time:
        return None
    candidate = str(since_time).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            if fmt.startswith("%Y"):
                return datetime.strptime(candidate, fmt)
            return datetime.strptime(f"{target_date} {candidate}", f"%Y-%m-%d {fmt}")
        except Exception:
            continue
    return None


def _bucket_5m(ts: datetime) -> str:
    minute = (ts.minute // 5) * 5
    return f"{ts.strftime('%H')}:{minute:02d}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Add-Judgment-Lock Report ({summary['target_date']})")
    lines.append("")
    lines.append(f"- generated_at: `{summary['generated_at']}`")
    lines.append(f"- total_blocked_events: `{summary['total_blocked_events']}`")
    lines.append(f"- stagnation_held_threshold_sec: `{summary['stagnation_held_threshold_sec']}`")
    lines.append(f"- stagnation_blocked_events: `{summary['stagnation_blocked_events']}`")
    lines.append("")
    lines.append("## By Stock")
    lines.append("")
    lines.append("| stock | blocked_count | latest_held_sec | latest_profit_rate | stagnation_cohort |")
    lines.append("|---|---:|---:|---:|---|")
    for row in summary.get("by_stock", []):
        lines.append(
            f"| `{row['stock']}` | `{row['blocked_count']}` | `{row['latest_held_sec']}` | "
            f"`{row['latest_profit_rate']:+.2f}` | `{str(row['stagnation_cohort']).lower()}` |"
        )
    lines.append("")
    lines.append("## By Time Bucket (5m)")
    lines.append("")
    lines.append("| bucket | blocked_count |")
    lines.append("|---|---:|")
    for row in summary.get("by_time_bucket", []):
        lines.append(f"| `{row['bucket']}` | `{row['blocked_count']}` |")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_add_blocked_lock_report(
    *,
    target_date: str | None = None,
    since_time: str | None = None,
    stagnation_held_threshold_sec: int = 600,
    top_n: int = 20,
) -> dict[str, Any]:
    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")
    since_dt = _parse_since_datetime(target_date, since_time)

    log_paths = [
        LOGS_DIR / "sniper_state_handlers_info.log",
        LOGS_DIR / "pipeline_event_logger_info.log",
    ]
    add_lines = iter_target_log_lines([log_paths[0]], target_date=target_date, marker="[ADD_BLOCKED]")
    holding_lines = iter_target_log_lines([log_paths[1]], target_date=target_date, marker="[HOLDING_PIPELINE]")

    by_stock_counter: Counter[str] = Counter()
    by_bucket_counter: Counter[str] = Counter()
    blocked_events: list[dict[str, Any]] = []

    for line in add_lines:
        m = _ADD_BLOCKED_RE.match(line.strip())
        if not m:
            continue
        if m.group("reason") != "add_judgment_locked":
            continue
        try:
            ts = datetime.strptime(m.group("timestamp"), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if since_dt and ts < since_dt:
            continue
        stock = f"{m.group('name')}({m.group('code')})"
        by_stock_counter[stock] += 1
        by_bucket_counter[_bucket_5m(ts)] += 1
        blocked_events.append({"stock": stock, "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S")})

    latest_holding_by_stock: dict[str, dict[str, Any]] = {}
    for line in holding_lines:
        m = _HOLDING_REVIEW_RE.match(line.strip())
        if not m:
            continue
        try:
            ts = datetime.strptime(m.group("timestamp"), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if since_dt and ts < since_dt:
            continue
        fields = {
            g.group("key"): str(g.group("value") or "")
            for g in _FIELD_RE.finditer(m.group("rest") or "")
        }
        stock = f"{m.group('name')}({m.group('code')})"
        latest_holding_by_stock[stock] = {
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "held_sec": _safe_int(fields.get("held_sec"), 0),
            "profit_rate": _safe_float(fields.get("profit_rate"), 0.0),
        }

    by_stock_rows: list[dict[str, Any]] = []
    for stock, count in by_stock_counter.most_common(top_n):
        held = latest_holding_by_stock.get(stock, {})
        latest_held = _safe_int(held.get("held_sec"), 0)
        by_stock_rows.append(
            {
                "stock": stock,
                "blocked_count": int(count),
                "latest_held_sec": latest_held,
                "latest_profit_rate": float(_safe_float(held.get("profit_rate"), 0.0)),
                "stagnation_cohort": bool(latest_held >= stagnation_held_threshold_sec),
                "latest_review_timestamp": held.get("timestamp", ""),
            }
        )

    stagnation_stocks = {row["stock"] for row in by_stock_rows if row["stagnation_cohort"]}
    stagnation_blocked_events = sum(
        1 for event in blocked_events if event.get("stock") in stagnation_stocks
    )

    summary = {
        "target_date": target_date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "since_time": since_time or "",
        "stagnation_held_threshold_sec": int(stagnation_held_threshold_sec),
        "total_blocked_events": int(sum(by_stock_counter.values())),
        "stagnation_blocked_events": int(stagnation_blocked_events),
        "by_stock": by_stock_rows,
        "by_time_bucket": [
            {"bucket": bucket, "blocked_count": int(count)}
            for bucket, count in sorted(by_bucket_counter.items(), key=lambda x: x[0])
        ],
    }
    return summary


def _write_artifacts(summary: dict[str, Any]) -> dict[str, str]:
    target_date = str(summary["target_date"])
    snapshot_path = save_monitor_snapshot("add_blocked_lock", target_date, summary)

    report_dir = DATA_DIR / "report" / "monitor_snapshots"
    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / f"add_blocked_lock_{target_date}.md"
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    return {"snapshot_path": str(snapshot_path), "markdown_path": str(md_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build add_judgment_locked blocker monitoring report.")
    parser.add_argument("--date", dest="target_date", default=None, help="Target date (YYYY-MM-DD).")
    parser.add_argument("--since", dest="since_time", default=None, help="Optional since time (HH:MM[:SS]).")
    parser.add_argument("--stagnation-held-sec", type=int, default=600)
    parser.add_argument("--top", dest="top_n", type=int, default=20)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    summary = build_add_blocked_lock_report(
        target_date=args.target_date,
        since_time=args.since_time,
        stagnation_held_threshold_sec=args.stagnation_held_sec,
        top_n=args.top_n,
    )
    artifacts = _write_artifacts(summary)
    summary.update(artifacts)

    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            f"[ADD_BLOCKED_LOCK_REPORT] date={summary['target_date']} "
            f"total={summary['total_blocked_events']} "
            f"stagnation={summary['stagnation_blocked_events']} "
            f"snapshot={summary['snapshot_path']} "
            f"markdown={summary['markdown_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
