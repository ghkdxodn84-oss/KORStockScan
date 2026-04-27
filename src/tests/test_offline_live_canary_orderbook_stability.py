from datetime import time

from analysis.offline_live_canary_bundle.local_canary_analysis_runtime import build_entry_summary


def _event(stage, record_id, fields=None, pipeline="ENTRY_PIPELINE"):
    return {
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "record_id": record_id,
        "emitted_at": "2026-04-28T09:01:00",
        "emitted_date": "2026-04-28",
        "fields": fields or {},
    }


def test_entry_summary_includes_orderbook_stability_observation():
    events = [
        _event(
            "orderbook_stability_observed",
            1,
            {
                "unstable_quote_observed": "True",
                "unstable_reasons": "fr_10s,quote_age_p90",
            },
        ),
        _event("budget_pass", 1),
        _event("order_bundle_submitted", 1),
        _event(
            "latency_block",
            1,
            {
                "reason": "latency_state_danger",
                "latency_state": "DANGER",
            },
        ),
        _event("full_fill", 1, {"fill_quality": "FULL"}, pipeline="HOLDING_PIPELINE"),
    ]

    summary = build_entry_summary(
        events,
        since=time(9, 0, 0),
        until=time(9, 10, 0),
        label="h0900",
        shadow_diff_status="available",
    )

    stability = summary["orderbook_stability"]
    assert stability["orderbook_stability_observed_count"] == 1
    assert stability["unstable_quote_observed_count"] == 1
    assert stability["unstable_reason_breakdown"] == {"fr_10s": 1, "quote_age_p90": 1}
    assert stability["unstable_vs_submitted"]["submitted_count"] == 1
    assert stability["unstable_vs_fill"]["fill_count"] == 1
    assert stability["unstable_vs_latency_danger"]["latency_danger_count"] == 1
