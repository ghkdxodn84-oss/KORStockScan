"""CLI wrapper for saving monitor snapshots without cron-unfriendly inline code."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from datetime import datetime
from pathlib import Path

from src.engine.log_archive_service import save_monitor_snapshots_for_date_with_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save monitor snapshots for a target date.")
    parser.add_argument(
        "--date",
        dest="target_date",
        help="Target date in YYYY-MM-DD format. Defaults to local today.",
    )
    parser.add_argument(
        "--profile",
        choices=("full", "intraday_light"),
        default=os.getenv("MONITOR_SNAPSHOT_PROFILE", "full"),
        help="Snapshot build profile. default=full",
    )
    parser.add_argument(
        "--io-delay-sec",
        dest="io_delay_sec",
        type=float,
        default=float(os.getenv("MONITOR_SNAPSHOT_IO_DELAY_SEC", "0")),
        help="Delay seconds between snapshot stages to reduce read/write burst.",
    )
    parser.add_argument(
        "--skip-server-comparison",
        action="store_true",
        default=os.getenv("MONITOR_SNAPSHOT_SKIP_SERVER_COMPARISON", "0") == "1",
        help="Skip remote server comparison artifact generation.",
    )
    parser.add_argument(
        "--lock-file",
        dest="lock_file",
        default=os.getenv("MONITOR_SNAPSHOT_LOCK_FILE", "tmp/run_monitor_snapshot.lock"),
        help="Process lock file path to prevent concurrent snapshot jobs.",
    )
    parser.add_argument(
        "--skip-lock",
        action="store_true",
        help="Skip inner process lock. Use only when an outer wrapper already holds the lock.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_date = args.target_date or datetime.now().strftime("%Y-%m-%d")
    lock_path = Path(args.lock_file)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = None
    if not args.skip_lock:
        lock_handle = open(lock_path, "a+", encoding="utf-8")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(
                json.dumps(
                    {
                        "target_date": target_date,
                        "skipped": True,
                        "reason": "lock_busy",
                        "lock_file": str(lock_path),
                    },
                    ensure_ascii=False,
                )
            )
            lock_handle.close()
            return 0
    try:
        result = save_monitor_snapshots_for_date_with_profile(
            target_date,
            profile=args.profile,
            io_delay_sec=max(0.0, float(args.io_delay_sec)),
            include_server_comparison=not args.skip_server_comparison,
        )
    finally:
        if lock_handle is not None:
            lock_handle.close()
    print(
        json.dumps(
            {
                "target_date": target_date,
                "profile": args.profile,
                "io_delay_sec": max(0.0, float(args.io_delay_sec)),
                "skip_server_comparison": bool(args.skip_server_comparison),
                "skip_lock": bool(args.skip_lock),
                "snapshots": result,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
