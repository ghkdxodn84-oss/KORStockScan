"""Summaries for latency-aware entry behavior from existing log files."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.utils.constants import LOGS_DIR


_DECISION_RE = re.compile(
    r"\[LATENCY_ENTRY_DECISION\].*?mode=(?P<mode>\w+).*?decision=(?P<decision>\w+).*?"
    r"latency=(?P<latency>\w+)"
)
_SUBMISSION_RE = re.compile(
    r"\[ENTRY_SUBMISSION_BUNDLE\].*?mode=(?P<mode>\w+).*?requested_qty=(?P<qty>\d+).*?legs=(?P<legs>\d+)"
)
_ORDER_SENT_RE = re.compile(
    r"\[LATENCY_ENTRY_ORDER_SENT\].*?tag=(?P<tag>[\w_]+).*?type=(?P<order_type>\w+).*?tif=(?P<tif>\w+)"
)
_FILL_RE = re.compile(
    r"\[ENTRY_FILL\].*?tag=(?P<tag>[\w_]+).*?fill_qty=(?P<fill_qty>\d+).*?filled=(?P<filled>\d+)/(?P<requested>\d+)"
)
_BUNDLE_FILLED_RE = re.compile(
    r"\[ENTRY_BUNDLE_FILLED\].*?mode=(?P<mode>\w+).*?filled_qty=(?P<filled>\d+)/(?P<requested>\d+)"
)
_TIF_PROMOTION_RE = re.compile(r"\[ENTRY_TIF_MAP\]")


@dataclass
class EntryMetricsSummary:
    """Compact operating summary for the current trading day."""

    date: str
    latency_counts: Counter = field(default_factory=Counter)
    decision_counts: Counter = field(default_factory=Counter)
    mode_counts: Counter = field(default_factory=Counter)
    submission_mode_counts: Counter = field(default_factory=Counter)
    order_tag_counts: Counter = field(default_factory=Counter)
    order_tif_counts: Counter = field(default_factory=Counter)
    order_type_counts: Counter = field(default_factory=Counter)
    fill_tag_counts: Counter = field(default_factory=Counter)
    bundle_filled_mode_counts: Counter = field(default_factory=Counter)
    tif_promotions: int = 0

    @property
    def fallback_activation_count(self) -> int:
        return int(self.submission_mode_counts.get("fallback", 0))

    @property
    def normal_activation_count(self) -> int:
        return int(self.submission_mode_counts.get("normal", 0))


def _iter_today_lines(log_path: Path, *, target_date: str) -> list[str]:
    if not log_path.exists():
        return []
    lines: list[str] = []
    with open(log_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            if f"[{target_date}" not in raw_line:
                continue
            lines.append(raw_line.strip())
    return lines


def summarize_today_entry_metrics(now: datetime | None = None) -> EntryMetricsSummary:
    current = now or datetime.now()
    target_date = current.strftime("%Y-%m-%d")
    summary = EntryMetricsSummary(date=target_date)

    decision_lines = _iter_today_lines(LOGS_DIR / "sniper_state_handlers_info.log", target_date=target_date)
    fill_lines = _iter_today_lines(LOGS_DIR / "sniper_execution_receipts_info.log", target_date=target_date)
    tif_lines = _iter_today_lines(LOGS_DIR / "kiwoom_orders_info.log", target_date=target_date)

    for line in decision_lines:
        if match := _DECISION_RE.search(line):
            summary.mode_counts.update([match.group("mode").lower()])
            summary.decision_counts.update([match.group("decision").upper()])
            summary.latency_counts.update([match.group("latency").upper()])
        if match := _SUBMISSION_RE.search(line):
            summary.submission_mode_counts.update([match.group("mode").lower()])
        if match := _ORDER_SENT_RE.search(line):
            summary.order_tag_counts.update([match.group("tag").lower()])
            summary.order_tif_counts.update([match.group("tif").upper()])
            summary.order_type_counts.update([match.group("order_type").upper()])

    for line in fill_lines:
        if match := _FILL_RE.search(line):
            summary.fill_tag_counts.update([match.group("tag").lower()])
        if match := _BUNDLE_FILLED_RE.search(line):
            summary.bundle_filled_mode_counts.update([match.group("mode").lower()])

    for line in tif_lines:
        if _TIF_PROMOTION_RE.search(line):
            summary.tif_promotions += 1

    return summary


def format_entry_metrics_summary(summary: EntryMetricsSummary) -> str:
    """Render a Telegram-friendly report for admins."""

    safe = summary.latency_counts.get("SAFE", 0)
    caution = summary.latency_counts.get("CAUTION", 0)
    danger = summary.latency_counts.get("DANGER", 0)
    normal = summary.normal_activation_count
    fallback = summary.fallback_activation_count
    scout_sent = summary.order_tag_counts.get("fallback_scout", 0)
    main_sent = summary.order_tag_counts.get("fallback_main", 0)
    scout_fill = summary.fill_tag_counts.get("fallback_scout", 0)
    main_fill = summary.fill_tag_counts.get("fallback_main", 0)
    fallback_filled = summary.bundle_filled_mode_counts.get("fallback", 0)

    return (
        f"📊 진입 지표 요약 ({summary.date})\n"
        f"- latency: SAFE {safe} / CAUTION {caution} / DANGER {danger}\n"
        f"- decision: normal {normal} / fallback {fallback}\n"
        f"- fallback sent: scout {scout_sent} / main {main_sent}\n"
        f"- fallback fill: scout {scout_fill} / main {main_fill} / bundle_done {fallback_filled}\n"
        f"- order types: {dict(summary.order_type_counts)}\n"
        f"- tif usage: {dict(summary.order_tif_counts)}\n"
        f"- IOC->16 promotions: {summary.tif_promotions}"
    )
