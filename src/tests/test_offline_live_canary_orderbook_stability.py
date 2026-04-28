import json
from datetime import time

from analysis.offline_live_canary_bundle.local_canary_analysis_runtime import build_entry_summary, run_analysis


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
        _event(
            "order_bundle_submitted",
            1,
            {
                "entry_price_guard": "latency_danger_override_defensive",
                "entry_price_defensive_ticks": "3",
                "order_price": "9990",
                "counterfactual_order_price_1tick": "10010",
            },
        ),
        _event(
            "latency_block",
            1,
            {
                "reason": "latency_state_danger",
                "latency_state": "DANGER",
            },
        ),
        _event(
            "full_fill",
            1,
            {
                "fill_quality": "FULL",
                "fill_price": "10000",
                "status": "COMPLETED",
                "profit_rate": "0.42",
            },
            pipeline="HOLDING_PIPELINE",
        ),
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

    price_guard = summary["latency_entry_price_guard"]
    assert price_guard["submitted_guard_breakdown"] == {"latency_danger_override_defensive": 1}
    assert price_guard["three_tick_guard"]["submitted_count"] == 1
    assert price_guard["three_tick_guard"]["full_fill_count"] == 1
    assert price_guard["three_tick_guard"]["fill_rate"] == 100.0
    assert price_guard["three_tick_guard"]["avg_realized_slippage_krw"] == 10.0
    assert price_guard["three_tick_guard"]["avg_realized_slippage_bps"] == 10.01001
    assert price_guard["three_tick_guard"]["completed_valid_profit_avg"] == 0.42


def test_run_analysis_supports_output_dir_and_bundle_metadata(tmp_path):
    bundle_dir = tmp_path / "bundle"
    events_dir = bundle_dir / "data" / "pipeline_events"
    events_dir.mkdir(parents=True)
    (bundle_dir / "data" / "post_sell").mkdir(parents=True)
    (bundle_dir / "data" / "analytics").mkdir(parents=True)
    (bundle_dir / "data" / "analytics" / "shadow_diff_summary.json").write_text("{}", encoding="utf-8")
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(
            {
                "target_date": "2026-04-28",
                "generated_at": "2026-04-28T10:59:00",
                "evidence_cutoff": "11:00:00",
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event("budget_pass", 1),
        _event("orderbook_stability_observed", 1, {"unstable_quote_observed": "False", "unstable_reasons": "-"}),
    ]
    with (events_dir / "pipeline_events_2026-04-28.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    output_dir = tmp_path / "summary_only"
    combined = run_analysis(
        bundle_dir,
        since="09:00:00",
        until="10:00:00",
        cumulative_since=None,
        label="h1000",
        output_dir=output_dir,
    )

    entry_path = output_dir / "entry_quote_fresh_composite_summary_h1000.json"
    soft_stop_path = output_dir / "soft_stop_micro_grace_summary_h1000.json"
    assert entry_path.exists()
    assert soft_stop_path.exists()

    entry = json.loads(entry_path.read_text(encoding="utf-8"))
    assert entry["bundle_metadata"]["bundle_dir"] == str(bundle_dir)
    assert entry["bundle_metadata"]["manifest_generated_at"] == "2026-04-28T10:59:00"
    assert entry["bundle_metadata"]["pipeline_event_rows_loaded"] == 2
    assert combined["bundle_dir"] == str(bundle_dir)
