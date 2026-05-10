from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.model.common_v2 import DATA_DIR, MODEL_REGISTRY_DIR, resolve_bull_specialist_mode
from src.model.swing_bull_period_ai_review import write_review
from src.model.swing_retrain_diagnosis import write_diagnosis


ACTIVE_MODEL_FILES = [
    "hybrid_xgb_v2.pkl",
    "hybrid_lgbm_v2.pkl",
    "bull_xgb_v2.pkl",
    "bull_lgbm_v2.pkl",
    "stacking_meta_v2.pkl",
]
REQUIRED_NON_BULL_FILES = ["hybrid_xgb_v2.pkl", "hybrid_lgbm_v2.pkl", "stacking_meta_v2.pkl"]
REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_retrain"
REGISTRY_DIR = Path(MODEL_REGISTRY_DIR)
RUNS_DIR = REGISTRY_DIR / "runs"
PROMOTIONS_DIR = REGISTRY_DIR / "promotions"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _run_id(target_date: str) -> str:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"{target_date}_{stamp}"


def _run_command(args: list[str], *, env: dict[str, str], cwd: Path) -> dict[str, Any]:
    started = datetime.now().isoformat(timespec="seconds")
    proc = subprocess.run(args, cwd=str(cwd), env=env, text=True, capture_output=True)
    return {
        "args": args,
        "started_at": started,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def evaluate_bull_specialist_mode(
    enabled_metrics: dict[str, Any],
    disabled_metrics: dict[str, Any],
    *,
    sample_floor: int = 10,
) -> dict[str, Any]:
    enabled_sample = _safe_int(enabled_metrics.get("sample_count"), 0)
    disabled_sample = _safe_int(disabled_metrics.get("sample_count"), 0)
    if min(enabled_sample, disabled_sample) < sample_floor:
        return {
            "bull_specialist_mode": "hold_current",
            "reason": "insufficient_bull_forward_sample",
            "tradeoff_delta": 0.0,
        }

    enabled_avg = _safe_float(enabled_metrics.get("avg_net_pct"), 0.0)
    disabled_avg = _safe_float(disabled_metrics.get("avg_net_pct"), 0.0)
    enabled_p10 = _safe_float(enabled_metrics.get("downside_p10_pct"), 0.0)
    disabled_p10 = _safe_float(disabled_metrics.get("downside_p10_pct"), 0.0)
    enabled_selected = _safe_int(enabled_metrics.get("selected_count"), 0)
    disabled_selected = max(1, _safe_int(disabled_metrics.get("selected_count"), 0))
    selected_drop = (disabled_selected - enabled_selected) / disabled_selected
    tradeoff_delta = (
        (enabled_avg - disabled_avg) * 0.45
        + (enabled_p10 - disabled_p10) * 0.25
        - max(0.0, selected_drop) * 0.30
    )
    if (
        tradeoff_delta >= 0.05
        and enabled_avg - disabled_avg >= 0.10
        and enabled_p10 - disabled_p10 >= -0.30
        and selected_drop <= 0.30
    ):
        mode = "enabled"
        reason = "enabled_outperformed_disabled"
    elif enabled_avg < disabled_avg or enabled_p10 < disabled_p10 - 0.30:
        mode = "disabled"
        reason = "disabled_outperformed_or_safer"
    else:
        mode = "hold_current"
        reason = "no_clear_bull_specialist_edge"
    return {
        "bull_specialist_mode": mode,
        "reason": reason,
        "tradeoff_delta": round(tradeoff_delta, 4),
        "selected_drop_ratio": round(selected_drop, 4),
    }


def _summarize_backtest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "sample_count": 0}
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return {"available": False, "sample_count": 0, "error": str(exc)}
    if df.empty or "net_ret" not in df.columns:
        return {"available": True, "sample_count": 0}
    bull_df = df[df.get("bull_regime", 0) == 1] if "bull_regime" in df.columns else df
    sample = len(bull_df)
    net = bull_df["net_ret"].astype(float) * 100.0 if sample else pd.Series(dtype=float)
    return {
        "available": True,
        "sample_count": int(sample),
        "selected_count": int(len(df)),
        "avg_net_pct": float(net.mean()) if sample else 0.0,
        "downside_p10_pct": float(net.quantile(0.10)) if sample else 0.0,
        "win_rate": float((net > 0).mean()) if sample else 0.0,
    }


