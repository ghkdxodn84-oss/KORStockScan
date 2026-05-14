import sys
import types
import json

from src.engine import sniper_missed_entry_counterfactual as report_mod


def _make_candle(ts: str, open_p: int, high: int, low: int, close: int) -> dict:
    return {
        "체결시간": ts,
        "시가": open_p,
        "고가": high,
        "저가": low,
        "현재가": close,
    }


def _write_pipeline_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    path = tmp_path / "pipeline_events"
    path.mkdir(parents=True, exist_ok=True)
    with open(path / f"pipeline_events_{target_date}.jsonl", "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_build_missed_entry_counterfactual_report(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-09"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"action": "BUY", "ai_score": "92"},
                "emitted_at": "2026-04-09T10:00:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"ai_score": "92.0", "target_buy_price": "10000"},
                "emitted_at": "2026-04-09T10:00:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "budget_pass",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"qty": "10", "safe_budget": "100000"},
                "emitted_at": "2026-04-09T10:00:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "latency_block",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"decision": "REJECT_DANGER", "reason": "latency_state_danger"},
                "emitted_at": "2026-04-09T10:00:04",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "리퀴드로저",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"action": "BUY", "ai_score": "88"},
                "emitted_at": "2026-04-09T10:05:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "blocked_liquidity",
                "stock_name": "리퀴드로저",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"liquidity_value": "70000000", "min_liquidity": "350000000"},
                "emitted_at": "2026-04-09T10:05:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "제출완료",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {"action": "BUY", "ai_score": "85"},
                "emitted_at": "2026-04-09T10:10:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "제출완료",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {"target_buy_price": "30000"},
                "emitted_at": "2026-04-09T10:10:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "order_bundle_submitted",
                "stock_name": "제출완료",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {},
                "emitted_at": "2026-04-09T10:10:03",
                "emitted_date": target_date,
            },
        ],
    )

    candle_map = {
        "111111": [
            _make_candle("10:01:00", 10000, 10120, 9995, 10080),
            _make_candle("10:02:00", 10080, 10180, 10040, 10120),
            _make_candle("10:03:00", 10110, 10160, 10070, 10130),
            _make_candle("10:04:00", 10120, 10150, 10090, 10110),
            _make_candle("10:05:00", 10100, 10130, 10080, 10100),
            _make_candle("10:06:00", 10110, 10140, 10090, 10120),
            _make_candle("10:07:00", 10120, 10150, 10090, 10130),
            _make_candle("10:08:00", 10130, 10160, 10100, 10140),
            _make_candle("10:09:00", 10140, 10180, 10110, 10150),
            _make_candle("10:10:00", 10150, 10190, 10120, 10160),
        ],
        "222222": [
            _make_candle("10:06:00", 20000, 20050, 19880, 19920),
            _make_candle("10:07:00", 19920, 19960, 19780, 19820),
            _make_candle("10:08:00", 19820, 19880, 19720, 19760),
            _make_candle("10:09:00", 19760, 19820, 19680, 19720),
            _make_candle("10:10:00", 19720, 19780, 19640, 19680),
            _make_candle("10:11:00", 19680, 19710, 19620, 19660),
            _make_candle("10:12:00", 19660, 19690, 19600, 19640),
            _make_candle("10:13:00", 19640, 19680, 19580, 19620),
            _make_candle("10:14:00", 19620, 19660, 19560, 19600),
            _make_candle("10:15:00", 19600, 19630, 19540, 19580),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 2
    assert report["summary"]["evaluated_candidates"] == 2
    assert report["summary"]["outcome_counts"]["MISSED_WINNER"] == 1
    assert report["summary"]["outcome_counts"]["AVOIDED_LOSER"] == 1
    assert report["metrics"]["missed_winner_rate"] == 50.0
    assert report["metrics"]["avoided_loser_rate"] == 50.0
    blocker_metrics = report["metrics"]["blocker_outcome_metrics"]
    assert blocker_metrics["latency_block"]["missed_winner_rate"] == 100.0
    assert blocker_metrics["blocked_liquidity"]["avoided_loser_rate"] == 100.0
    assert blocker_metrics["latency_block"]["avg_close_10m_pct"] > 0
    assert report["buy_signal_universe"]["metrics"]["total_buy_judged_attempts"] == 3
    assert report["buy_signal_universe"]["metrics"]["entered_attempts"] == 1
    assert report["buy_signal_universe"]["metrics"]["missed_attempts"] == 2
    assert report["top_missed_winners"][0]["stock_code"] == "111111"
    assert report["top_missed_winners"][0]["counterfactual_qty"] == 114
    assert report["top_missed_winners"][0]["counterfactual_qty_source"] == "sim_virtual_budget_dynamic_formula"
    assert report["top_missed_winners"][0]["virtual_budget_krw"] == 10_000_000
    assert report["top_avoided_losers"][0]["stock_code"] == "222222"
    stages = {row["stage"] for row in report["reason_breakdown"]}
    assert "latency_block" in stages
    assert "blocked_liquidity" in stages
    tiers = {row["tier"] for row in report["buy_signal_universe"]["confidence_breakdown"]}
    assert "A" in tiers


def test_collects_all_missed_attempts_not_only_latest_per_stock(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-09"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"action": "BUY", "ai_score": "90"},
                "emitted_at": "2026-04-09T09:30:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"target_buy_price": "10000"},
                "emitted_at": "2026-04-09T09:30:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "latency_block",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"reason": "latency_state_danger"},
                "emitted_at": "2026-04-09T09:30:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"action": "BUY", "ai_score": "88"},
                "emitted_at": "2026-04-09T10:10:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"target_buy_price": "10100"},
                "emitted_at": "2026-04-09T10:10:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "order_bundle_submitted",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {},
                "emitted_at": "2026-04-09T10:10:03",
                "emitted_date": target_date,
            },
        ],
    )

    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: [
            _make_candle("09:31:00", 10000, 10050, 9950, 10020),
            _make_candle("09:32:00", 10020, 10080, 10000, 10050),
            _make_candle("09:33:00", 10050, 10100, 10020, 10060),
            _make_candle("09:34:00", 10060, 10090, 10030, 10040),
            _make_candle("09:35:00", 10040, 10070, 10010, 10030),
            _make_candle("09:36:00", 10030, 10060, 10000, 10020),
            _make_candle("09:37:00", 10020, 10040, 9990, 10010),
            _make_candle("09:38:00", 10010, 10030, 9980, 10000),
            _make_candle("09:39:00", 10000, 10020, 9970, 9990),
            _make_candle("09:40:00", 9990, 10010, 9960, 9980),
        ],
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 1
    assert report["rows"][0]["stock_code"] == "444444"
    assert report["rows"][0]["terminal_stage"] == "latency_block"
    assert report["buy_signal_universe"]["metrics"]["total_buy_judged_attempts"] == 2
    assert report["buy_signal_universe"]["metrics"]["entered_attempts"] == 1
