"""Export lightweight offline bundles for entry latency review."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


def _parse_time(target_date: str, raw: str | None) -> datetime | None:
    if not raw:
        return None
    value = str(raw).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            if fmt.startswith("%Y"):
                return datetime.strptime(value, fmt)
            return datetime.strptime(f"{target_date} {value}", f"%Y-%m-%d {fmt}")
        except Exception:
            continue
    return None


def _parse_event_dt(raw: str | None) -> datetime | None:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        return None


def _copy_if_exists(src: Path, dst: Path) -> str | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


def export_bundle(
    *,
    target_date: str,
    slot_label: str,
    evidence_cutoff: str,
    output_root: Path | None = None,
) -> dict[str, Any]:
    cutoff_dt = _parse_time(target_date, evidence_cutoff)
    if cutoff_dt is None:
        raise ValueError(f"invalid evidence_cutoff: {evidence_cutoff}")

    source_pipeline = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if not source_pipeline.exists():
        raise FileNotFoundError(f"missing pipeline events: {source_pipeline}")

    bundle_root = (output_root or Path("tmp") / "offline_gatekeeper_fast_reuse_exports") / target_date / slot_label
    bundle_root.mkdir(parents=True, exist_ok=True)

    bundle_pipeline = bundle_root / "data" / "pipeline_events" / source_pipeline.name
    bundle_pipeline.parent.mkdir(parents=True, exist_ok=True)

    total_lines = 0
    exported_lines = 0
    with source_pipeline.open("r", encoding="utf-8", errors="replace") as src, bundle_pipeline.open(
        "w",
        encoding="utf-8",
    ) as dst:
        for line in src:
            if not line.strip():
                continue
            total_lines += 1
            try:
                row = json.loads(line)
            except Exception:
                continue
            emitted_dt = _parse_event_dt(row.get("emitted_at"))
            if emitted_dt is None:
                continue
            if emitted_dt.date().isoformat() != target_date:
                continue
            if emitted_dt > cutoff_dt:
                continue
            dst.write(line if line.endswith("\n") else f"{line}\n")
            exported_lines += 1

    snapshot_dir = DATA_DIR / "report" / "monitor_snapshots"
    manifest_dir = snapshot_dir / "manifests"
    gatekeeper_dir = DATA_DIR / "gatekeeper"

    copied_files: dict[str, str] = {}
    copy_plan = {
        "performance_tuning": snapshot_dir / f"performance_tuning_{target_date}.json",
        "trade_review": snapshot_dir / f"trade_review_{target_date}.json",
        "wait6579_ev_cohort": snapshot_dir / f"wait6579_ev_cohort_{target_date}.json",
        f"monitor_snapshot_manifest_{target_date}_intraday_light.json": manifest_dir
        / f"monitor_snapshot_manifest_{target_date}_intraday_light.json",
        "gatekeeper_snapshots": gatekeeper_dir / f"gatekeeper_snapshots_{target_date}.jsonl",
    }
    for key, src in copy_plan.items():
        rel_parts = ["data", *src.relative_to(DATA_DIR).parts]
        if "monitor_snapshot_manifest_" in key:
            rel_parts = ["data", "report", "monitor_snapshots", "manifests", src.name]
        copied = _copy_if_exists(src, bundle_root.joinpath(*rel_parts))
        if copied:
            copied_files[key] = copied

    manifest = {
        "target_date": target_date,
        "slot_label": slot_label,
        "evidence_cutoff": evidence_cutoff,
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_pipeline_path": str(source_pipeline),
        "pipeline_event_lines_total": total_lines,
        "pipeline_event_lines_exported": exported_lines,
        "bundle_dir": str(bundle_root),
        "copied_files": copied_files,
        "recommended_local_command": (
            "analysis\\offline_gatekeeper_fast_reuse_bundle\\run_local_bundle_analysis.bat "
            f'--bundle-dir "{bundle_root}"'
        ),
    }
    manifest_path = bundle_root / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export an offline entry latency review bundle.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Create a local-review bundle from server data.")
    export_parser.add_argument("--target-date", required=True, help="Target trading date (YYYY-MM-DD).")
    export_parser.add_argument("--slot-label", required=True, help="Slot label, e.g. smoke_1000 or latency_1300.")
    export_parser.add_argument("--evidence-cutoff", required=True, help="Inclusive cutoff HH:MM[:SS].")
    export_parser.add_argument(
        "--output-root",
        default=None,
        help="Override export root. Defaults to tmp/offline_gatekeeper_fast_reuse_exports.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command != "export":
        raise ValueError(f"unsupported command: {args.command}")
    manifest = export_bundle(
        target_date=args.target_date,
        slot_label=args.slot_label,
        evidence_cutoff=args.evidence_cutoff,
        output_root=Path(args.output_root) if args.output_root else None,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0

