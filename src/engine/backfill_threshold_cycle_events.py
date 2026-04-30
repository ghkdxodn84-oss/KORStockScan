"""Stream raw pipeline events into compact threshold-cycle event files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.engine.daily_threshold_cycle_report import TARGET_STAGES, THRESHOLD_CYCLE_DIR
from src.utils.constants import DATA_DIR


def raw_pipeline_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def compact_threshold_path(target_date: str) -> Path:
    THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    return THRESHOLD_CYCLE_DIR / f"threshold_events_{target_date}.jsonl"


def backfill_threshold_cycle_events(target_date: str, *, overwrite: bool = False) -> dict:
    source = raw_pipeline_path(target_date)
    target = compact_threshold_path(target_date)
    if not source.exists():
        return {"target_date": target_date, "source_exists": False, "written": 0, "target": str(target)}
    if overwrite and target.exists():
        target.unlink()

    written = 0
    with open(source, "r", encoding="utf-8", errors="replace") as src, open(target, "a", encoding="utf-8") as dst:
        for raw_line in src:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            if payload.get("event_type") not in (None, "", "pipeline_event"):
                continue
            if str(payload.get("stage") or "") not in TARGET_STAGES:
                continue
            compact_payload = {
                "schema_version": 1,
                "event_type": "threshold_cycle_event",
                "pipeline": payload.get("pipeline"),
                "stage": payload.get("stage"),
                "stock_name": payload.get("stock_name"),
                "stock_code": payload.get("stock_code"),
                "record_id": payload.get("record_id"),
                "fields": payload.get("fields") or {},
                "emitted_at": payload.get("emitted_at"),
                "emitted_date": payload.get("emitted_date"),
            }
            dst.write(json.dumps(compact_payload, ensure_ascii=False) + "\n")
            written += 1

    return {
        "target_date": target_date,
        "source_exists": True,
        "written": written,
        "target": str(target),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill compact threshold-cycle events from raw pipeline events.")
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing compact file")
    args = parser.parse_args(argv)
    summary = backfill_threshold_cycle_events(args.date, overwrite=args.overwrite)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
