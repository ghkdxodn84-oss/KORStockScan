"""Standalone local analyzer for entry latency offline bundles."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


_ENTRY_PIPELINE = "ENTRY_PIPELINE"
_HOLDING_PIPELINE = "HOLDING_PIPELINE"
_GATEKEEPER_DECISION_STAGES = {
    "blocked_gatekeeper_reject",
    "market_regime_pass",
    "blocked_gatekeeper_error",
}
_ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
_REUSE_REASON_LABELS = {
    "sig_changed": "시그니처 변경",
    "age_expired": "재사용 창 만료",
    "ws_stale": "WS stale",
    "price_move": "가격 변화 확대",
    "near_ai_exit": "AI 손절 경계",
    "near_safe_profit": "안전수익 경계",
    "near_low_score": "저점수 경계",
    "score_boundary": "점수 경계",
    "missing_action": "이전 액션 없음",
    "missing_allow_flag": "이전 허용값 없음",
}


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-", "None"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 1)


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    result = ordered[lower] * (1.0 - weight) + ordered[upper] * weight
    return round(result, 2)


def _parse_event_dt(raw_value: str | None) -> datetime | None:
    raw = str(raw_value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("T", " ")
    if len(normalized) >= 19:
        normalized = normalized[:19]
    try:
        return datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _resolve_window_dt(target_date: str, time_value: str | None) -> datetime | None:
    if not time_value:
        return None
    raw = str(time_value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            if fmt.startswith("%Y"):
                return datetime.strptime(raw, fmt)
            return datetime.strptime(f"{target_date} {raw}", f"%Y-%m-%d {fmt}")
        except Exception:
            continue
    return None


def _split_reason_codes(raw_value: Any) -> list[str]:
    raw = str(raw_value or "").strip()
    if not raw or raw == "-":
        return []
    return [token.strip() for token in raw.split(",") if token.strip()]


def _friendly_reason_name(reason_code: str) -> str:
    code = str(reason_code or "").strip()
    return _REUSE_REASON_LABELS.get(code, code or "-")


def _count_sig_delta_fields(counter: Counter[str], raw_value: Any) -> None:
    raw = str(raw_value or "").strip()
    if not raw or raw == "-":
        return
    for token in raw.split(","):
        field = token.split(":", 1)[0].strip()
        if field:
            counter[field] += 1


def _count_csv_values(counter: Counter[str], raw_value: Any) -> None:
    raw = str(raw_value or "").strip()
    if not raw or raw == "-":
        return
    for token in raw.split(","):
        clean = token.strip()
        if clean:
            counter[clean] += 1


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _load_manifest(bundle_dir: Path) -> dict[str, Any]:
    path = bundle_dir / "bundle_manifest.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _infer_target_date(bundle_dir: Path) -> str:
    for candidate in (bundle_dir / "data" / "pipeline_events").glob("pipeline_events_*.jsonl"):
        name = candidate.stem
        if name.startswith("pipeline_events_"):
            return name.replace("pipeline_events_", "", 1)
    return ""


def _locate_pipeline_events(bundle_dir: Path, target_date: str) -> Path:
    preferred = bundle_dir / "data" / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if preferred.exists():
        return preferred
    fallback = list(bundle_dir.rglob(f"pipeline_events_{target_date}.jsonl"))
    if fallback:
        return fallback[0]
    raise FileNotFoundError(f"missing pipeline events bundle for {target_date}: {preferred}")


def build_summary(
    *,
    bundle_dir: Path,
    target_date: str | None = None,
    since_time: str | None = "09:00:00",
    until_time: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    manifest = _load_manifest(bundle_dir)
    resolved_target_date = str(target_date or manifest.get("target_date") or _infer_target_date(bundle_dir)).strip()
    if not resolved_target_date:
        raise ValueError("target_date is required when bundle manifest is missing")
    resolved_until = str(until_time or manifest.get("evidence_cutoff") or "").strip() or None
    pipeline_path = _locate_pipeline_events(bundle_dir, resolved_target_date)
    since_dt = _resolve_window_dt(resolved_target_date, since_time)
    until_dt = _resolve_window_dt(resolved_target_date, resolved_until)

    rows = _read_jsonl(pipeline_path)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        emitted_dt = _parse_event_dt(str(row.get("emitted_at") or ""))
        if emitted_dt is None:
            continue
        if emitted_dt.date().isoformat() != resolved_target_date:
            continue
        if since_dt is not None and emitted_dt < since_dt:
            continue
        if until_dt is not None and emitted_dt > until_dt:
            continue
        filtered.append(row)

    entry_events = [row for row in filtered if str(row.get("pipeline") or "") == _ENTRY_PIPELINE]
    holding_events = [row for row in filtered if str(row.get("pipeline") or "") == _HOLDING_PIPELINE]
    gatekeeper_decisions = [row for row in entry_events if str(row.get("stage") or "") in _GATEKEEPER_DECISION_STAGES]
    gatekeeper_fast_reuse_events = [row for row in entry_events if str(row.get("stage") or "") == "gatekeeper_fast_reuse"]
    gatekeeper_bypass_events = [row for row in entry_events if str(row.get("stage") or "") == "gatekeeper_fast_reuse_bypass"]
    budget_pass_events = [row for row in entry_events if str(row.get("stage") or "") == "budget_pass"]
    submitted_events = [row for row in entry_events if str(row.get("stage") or "") == "order_bundle_submitted"]
    latency_block_events = [row for row in entry_events if str(row.get("stage") or "") == "latency_block"]
    latency_pass_events = [row for row in entry_events if str(row.get("stage") or "") == "latency_pass"]
    ai_confirmed_events = [row for row in entry_events if str(row.get("stage") or "") == "ai_confirmed"]
    entry_armed_events = [row for row in entry_events if str(row.get("stage") or "") in _ENTRY_ARMED_STAGES]
    fill_events = [row for row in holding_events if str(row.get("stage") or "") == "position_rebased_after_fill"]

    gatekeeper_eval_ms = []
    gatekeeper_model_call_ms = []
    gatekeeper_total_internal_ms = []
    gatekeeper_action_ages = []
    gatekeeper_allow_ages = []
    gatekeeper_cache_modes = Counter()
    gatekeeper_reuse_blockers: Counter[str] = Counter()
    gatekeeper_sig_deltas: Counter[str] = Counter()
    latency_reason_counts: Counter[str] = Counter()
    latency_danger_reason_counts: Counter[str] = Counter()
    quote_fresh_latency_blocks = 0
    quote_fresh_latency_passes = 0
    fill_quality_counts: Counter[str] = Counter()

    for row in gatekeeper_decisions:
        fields = row.get("fields") or {}
        gatekeeper_cache_modes[str(fields.get("gatekeeper_cache") or "miss")] += 1
        for source, container in (
            (fields.get("gatekeeper_eval_ms"), gatekeeper_eval_ms),
            (fields.get("gatekeeper_model_call_ms"), gatekeeper_model_call_ms),
            (fields.get("gatekeeper_total_internal_ms"), gatekeeper_total_internal_ms),
        ):
            parsed = _safe_float(source)
            if parsed is not None:
                container.append(parsed)

    for row in gatekeeper_bypass_events:
        fields = row.get("fields") or {}
        for code in _split_reason_codes(fields.get("reason_codes")):
            gatekeeper_reuse_blockers[_friendly_reason_name(code)] += 1
        _count_sig_delta_fields(gatekeeper_sig_deltas, fields.get("sig_delta"))
        parsed_action_age = _safe_float(fields.get("action_age_sec"))
        if parsed_action_age is not None:
            gatekeeper_action_ages.append(parsed_action_age)
        parsed_allow_age = _safe_float(fields.get("allow_entry_age_sec"))
        if parsed_allow_age is not None:
            gatekeeper_allow_ages.append(parsed_allow_age)

    for row in latency_block_events:
        fields = row.get("fields") or {}
        latency_reason_counts[str(fields.get("reason") or "-")] += 1
        _count_csv_values(latency_danger_reason_counts, fields.get("latency_danger_reasons"))
        if str(fields.get("quote_stale") or "").strip().lower() in {"false", "0", "no"}:
            quote_fresh_latency_blocks += 1

    for row in latency_pass_events:
        fields = row.get("fields") or {}
        if str(fields.get("quote_stale") or "").strip().lower() in {"false", "0", "no"}:
            quote_fresh_latency_passes += 1

    for row in fill_events:
        fields = row.get("fields") or {}
        fill_quality = str(fields.get("fill_quality") or "UNKNOWN").strip().upper() or "UNKNOWN"
        fill_quality_counts[fill_quality] += 1

    metrics = {
        "ai_confirmed_events": len(ai_confirmed_events),
        "entry_armed_events": len(entry_armed_events),
        "budget_pass_events": len(budget_pass_events),
        "order_bundle_submitted_events": len(submitted_events),
        "budget_pass_to_submitted_rate": _ratio(len(submitted_events), len(budget_pass_events)),
        "latency_block_events": len(latency_block_events),
        "latency_pass_events": len(latency_pass_events),
        "latency_state_danger_events": int(latency_reason_counts.get("latency_state_danger", 0)),
        "quote_fresh_latency_blocks": quote_fresh_latency_blocks,
        "quote_fresh_latency_passes": quote_fresh_latency_passes,
        "quote_fresh_latency_pass_rate": _ratio(
            quote_fresh_latency_passes,
            quote_fresh_latency_passes + quote_fresh_latency_blocks,
        ),
        "gatekeeper_decisions": len(gatekeeper_decisions),
        "gatekeeper_fast_reuse_stage_events": len(gatekeeper_fast_reuse_events),
        "gatekeeper_fast_reuse_ratio": _ratio(
            gatekeeper_cache_modes.get("fast_reuse", 0),
            len(gatekeeper_decisions),
        ),
        "gatekeeper_eval_ms_p95": _percentile(gatekeeper_eval_ms, 95),
        "gatekeeper_model_call_ms_p95": _percentile(gatekeeper_model_call_ms, 95),
        "gatekeeper_total_internal_ms_p95": _percentile(gatekeeper_total_internal_ms, 95),
        "gatekeeper_bypass_evaluation_samples": len(gatekeeper_bypass_events),
        "gatekeeper_action_age_p95": _percentile(gatekeeper_action_ages, 95),
        "gatekeeper_allow_entry_age_p95": _percentile(gatekeeper_allow_ages, 95),
        "full_fill_events": int(fill_quality_counts.get("FULL_FILL", 0)),
        "partial_fill_events": int(fill_quality_counts.get("PARTIAL_FILL", 0)),
    }

    smoke_status = (
        "observed"
        if metrics["gatekeeper_decisions"] > 0
        or metrics["gatekeeper_fast_reuse_stage_events"] > 0
        or metrics["gatekeeper_bypass_evaluation_samples"] > 0
        else "missing"
    )
    result_label = str(label or manifest.get("slot_label") or bundle_dir.name).strip() or "offline_review"
    return {
        "target_date": resolved_target_date,
        "label": result_label,
        "bundle_dir": str(bundle_dir),
        "pipeline_events_path": str(pipeline_path),
        "since_time": since_time,
        "until_time": resolved_until,
        "metrics": metrics,
        "breakdowns": {
            "latency_reason_breakdown": [
                {"label": key, "count": value}
                for key, value in latency_reason_counts.most_common()
            ],
            "latency_danger_reason_breakdown": [
                {"label": key, "count": value}
                for key, value in latency_danger_reason_counts.most_common()
            ],
            "gatekeeper_reuse_blockers": [
                {"label": key, "count": value}
                for key, value in gatekeeper_reuse_blockers.most_common()
            ],
            "gatekeeper_sig_deltas": [
                {"label": key, "count": value}
                for key, value in gatekeeper_sig_deltas.most_common()
            ],
        },
        "judgment": {
            "smoke_status": smoke_status,
            "directional_ready": bool(
                metrics["budget_pass_events"] >= 30 or metrics["gatekeeper_decisions"] >= 10
            ),
            "why": (
                "raw pipeline_events 기반 재집계다. gatekeeper_fast_reuse 보조 진단과 함께 "
                "submitted/full/partial, latency_block, latency_state_danger, other_danger 분해를 본다."
            ),
        },
        "manifest": manifest,
    }


def _render_markdown(summary: dict[str, Any]) -> str:
    metrics = summary.get("metrics") or {}
    breakdowns = summary.get("breakdowns") or {}

    def _top_lines(rows: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
        lines: list[str] = []
        for row in rows[:limit]:
            lines.append(f"- {row.get('label')}: {row.get('count')}")
        return lines or ["- -"]

    lines = [
        "# Entry Latency Offline Summary",
        "",
        f"- target_date: `{summary.get('target_date')}`",
        f"- label: `{summary.get('label')}`",
        f"- since: `{summary.get('since_time') or '-'}`",
        f"- until: `{summary.get('until_time') or '-'}`",
        f"- smoke_status: `{(summary.get('judgment') or {}).get('smoke_status', '-')}`",
        f"- directional_ready: `{(summary.get('judgment') or {}).get('directional_ready', False)}`",
        "",
        "## Metrics",
        f"- ai_confirmed_events: `{metrics.get('ai_confirmed_events', 0)}`",
        f"- entry_armed_events: `{metrics.get('entry_armed_events', 0)}`",
        f"- budget_pass_events: `{metrics.get('budget_pass_events', 0)}`",
        f"- order_bundle_submitted_events: `{metrics.get('order_bundle_submitted_events', 0)}`",
        f"- budget_pass_to_submitted_rate: `{metrics.get('budget_pass_to_submitted_rate', 0.0)}%`",
        f"- latency_block_events: `{metrics.get('latency_block_events', 0)}`",
        f"- latency_state_danger_events: `{metrics.get('latency_state_danger_events', 0)}`",
        f"- quote_fresh_latency_pass_rate: `{metrics.get('quote_fresh_latency_pass_rate', 0.0)}%`",
        f"- gatekeeper_decisions: `{metrics.get('gatekeeper_decisions', 0)}`",
        f"- gatekeeper_fast_reuse_stage_events: `{metrics.get('gatekeeper_fast_reuse_stage_events', 0)}`",
        f"- gatekeeper_fast_reuse_ratio: `{metrics.get('gatekeeper_fast_reuse_ratio', 0.0)}%`",
        f"- gatekeeper_eval_ms_p95: `{metrics.get('gatekeeper_eval_ms_p95', 0.0)}ms`",
        f"- full_fill_events: `{metrics.get('full_fill_events', 0)}`",
        f"- partial_fill_events: `{metrics.get('partial_fill_events', 0)}`",
        "",
        "## Latency Reasons",
        *_top_lines(breakdowns.get("latency_reason_breakdown") or []),
        "",
        "## Danger Reasons",
        *_top_lines(breakdowns.get("latency_danger_reason_breakdown") or []),
        "",
        "## Reuse Blockers",
        *_top_lines(breakdowns.get("gatekeeper_reuse_blockers") or []),
        "",
        "## Sig Deltas",
        *_top_lines(breakdowns.get("gatekeeper_sig_deltas") or []),
        "",
    ]
    return "\n".join(lines) + "\n"


def write_summary(summary: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    label = str(summary.get("label") or "offline_review").strip().replace(" ", "_")
    json_path = output_dir / f"gatekeeper_fast_reuse_summary_{label}.json"
    md_path = output_dir / f"gatekeeper_fast_reuse_summary_{label}.md"
    generic_json_path = output_dir / f"entry_latency_offline_summary_{label}.json"
    generic_md_path = output_dir / f"entry_latency_offline_summary_{label}.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    generic_json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    generic_md_path.write_text(_render_markdown(summary), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "generic_json": str(generic_json_path),
        "generic_markdown": str(generic_md_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a downloaded entry latency offline bundle.")
    parser.add_argument("--bundle-dir", required=True, help="Path to the exported bundle directory.")
    parser.add_argument("--target-date", default=None, help="Target date override.")
    parser.add_argument("--since", dest="since_time", default="09:00:00", help="Since time HH:MM[:SS].")
    parser.add_argument("--until", dest="until_time", default=None, help="Until time HH:MM[:SS].")
    parser.add_argument("--label", default=None, help="Optional result label override.")
    parser.add_argument("--output-dir", default=None, help="Result output directory. Defaults to bundle_dir/results.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    bundle_dir = Path(args.bundle_dir)
    summary = build_summary(
        bundle_dir=bundle_dir,
        target_date=args.target_date,
        since_time=args.since_time,
        until_time=args.until_time,
        label=args.label,
    )
    output_dir = Path(args.output_dir) if args.output_dir else bundle_dir / "results"
    output_paths = write_summary(summary, output_dir)
    print(
        json.dumps(
            {
                "summary": summary,
                "output_paths": output_paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
