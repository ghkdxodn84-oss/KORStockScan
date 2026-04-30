import json

from src.engine import backfill_threshold_cycle_events as mod


def test_backfill_threshold_cycle_events_streams_only_target_stages(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")

    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    raw_path.write_text(
        "\n".join(
            [
                json.dumps({"event_type": "pipeline_event", "stage": "budget_pass", "pipeline": "ENTRY_PIPELINE", "stock_name": "A", "stock_code": "111111", "fields": {"x": "1"}, "emitted_at": "2026-04-30T09:00:00", "emitted_date": "2026-04-30"}),
                json.dumps({"event_type": "pipeline_event", "stage": "sell_completed", "pipeline": "HOLDING_PIPELINE", "stock_name": "B", "stock_code": "222222", "fields": {"y": "2"}, "emitted_at": "2026-04-30T09:01:00", "emitted_date": "2026-04-30"}),
                json.dumps({"event_type": "pipeline_event", "stage": "bad_entry_block_observed", "pipeline": "HOLDING_PIPELINE", "stock_name": "C", "stock_code": "333333", "fields": {"z": "3"}, "emitted_at": "2026-04-30T09:02:00", "emitted_date": "2026-04-30"}),
            ]
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events("2026-04-30", overwrite=True)
    assert summary["written"] == 2

    compact_path = tmp_path / "threshold_cycle" / "threshold_events_2026-04-30.jsonl"
    rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["stage"] for row in rows] == ["budget_pass", "bad_entry_block_observed"]