def candidate_tradeoff_score(metrics: dict[str, Any]) -> float:
    avg = max(-1.0, min(1.0, _safe_float(metrics.get("avg_net_pct"), 0.0) / 2.0))
    downside = max(0.0, min(1.0, (_safe_float(metrics.get("downside_p10_pct"), -4.0) + 4.0) / 4.0))
    win = max(0.0, min(1.0, _safe_float(metrics.get("win_rate"), 0.0)))
    participation = max(0.0, min(1.0, _safe_int(metrics.get("sample_count"), 0) / 40.0))
    return round(avg * 0.40 + downside * 0.20 + win * 0.15 + participation * 0.15 + 0.10, 4)


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _prepare_hold_current_bull_artifacts(run_dir: Path) -> None:
    for name in ("bull_xgb_v2.pkl", "bull_lgbm_v2.pkl"):
        _copy_if_exists(Path(DATA_DIR) / name, run_dir / name)


def _staging_env(run_dir: Path, bull_mode: str, bull_review: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["KORSTOCKSCAN_SWING_MODEL_OUTPUT_DIR"] = str(run_dir)
    env["KORSTOCKSCAN_SWING_BULL_SPECIALIST_MODE"] = bull_mode
    decision = bull_review.get("decision") if isinstance(bull_review.get("decision"), dict) else {}
    if decision.get("bull_base_start"):
        env["KORSTOCKSCAN_SWING_BULL_BASE_START"] = str(decision["bull_base_start"])
    if decision.get("bull_base_end"):
        env["KORSTOCKSCAN_SWING_BULL_BASE_END"] = str(decision["bull_base_end"])
    return env


def _train_candidate(run_dir: Path, bull_mode: str, bull_review: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    env = _staging_env(run_dir, bull_mode, bull_review)
    commands = [
        [sys.executable, "-m", "src.model.train_hybrid_xgb_v2"],
        [sys.executable, "-m", "src.model.train_hybrid_lgbm_v2"],
    ]
    if bull_mode == "enabled":
        commands.append(
            [
                sys.executable,
                "-m",
                "src.model.train_bull_specialists_v2",
                "--bull-base-start",
                str((bull_review.get("decision") or {}).get("bull_base_start") or ""),
                "--bull-base-end",
                str((bull_review.get("decision") or {}).get("bull_base_end") or ""),
            ]
        )
    elif bull_mode == "hold_current":
        _prepare_hold_current_bull_artifacts(run_dir)
    commands.extend(
        [
            [sys.executable, "-m", "src.model.train_meta_model_v2", "--bull-mode", bull_mode],
            [sys.executable, "-m", "src.model.backtest_v2"],
        ]
    )
    results: list[dict[str, Any]] = []
    for command in commands:
        result = _run_command(command, env=env, cwd=root)
        results.append(result)
        if result["returncode"] != 0:
            break
    return results


def _candidate_files_for_mode(mode: str) -> list[str]:
    if mode == "disabled":
        return REQUIRED_NON_BULL_FILES
    return ACTIVE_MODEL_FILES


def _validate_candidate_files(run_dir: Path, mode: str) -> list[str]:
    missing = []
    for name in _candidate_files_for_mode(mode):
        if not (run_dir / name).exists():
            missing.append(name)
    return missing


def _backup_active_models(backup_dir: Path) -> list[str]:
    copied = []
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in ACTIVE_MODEL_FILES:
        src = Path(DATA_DIR) / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
            copied.append(name)
    return copied


def _promote_candidate(run_dir: Path, backup_dir: Path, mode: str) -> dict[str, Any]:
    copied = _backup_active_models(backup_dir)
    for name in _candidate_files_for_mode(mode):
        shutil.copy2(run_dir / name, Path(DATA_DIR) / name)
    if mode == "disabled":
        for name in ("bull_xgb_v2.pkl", "bull_lgbm_v2.pkl"):
            active = Path(DATA_DIR) / name
            if active.exists():
                active.unlink()
    return {"backup_files": copied, "promoted_files": _candidate_files_for_mode(mode)}


def _rollback_active_models(backup_dir: Path) -> list[str]:
    restored = []
    for name in ACTIVE_MODEL_FILES:
        src = backup_dir / name
        dst = Path(DATA_DIR) / name
        if src.exists():
            shutil.copy2(src, dst)
            restored.append(name)
    return restored


def _write_current_manifest(run_id: str, target_date: str, run_dir: Path, mode: str, metrics: dict[str, Any]) -> Path:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "target_date": target_date,
        "promoted_at": datetime.now().isoformat(timespec="seconds"),
        "bull_specialist_mode": mode,
        "artifact_dir": str(run_dir),
        "runtime_change": "model_artifact_promote_only",
        "swing_live_order_dry_run_required": True,
        "metrics": metrics,
    }
    path = REGISTRY_DIR / "current.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _smoke_after_promote(mode: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["KORSTOCKSCAN_SWING_BULL_SPECIALIST_MODE"] = mode
    return _run_command([sys.executable, "-m", "src.model.recommend_daily_v2", "--bull-mode", mode], env=env, cwd=root)


def pipeline_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_model_retrain_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Swing Model Retrain {report.get('target_date')}",
            "",
            f"- status: `{report.get('status')}`",
            f"- run_id: `{report.get('run_id')}`",
            f"- bull_specialist_mode: `{report.get('bull_specialist_mode')}`",
            f"- promoted: `{report.get('promoted')}`",
            f"- rollback_executed: `{report.get('rollback_executed')}`",
            "- swing_live_order_dry_run_required: `true`",
            "",
        ]
    )


