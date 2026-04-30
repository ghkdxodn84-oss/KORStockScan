"""Stream raw pipeline events into partitioned threshold-cycle event files."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine import system_metric_sampler
from src.engine.daily_threshold_cycle_report import THRESHOLD_CYCLE_DIR
from src.utils.constants import DATA_DIR
from src.utils.threshold_cycle_registry import threshold_family_for_stage


DEFAULT_MAX_INPUT_LINES_PER_CHUNK = 20_000
DEFAULT_MAX_OUTPUT_LINES_PER_PARTITION = 25_000
DEFAULT_MAX_CHUNK_READ_MB = 128.0
DEFAULT_MAX_IOWAIT_PCT = 20.0
DEFAULT_MIN_MEM_AVAILABLE_MB = 512.0

def raw_pipeline_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def compact_threshold_path(target_date: str) -> Path:
    THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    return THRESHOLD_CYCLE_DIR / f"threshold_events_{target_date}.jsonl"


def checkpoint_path(target_date: str) -> Path:
    return THRESHOLD_CYCLE_DIR / "checkpoints" / f"{target_date}.json"


def partition_dir(target_date: str, family: str) -> Path:
    return THRESHOLD_CYCLE_DIR / f"date={target_date}" / f"family={family}"


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    values: list[str] = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _source_fingerprint(source: Path) -> dict[str, Any]:
    stat = source.stat()
    return {
        "source_path": str(source),
        "source_size": int(stat.st_size),
        "source_mtime": float(stat.st_mtime),
    }


def _checkpoint_compatible(checkpoint: dict[str, Any], source_fp: dict[str, Any]) -> bool:
    if not checkpoint:
        return True
    if checkpoint.get("source_path") != source_fp["source_path"]:
        return False
    if int(checkpoint.get("source_size", 0) or 0) != int(source_fp["source_size"]):
        return False
    if checkpoint.get("completed") and int(checkpoint.get("source_size", 0) or 0) == int(source_fp["source_size"]):
        return True
    return float(checkpoint.get("source_mtime", 0.0) or 0.0) == float(source_fp["source_mtime"])


def _sample_metrics() -> dict[str, Any]:
    try:
        sample = system_metric_sampler.sample_once()
    except Exception as exc:
        return {"sample_error": str(exc)}
    return sample if isinstance(sample, dict) else {"sample_error": "invalid-sample"}


def _metric_value(sample: dict[str, Any], section: str, key: str, default: float = 0.0) -> float:
    value = (sample.get(section) or {}).get(key)
    try:
        return float(value)
    except Exception:
        return default


def _availability_pause_reason(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    max_iowait_pct: float,
    max_chunk_read_mb: float,
    min_mem_available_mb: float,
) -> str | None:
    if after.get("sample_error"):
        return None
    iowait_pct = _metric_value(after, "cpu", "iowait_pct")
    if iowait_pct >= max_iowait_pct:
        return f"iowait_pct>={max_iowait_pct:g}"
    mem_available = _metric_value(after, "memory", "mem_available_mb", default=999999.0)
    if mem_available < min_mem_available_mb:
        return f"mem_available_mb<{min_mem_available_mb:g}"
    before_read = _metric_value(before, "io", "disk_read_mb_delta")
    after_read = _metric_value(after, "io", "disk_read_mb_delta")
    if max(before_read, after_read) >= max_chunk_read_mb:
        return f"disk_read_mb_delta>={max_chunk_read_mb:g}"
    return None


def _recommend_next_input_line_cap(
    current_cap: int,
    pause_reason: str | None,
    after_sample: dict[str, Any],
) -> int:
    if pause_reason:
        return max(1_000, int(current_cap * 0.5))
    iowait_pct = _metric_value(after_sample, "cpu", "iowait_pct")
    read_mb = _metric_value(after_sample, "io", "disk_read_mb_delta")
    mem_available = _metric_value(after_sample, "memory", "mem_available_mb", default=999999.0)
    if iowait_pct <= 5.0 and read_mb <= 64.0 and mem_available >= 1024.0:
        return min(DEFAULT_MAX_INPUT_LINES_PER_CHUNK, max(current_cap, int(current_cap * 1.25)))
    return current_cap


def _partition_path(target_date: str, family: str, part_number: int) -> Path:
    return partition_dir(target_date, family) / f"part-{part_number:06d}.jsonl"


def _initial_partition_state(checkpoint: dict[str, Any]) -> dict[str, dict[str, int]]:
    state = checkpoint.get("partitions") if isinstance(checkpoint.get("partitions"), dict) else {}
    result: dict[str, dict[str, int]] = {}
    for family, payload in state.items():
        if not isinstance(payload, dict):
            continue
        result[str(family)] = {
            "part": int(payload.get("part", 1) or 1),
            "line_count": int(payload.get("line_count", 0) or 0),
        }
    return result


def _write_compact_payload(
    *,
    target_date: str,
    payload: dict[str, Any],
    partition_state: dict[str, dict[str, int]],
    max_output_lines_per_partition: int,
) -> tuple[bool, str | None]:
    stage = str(payload.get("stage") or "")
    family = threshold_family_for_stage(stage, payload.get("fields") if isinstance(payload.get("fields"), dict) else None)
    if not family:
        return False, "not_threshold_cycle_stage"
    state = partition_state.setdefault(family, {"part": 1, "line_count": 0})
    if state["line_count"] >= max_output_lines_per_partition:
        state["part"] += 1
        state["line_count"] = 0
        return False, "output_partition_line_cap"

    target = _partition_path(target_date, family, state["part"])
    target.parent.mkdir(parents=True, exist_ok=True)
    compact_payload = {
        "schema_version": 1,
        "event_type": "threshold_cycle_event",
        "family": family,
        "pipeline": payload.get("pipeline"),
        "stage": stage,
        "stock_name": payload.get("stock_name"),
        "stock_code": payload.get("stock_code"),
        "record_id": payload.get("record_id"),
        "fields": payload.get("fields") or {},
        "emitted_at": payload.get("emitted_at"),
        "emitted_date": payload.get("emitted_date"),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(compact_payload, ensure_ascii=False) + "\n")
    state["line_count"] += 1
    return True, None


def _reset_outputs(target_date: str) -> None:
    legacy = compact_threshold_path(target_date)
    if legacy.exists():
        legacy.unlink()
    base = THRESHOLD_CYCLE_DIR / f"date={target_date}"
    if base.exists():
        shutil.rmtree(base)
    cp = checkpoint_path(target_date)
    if cp.exists():
        cp.unlink()


def backfill_threshold_cycle_events(
    target_date: str,
    *,
    mode: str = "bootstrap",
    resume: bool = True,
    overwrite: bool = False,
    max_input_lines_per_chunk: int = DEFAULT_MAX_INPUT_LINES_PER_CHUNK,
    max_output_lines_per_partition: int = DEFAULT_MAX_OUTPUT_LINES_PER_PARTITION,
    max_iowait_pct: float = DEFAULT_MAX_IOWAIT_PCT,
    max_chunk_read_mb: float = DEFAULT_MAX_CHUNK_READ_MB,
    min_mem_available_mb: float = DEFAULT_MIN_MEM_AVAILABLE_MB,
) -> dict[str, Any]:
    source = raw_pipeline_path(target_date)
    checkpoint_file = checkpoint_path(target_date)
    if overwrite:
        _reset_outputs(target_date)
    if not source.exists():
        return {"target_date": target_date, "source_exists": False, "written": 0, "checkpoint": str(checkpoint_file)}

    source_fp = _source_fingerprint(source)
    checkpoint = _load_json(checkpoint_file) if resume else {}
    if not _checkpoint_compatible(checkpoint, source_fp):
        summary = {
            "target_date": target_date,
            "source_exists": True,
            "status": "stopped_source_changed",
            "written": 0,
            "checkpoint": str(checkpoint_file),
            "source": source_fp,
        }
        _save_json(checkpoint_file, {**source_fp, **summary, "completed": False})
        return summary

    byte_offset = int(checkpoint.get("byte_offset", 0) or 0)
    raw_line_count = int(checkpoint.get("raw_line_count", 0) or 0)
    written_total = int(checkpoint.get("written_count", 0) or 0)
    partition_state = _initial_partition_state(checkpoint)

    before_sample = _sample_metrics()
    written_this_run = 0
    processed_this_run = 0
    pause_reason: str | None = None

    with source.open("r", encoding="utf-8", errors="replace") as src:
        src.seek(byte_offset)
        while processed_this_run < max_input_lines_per_chunk:
            line_start = src.tell()
            raw_line = src.readline()
            if not raw_line:
                break
            byte_offset = src.tell()
            raw_line_count += 1
            processed_this_run += 1
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
            if not threshold_family_for_stage(
                str(payload.get("stage") or ""),
                payload.get("fields") if isinstance(payload.get("fields"), dict) else None,
            ):
                continue
            wrote, reason = _write_compact_payload(
                target_date=target_date,
                payload=payload,
                partition_state=partition_state,
                max_output_lines_per_partition=max_output_lines_per_partition,
            )
            if not wrote:
                byte_offset = line_start
                raw_line_count -= 1
                pause_reason = reason
                break
            written_this_run += 1
            written_total += 1

    after_sample = _sample_metrics()
    if pause_reason is None:
        pause_reason = _availability_pause_reason(
            before_sample,
            after_sample,
            max_iowait_pct=max_iowait_pct,
            max_chunk_read_mb=max_chunk_read_mb,
            min_mem_available_mb=min_mem_available_mb,
        )
    recommended_next_input_lines_per_chunk = _recommend_next_input_line_cap(
        max_input_lines_per_chunk,
        pause_reason,
        after_sample,
    )

    completed = pause_reason is None and byte_offset >= source_fp["source_size"]
    status = "completed" if completed else "paused_by_availability_guard" if pause_reason else "paused_by_chunk_limit"
    checkpoint_payload = {
        **source_fp,
        "target_date": target_date,
        "mode": mode,
        "byte_offset": byte_offset,
        "raw_line_count": raw_line_count,
        "written_count": written_total,
        "written_this_run": written_this_run,
        "processed_this_run": processed_this_run,
        "partitions": partition_state,
        "completed": completed,
        "paused_reason": pause_reason,
        "recommended_next_input_lines_per_chunk": recommended_next_input_lines_per_chunk,
        "last_sample_metrics": {"before": before_sample, "after": after_sample},
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _save_json(checkpoint_file, checkpoint_payload)

    return {
        "target_date": target_date,
        "source_exists": True,
        "status": status,
        "mode": mode,
        "written": written_this_run,
        "written_total": written_total,
        "processed": processed_this_run,
        "byte_offset": byte_offset,
        "source_size": source_fp["source_size"],
        "completed": completed,
        "paused_reason": pause_reason,
        "recommended_next_input_lines_per_chunk": recommended_next_input_lines_per_chunk,
        "checkpoint": str(checkpoint_file),
        "partition_root": str(THRESHOLD_CYCLE_DIR / f"date={target_date}"),
    }


def backfill_threshold_cycle_range(
    start_date: str,
    end_date: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return [backfill_threshold_cycle_events(target_date, **kwargs) for target_date in _date_range(start_date, end_date)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill compact threshold-cycle events from raw pipeline events.")
    single_or_range = parser.add_mutually_exclusive_group(required=True)
    single_or_range.add_argument("--date", help="Target date (YYYY-MM-DD)")
    single_or_range.add_argument("--from-date", dest="from_date", help="Start date for range bootstrap (YYYY-MM-DD)")
    parser.add_argument("--to-date", dest="to_date", help="End date for range bootstrap (YYYY-MM-DD)")
    parser.add_argument("--mode", choices=["bootstrap", "incremental"], default="bootstrap")
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--overwrite", action="store_true", help="Replace existing compact output/checkpoint")
    parser.add_argument("--max-input-lines-per-chunk", type=int, default=DEFAULT_MAX_INPUT_LINES_PER_CHUNK)
    parser.add_argument("--max-output-lines-per-partition", type=int, default=DEFAULT_MAX_OUTPUT_LINES_PER_PARTITION)
    parser.add_argument("--max-iowait-pct", type=float, default=DEFAULT_MAX_IOWAIT_PCT)
    parser.add_argument("--max-chunk-read-mb", type=float, default=DEFAULT_MAX_CHUNK_READ_MB)
    parser.add_argument("--min-mem-available-mb", type=float, default=DEFAULT_MIN_MEM_AVAILABLE_MB)
    args = parser.parse_args(argv)

    options = {
        "mode": args.mode,
        "resume": args.resume,
        "overwrite": args.overwrite,
        "max_input_lines_per_chunk": args.max_input_lines_per_chunk,
        "max_output_lines_per_partition": args.max_output_lines_per_partition,
        "max_iowait_pct": args.max_iowait_pct,
        "max_chunk_read_mb": args.max_chunk_read_mb,
        "min_mem_available_mb": args.min_mem_available_mb,
    }
    if args.date:
        summary: dict[str, Any] | list[dict[str, Any]] = backfill_threshold_cycle_events(args.date, **options)
    else:
        if not args.to_date:
            parser.error("--to-date is required with --from-date")
        summary = backfill_threshold_cycle_range(args.from_date, args.to_date, **options)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
