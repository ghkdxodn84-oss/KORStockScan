from datetime import datetime

from src.engine import market_panic_breadth_collector as collector


def test_parse_kiwoom_industry_rows_from_nested_response():
    payload = {
        "all_inds_index": [
            {"inds_cd": "001", "inds_nm": "종합(KOSPI)", "cur_prc": "2,700.10", "flu_rt": "-1.45"},
            {"inds_cd": "101", "inds_nm": "코스닥", "cur_prc": "850.00", "flu_rt": "-2.10"},
            {"inds_cd": "201", "inds_nm": "반도체", "cur_prc": "1,000", "flu_rt": "-2.40"},
        ]
    }

    rows = collector.parse_kiwoom_industry_rows(payload)

    assert len(rows) == 3
    assert rows[0]["code"] == "001"
    assert rows[0]["change_pct"] == -1.45
    assert rows[2]["name"] == "반도체"


def test_summarize_breadth_sets_report_only_risk_off_advisory():
    rows = [
        {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
        {"code": "101", "name": "코스닥", "change_pct": -2.1},
        {"code": "201", "name": "반도체", "change_pct": -2.4},
        {"code": "202", "name": "IT", "change_pct": -1.2},
        {"code": "203", "name": "바이오", "change_pct": -2.2},
        {"code": "204", "name": "운송", "change_pct": 0.2},
    ]

    summary = collector.summarize_breadth(
        rows,
        industry_down_ratio_floor_pct=50.0,
        severe_down_ratio_floor_pct=40.0,
    )

    assert summary["risk_off_advisory"] is True
    assert summary["decision_authority"] == "source_quality_only"
    assert "order_submit" in summary["forbidden_uses"]
    assert summary["industry_breadth"]["down_count"] == 3


def test_build_market_panic_breadth_report_from_injected_rows():
    report = collector.build_market_panic_breadth_report(
        "2026-05-15",
        as_of=datetime.fromisoformat("2026-05-15T11:30:00"),
        rows=[
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
            {"code": "201", "name": "반도체", "change_pct": -2.4},
            {"code": "202", "name": "IT", "change_pct": -2.1},
        ],
    )

    assert report["report_type"] == "market_panic_breadth"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["source_quality"]["status"] == "ok"