def run_pipeline(
    target_date: str | None = None,
    *,
    auto_promote: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    target = target_date or date.today().isoformat()
    diagnosis = write_diagnosis(target, force=force)
    bull_review = write_review(target)
    initial_mode = resolve_bull_specialist_mode((bull_review.get("decision") or {}).get("bull_specialist_mode"))
    run_id = _run_id(target)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    status = "skipped"
    command_results: list[dict[str, Any]] = []
    promoted = False
    rollback_executed = False
    promotion: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    mode_decision = {"bull_specialist_mode": initial_mode, "reason": "review_decision"}

    if bool(diagnosis.get("retrain_required")):
        command_results = _train_candidate(run_dir, initial_mode, bull_review)
        failed = [item for item in command_results if item.get("returncode") != 0]
        missing = _validate_candidate_files(run_dir, initial_mode)
        metrics = _summarize_backtest(run_dir / "backtest_trades_v2.csv")
        if failed:
            status = "failed"
            promotion["blocked_reason"] = "training_command_failed"
        elif missing:
            status = "failed"
            promotion["blocked_reason"] = f"candidate_artifact_missing:{','.join(missing)}"
        else:
            metrics["tradeoff_score"] = candidate_tradeoff_score(metrics)
            min_score = _safe_float(os.getenv("KORSTOCKSCAN_SWING_RETRAIN_MIN_SCORE"), 0.72)
            hard_floor_passed = _safe_int(metrics.get("sample_count"), 0) >= 40
            avg_ok = _safe_float(metrics.get("avg_net_pct"), 0.0) >= 0.10
            score_ok = _safe_float(metrics.get("tradeoff_score"), 0.0) >= min_score
            if not hard_floor_passed:
                status = "hold_sample"
                promotion["blocked_reason"] = "sample_floor_not_met"
            elif not avg_ok:
                status = "rejected"
                promotion["blocked_reason"] = "avg_net_below_floor"
            elif not score_ok:
                status = "rejected"
                promotion["blocked_reason"] = "tradeoff_score_below_floor"
                promotion["min_tradeoff_score"] = min_score
            elif auto_promote:
                backup_dir = PROMOTIONS_DIR / f"{run_id}_backup"
                promotion = _promote_candidate(run_dir, backup_dir, initial_mode)
                smoke = _smoke_after_promote(initial_mode)
                promotion["smoke"] = smoke
                if smoke.get("returncode") == 0:
                    promoted = True
                    status = "promoted"
                    current_path = _write_current_manifest(run_id, target, run_dir, initial_mode, metrics)
                    promotion["current_manifest"] = str(current_path)
                else:
                    rollback_executed = True
                    promotion["rollback_files"] = _rollback_active_models(backup_dir)
                    status = "rolled_back"
            else:
                status = "passed_not_promoted"
                promotion["blocked_reason"] = "auto_promote_false"

    report = {
        "schema_version": 1,
        "report_type": "swing_model_retrain",
        "target_date": target,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "status": status,
        "runtime_change": "model_artifact_promote_only" if promoted else False,
        "swing_live_order_dry_run_required": True,
        "diagnosis": diagnosis,
        "bull_period_review": bull_review,
        "bull_specialist_mode": initial_mode,
        "bull_mode_decision": mode_decision,
        "run_dir": str(run_dir),
        "command_results": command_results,
        "metrics": metrics,
        "auto_promote": auto_promote,
        "promoted": promoted,
        "rollback_executed": rollback_executed,
        "promotion": promotion,
    }
    json_path, md_path = pipeline_paths(target)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    PROMOTIONS_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    promotion_path = PROMOTIONS_DIR / f"promotion_{target}.json"
    promotion_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run swing v2 retrain pipeline.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--auto-promote", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    report = run_pipeline(args.target_date, auto_promote=args.auto_promote, force=args.force)
    return 0 if report.get("status") not in {"failed", "rolled_back"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
