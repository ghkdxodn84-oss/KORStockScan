"""IPO listing day intraday dashboard."""

from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template_string, request

from src.utils import kiwoom_utils


ipo_intraday_bp = Blueprint("ipo_intraday", __name__)


KIND_IPO_URLS = (
    "https://kind.krx.co.kr/listinvstg/listingcompany.do?method=searchListingTypeMain",
    "https://kind.krx.co.kr/listinvstg/listingcompany.do?method=searchListingTypeSub",
)
IPO38_URL = "http://www.38.co.kr/html/fund/index.htm?o=k"


def _to_int(value: Any) -> int:
    if value in (None, "", "-"):
        return 0
    try:
        return int(float(str(value).replace(",", "").replace("+", "").strip()))
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    if value in (None, "", "-"):
        return 0.0
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"(20\d{2})[.\-/년\s]*(\d{1,2})[.\-/월\s]*(\d{1,2})", text)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def _normalize_code(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"([A-Z0-9]{6})", text.upper())
    return match.group(1) if match else ""


def _find_col(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    normalized = [(col, re.sub(r"\s+", "", str(col))) for col in columns]
    for raw, compact in normalized:
        if any(key in compact for key in candidates):
            return raw
    return None


@lru_cache(maxsize=4)
def _load_kind_ipo_rows_cached(cache_day: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for url in KIND_IPO_URLS:
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as res:
                html = res.read()
            tables = pd.read_html(html)
        except Exception:
            continue

        for table in tables:
            if table is None or table.empty:
                continue
            table.columns = [str(col) for col in table.columns]
            columns = list(table.columns)
            name_col = _find_col(columns, ("회사명", "종목명", "기업명"))
            date_col = _find_col(columns, ("상장일", "상장예정일", "신규상장일"))
            code_col = _find_col(columns, ("종목코드", "표준코드", "단축코드"))
            offer_col = _find_col(columns, ("공모가", "확정공모가", "발행가"))
            market_col = _find_col(columns, ("시장구분", "시장"))
            if not name_col or not date_col:
                continue
            for _, row in table.iterrows():
                listing_date = _parse_date(row.get(date_col))
                name = str(row.get(name_col) or "").strip()
                if not listing_date or not name or name.lower() == "nan":
                    continue
                rows.append(
                    {
                        "name": name,
                        "code": _normalize_code(row.get(code_col)) if code_col else "",
                        "listing_date": listing_date.isoformat(),
                        "offer_price": _to_int(row.get(offer_col)) if offer_col else 0,
                        "market": str(row.get(market_col) or "").strip() if market_col else "",
                        "source": "KIND",
                    }
                )

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in rows:
        key = (item.get("code") or item.get("name") or "", item.get("listing_date") or "")
        if key[0] and key[1]:
            dedup[key] = item
    return sorted(dedup.values(), key=lambda item: item["listing_date"])


def _load_ipo_rows() -> tuple[list[dict[str, Any]], str]:
    fdr_rows = _load_fdr_listing_rows()
    kind_rows = _load_kind_ipo_rows_cached(datetime.now().strftime("%Y-%m-%d"))
    ipo38_rows = _load_38_ipo_rows(datetime.now().strftime("%Y-%m-%d"))
    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for item in fdr_rows + kind_rows + ipo38_rows:
        key = (str(item.get("code") or item.get("name") or ""), str(item.get("listing_date") or ""))
        if key[0] and key[1]:
            existing = rows_by_key.get(key, {})
            rows_by_key[key] = {**existing, **{k: v for k, v in item.items() if v not in (None, "", 0)}}
    rows = sorted(rows_by_key.values(), key=lambda item: item["listing_date"])
    sources = []
    if fdr_rows:
        sources.append("FinanceDataReader KRX-DESC")
    if kind_rows:
        sources.append("KIND 공개 표")
    if ipo38_rows:
        sources.append("38커뮤니케이션")
    if sources:
        source = " + ".join(sources)
    elif fdr_rows:
        source = "FinanceDataReader KRX-DESC(KIND 403 fallback)"
    elif kind_rows:
        source = "KIND 공개 표"
    else:
        source = "일정 자동조회 실패(KIND 403 또는 외부 표 변경)"
    return rows, source


@lru_cache(maxsize=4)
def _load_38_ipo_rows(cache_day: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            IPO38_URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            },
            timeout=6,
        )
        response.encoding = "euc-kr"
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"summary": "공모주 청약일정"})
    if table is None:
        tables = soup.find_all("table")
        table = next((item for item in tables if "공모주" in item.get_text(" ", strip=True)), None)
    if table is None:
        return []

    rows: list[dict[str, Any]] = []
    header_map: dict[str, int] = {}
    for row in table.find_all("tr"):
        header_cells = [col.get_text(" ", strip=True) for col in row.find_all(["th", "td"])]
        compact_headers = [re.sub(r"\s+", "", value) for value in header_cells]
        if "종목명" in compact_headers and ("확정공모가" in compact_headers or "희망공모가" in compact_headers):
            header_map = {name: idx for idx, name in enumerate(compact_headers)}
            continue

        cols = [col.get_text(" ", strip=True) for col in row.find_all("td")]
        if len(cols) <= 5:
            continue
        name_idx = header_map.get("종목명", 0)
        schedule_idx = header_map.get("공모주일정", 1)
        final_idx = header_map.get("확정공모가", 2)
        band_idx = header_map.get("희망공모가", 3)
        competition_idx = header_map.get("청약경쟁률", 4)
        underwriter_idx = header_map.get("주간사", 5)
        name = re.sub(r"\s+", " ", cols[name_idx] if len(cols) > name_idx else "").strip()
        if not name or "종목" in name or name == "-":
            continue
        listing_date = _parse_date(cols[schedule_idx] if len(cols) > schedule_idx else "") or _parse_date(" ".join(cols))
        final_offer_price = _to_int(cols[final_idx] if len(cols) > final_idx else "")
        rows.append(
            {
                "name": name,
                "code": "",
                "listing_date": listing_date.isoformat() if listing_date else date.today().isoformat(),
                "offer_band": cols[band_idx] if len(cols) > band_idx else "",
                "final_offer_price": final_offer_price,
                "offer_price": final_offer_price,
                "forecast_competition": cols[competition_idx] if len(cols) > competition_idx else "",
                "underwriter": cols[underwriter_idx] if len(cols) > underwriter_idx else "",
                "market": "",
                "source": "38커뮤니케이션",
            }
        )
    return rows


@lru_cache(maxsize=4)
def _load_fdr_listing_rows(cache_day: str | None = None) -> list[dict[str, Any]]:
    try:
        import FinanceDataReader as fdr

        df = fdr.StockListing("KRX-DESC")
    except Exception:
        return []
    if df is None or df.empty:
        return []
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        listing_date = _parse_date(row.get("ListingDate"))
        code = _normalize_code(row.get("Code"))
        name = str(row.get("Name") or "").strip()
        market = str(row.get("Market") or "").strip()
        if not listing_date or not code or not name or market not in {"KOSPI", "KOSDAQ"}:
            continue
        rows.append(
            {
                "name": name,
                "code": code,
                "listing_date": listing_date.isoformat(),
                "offer_price": 0,
                "market": market,
                "source": "FDR_KRX_DESC",
            }
        )
    return sorted(rows, key=lambda item: item["listing_date"])


def _resolve_ipo_stock(query: str) -> tuple[str, str, list[tuple[str, str]]]:
    text = str(query or "").strip()
    if not text:
        return "", "", []
    direct_code = _normalize_code(text)
    rows = _load_fdr_listing_rows(datetime.now().strftime("%Y-%m-%d"))
    if direct_code:
        for row in rows:
            if row.get("code") == direct_code:
                return direct_code, str(row.get("name") or ""), [(direct_code, str(row.get("name") or ""))]
        return direct_code, "", [(direct_code, "")]

    compact = re.sub(r"\s+", "", text).upper()
    matched = [
        (str(row.get("code") or ""), str(row.get("name") or ""))
        for row in rows
        if compact in re.sub(r"\s+", "", str(row.get("name") or "")).upper()
    ]
    exact = [item for item in matched if re.sub(r"\s+", "", item[1]).upper() == compact]
    if len(exact) == 1:
        return exact[0][0], exact[0][1], exact
    if len(matched) == 1:
        return matched[0][0], matched[0][1], matched
    return "", "", matched[:30]


def _estimate_rows(rows: list[dict[str, Any]], today: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recent: list[dict[str, Any]] = []
    upcoming: list[dict[str, Any]] = []
    for item in rows:
        listing_date = _parse_date(item.get("listing_date"))
        if listing_date is None:
            continue
        cloned = dict(item)
        offer_price = int(cloned.get("offer_price") or 0)
        if offer_price > 0:
            cloned["day1_low"] = int(math.floor(offer_price * 0.6))
            cloned["day1_high"] = int(math.ceil(offer_price * 4.0))
        else:
            cloned["day1_low"] = 0
            cloned["day1_high"] = 0
        cloned.setdefault("forecast_competition", "")
        cloned.setdefault("underwriter", "")
        cloned.setdefault("offer_band", "")
        cloned.setdefault("final_offer_price", cloned.get("offer_price") or 0)
        if today - timedelta(days=45) <= listing_date <= today and cloned.get("code"):
            recent.append(cloned)
        if today < listing_date <= today + timedelta(days=10):
            upcoming.append(cloned)
    recent.sort(key=lambda item: (str(item.get("listing_date") or ""), str(item.get("code") or "")), reverse=True)
    upcoming.sort(key=lambda item: str(item.get("listing_date") or ""))
    return recent[:12], upcoming[:12]


def _fetch_minute_rows(token: str, code: str) -> list[dict[str, Any]]:
    if not token or not code:
        return []
    try:
        url = kiwoom_utils.get_api_url("/api/dostk/chart")
        payload = {"stk_cd": code, "tic_scope": "1", "upd_stkpc_tp": "1"}
        results = kiwoom_utils.fetch_kiwoom_api_continuous(
            url=url,
            token=token,
            api_id="ka10080",
            payload=payload,
            use_continuous=True,
        )
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for res in results or []:
        source_rows = (
            res.get("stk_min_pole_chart_qry")
            or res.get("chart")
            or res.get("output")
            or res.get("list")
            or []
        )
        for item in source_rows:
            raw_dt = str(
                item.get("cntr_tm")
                or item.get("dt")
                or item.get("time")
                or item.get("stck_bsop_date")
                or ""
            )
            digits = re.sub(r"\D", "", raw_dt)
            if len(digits) >= 12:
                ts = datetime.strptime(digits[:12], "%Y%m%d%H%M")
            elif len(digits) >= 8:
                ts = datetime.strptime(digits[:8] + "0900", "%Y%m%d%H%M")
            elif len(digits) >= 4:
                ts = datetime.combine(datetime.now().date(), datetime.strptime(digits[:4], "%H%M").time())
            else:
                continue
            price = abs(_to_int(item.get("cur_prc") or item.get("close_pric") or item.get("close") or item.get("price")))
            volume = abs(_to_int(item.get("trde_qty") or item.get("volume") or item.get("vol")))
            if price <= 0:
                continue
            rows.append({"ts": ts, "price": price, "volume": volume})
    rows.sort(key=lambda row: row["ts"])
    return rows


def _bucket_minutes(rows: list[dict[str, Any]], listing_date: date | None) -> list[dict[str, Any]]:
    if not rows:
        return []
    if listing_date:
        target_dates = set(sorted({row["ts"].date() for row in rows if row["ts"].date() >= listing_date})[:2])
    else:
        target_dates = set(sorted({row["ts"].date() for row in rows})[-2:])
    filtered = [row for row in rows if row["ts"].date() in target_dates]
    if not filtered:
        filtered = rows[-240:]

    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in filtered:
        minute = row["ts"]
        slot_minute = (minute.minute // 30) * 30
        slot_start = minute.replace(minute=slot_minute, second=0, microsecond=0)
        day_no = 1
        if listing_date and minute.date() > listing_date:
            day_no = 2
        key = (f"{day_no}일차", slot_start.strftime("%H:%M"))
        buckets.setdefault(key, []).append(row)

    output = []
    for (day_label, slot), items in sorted(buckets.items()):
        prices = [item["price"] for item in items]
        volume = sum(item["volume"] for item in items)
        output.append(
            {
                "day_label": day_label,
                "slot": slot,
                "open": prices[0],
                "high": max(prices),
                "low": min(prices),
                "close": prices[-1],
                "volume": volume,
                "avg_price": int(round(sum(prices) / len(prices))),
            }
        )
    return output


def _format_number(value: Any) -> str:
    number = _to_int(value)
    return f"{number:,}" if number else "-"


def _view_model_bars(buckets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not buckets:
        return []
    max_volume = max(1, max(int(row.get("volume") or 0) for row in buckets))
    prices = [int(row.get("avg_price") or 0) for row in buckets if int(row.get("avg_price") or 0) > 0]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    span = max(1, max_price - min_price)
    bars = []
    for row in buckets:
        avg_price = int(row.get("avg_price") or 0)
        bars.append(
            {
                **row,
                "avg_price_display": _format_number(avg_price),
                "volume_display": _format_number(row.get("volume")),
                "volume_height": max(8, int((int(row.get("volume") or 0) / max_volume) * 150)),
                "price_height": max(8, int(((avg_price - min_price) / span) * 130) + 20) if avg_price else 8,
            }
        )
    return bars


def _build_line_chart(buckets: list[dict[str, Any]]) -> dict[str, Any]:
    if not buckets:
        return {"points": "", "labels": [], "avg_price": 0, "min_price": 0, "max_price": 0}
    prices = [int(row.get("avg_price") or 0) for row in buckets if int(row.get("avg_price") or 0) > 0]
    if not prices:
        return {"points": "", "labels": [], "avg_price": 0, "min_price": 0, "max_price": 0}
    min_price = min(prices)
    max_price = max(prices)
    avg_price = int(round(sum(prices) / len(prices)))
    span = max(1, max_price - min_price)
    width = max(620, (len(buckets) - 1) * 54)
    height = 300
    coords = []
    labels = []
    for idx, row in enumerate(buckets):
        price = int(row.get("avg_price") or 0)
        x = 28 + idx * ((width - 56) / max(1, len(buckets) - 1))
        y = 38 + ((max_price - price) / span) * (height - 118)
        coords.append((x, y))
        labels.append(
            {
                "x": x,
                "y": y,
                "label": f"{row.get('day_label')} {row.get('slot')}",
                "price": _format_number(price),
            }
        )
    return {
        "points": " ".join(f"{x:.1f},{y:.1f}" for x, y in coords),
        "circles": [{"x": x, "y": y} for x, y in coords],
        "labels": labels,
        "avg_price": avg_price,
        "avg_price_display": _format_number(avg_price),
        "min_price_display": _format_number(min_price),
        "max_price_display": _format_number(max_price),
        "width": width,
        "height": height,
    }


def _build_demand_result(selected_code: str, selected_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = None
    ipo38_rows = _load_38_ipo_rows(datetime.now().strftime("%Y-%m-%d"))
    for row in rows:
        if selected_code and row.get("code") == selected_code:
            matched = row
            break
        if selected_name and row.get("name") == selected_name:
            matched = row
            break
    matched = matched or {}
    compact_name = re.sub(r"\s+", "", selected_name or str(matched.get("name") or "")).upper()
    if compact_name:
        for row in ipo38_rows:
            row_name = re.sub(r"\s+", "", str(row.get("name") or "")).upper()
            if row_name == compact_name or compact_name in row_name or row_name in compact_name:
                matched = {**matched, **{k: v for k, v in row.items() if v not in (None, "", 0)}}
                break
    offer_price = int(matched.get("final_offer_price") or matched.get("offer_price") or 0)
    return {
        "name": matched.get("name") or selected_name or "-",
        "code": matched.get("code") or selected_code or "-",
        "listing_date": matched.get("listing_date") or "-",
        "underwriter": matched.get("underwriter") or "자동 수집 전",
        "offer_band": matched.get("offer_band") or "자동 수집 전",
        "final_offer_price": _format_number(offer_price),
        "source": matched.get("source") or "FDR/KIND fallback",
    }


@ipo_intraday_bp.route("/ipo-intraday")
def ipo_intraday_view():
    today = datetime.now().date()
    token = kiwoom_utils.get_kiwoom_token()
    rows, schedule_source = _load_ipo_rows()
    recent, upcoming = _estimate_rows(rows, today)

    selected_code = _normalize_code(request.values.get("code"))
    selected_name = (request.values.get("name") or "").strip()
    selected_listing_date = _parse_date(request.values.get("listing_date"))
    selected_candidates: list[tuple[str, str]] = []
    if not selected_code and selected_name:
        resolved_code, resolved_name, candidates = _resolve_ipo_stock(selected_name)
        if resolved_code:
            selected_code = resolved_code
            selected_name = resolved_name or selected_name
        else:
            selected_candidates = candidates
    if not selected_code and recent:
        selected_code = str(recent[0].get("code") or "")
        selected_name = str(recent[0].get("name") or "")
        selected_listing_date = _parse_date(recent[0].get("listing_date"))

    minute_rows = _fetch_minute_rows(token, selected_code) if selected_code else []
    buckets = _bucket_minutes(minute_rows, selected_listing_date)
    bars = _view_model_bars(buckets)
    line_chart = _build_line_chart(buckets)
    demand_result = _build_demand_result(selected_code, selected_name, rows)

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>IPO 1~2일차 거래 바차트</title>
      <style>
        :root { --bg:#f6f2e8; --card:#fffdf7; --ink:#222018; --muted:#77705f; --line:#e3d8c2; --accent:#a55b12; --good:#1d7a52; --bad:#b83232; }
        body { margin:0; background:radial-gradient(circle at top left,#ffe2b6 0,#f6f2e8 34%,#eee7da 100%); color:var(--ink); font-family:"Pretendard","Noto Sans KR",sans-serif; }
        .wrap { max-width:1180px; margin:0 auto; padding:24px 16px 40px; }
        .hero { background:linear-gradient(135deg,#2b2118,#a55b12); color:white; padding:22px; border-radius:22px; box-shadow:0 18px 40px rgba(69,42,13,.18); }
        .hero h1 { margin:0 0 8px; font-size:28px; }
        .hero p { margin:0; opacity:.84; }
        .grid { display:grid; grid-template-columns:1.1fr .9fr; gap:14px; margin-top:16px; }
        .panel { background:rgba(255,253,247,.92); border:1px solid var(--line); border-radius:18px; padding:16px; }
        .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
        .chip { display:inline-flex; gap:6px; align-items:center; color:var(--ink); background:#f2eadb; border:1px solid var(--line); padding:7px 10px; border-radius:999px; text-decoration:none; font-size:12px; }
        .chip.active { background:#3b2b1d; color:white; border-color:#3b2b1d; }
        .meta { color:var(--muted); font-size:13px; margin-top:8px; }
        table { width:100%; border-collapse:collapse; margin-top:10px; }
        th,td { border-top:1px solid var(--line); padding:8px 6px; text-align:left; font-size:13px; }
        th { color:var(--muted); font-size:12px; }
        .chart { overflow-x:auto; padding:10px 4px 4px; border-bottom:1px solid var(--line); }
        .line-svg { min-width:100%; }
        .axis-label { fill:var(--muted); font-size:11px; }
        .price-label { fill:#2b2118; font-size:12px; font-weight:800; text-anchor:middle; }
        .line-path { fill:none; stroke:#274c77; stroke-width:4; stroke-linecap:round; stroke-linejoin:round; }
        .line-dot { fill:#fffdf7; stroke:#274c77; stroke-width:3; }
        .legend { display:flex; gap:12px; color:var(--muted); font-size:12px; margin-top:8px; }
        .dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:4px; }
        .blue { background:#6096ba; } .gold { background:#d08c31; }
        .demand-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin-top:16px; }
        .demand-card { background:#fff8eb; border:1px solid var(--line); border-radius:14px; padding:12px; }
        .demand-label { color:var(--muted); font-size:12px; margin-bottom:6px; }
        .demand-value { font-size:20px; font-weight:800; }
        form { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
        input,button { border:1px solid var(--line); border-radius:10px; padding:9px 10px; background:white; }
        button { background:var(--accent); color:white; border-color:var(--accent); cursor:pointer; }
        @media (max-width:860px) { .grid { grid-template-columns:1fr; } }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>IPO 상장 1~2일차 체결가격·거래량</h1>
          <p>최근 상장 종목은 실거래 분봉을 30분 구간으로 묶고, 다음 상장 예정 종목은 공모가 기준 첫날 가능 범위를 추정합니다.</p>
        </div>

        <div class="grid">
          <div class="panel">
            <h3>최근 상장 종목</h3>
            <div class="chips">
              {% for item in recent %}
                <a class="chip {% if item.code == selected_code %}active{% endif %}" href="/ipo-intraday?code={{ item.code }}&name={{ item.name }}&listing_date={{ item.listing_date }}">{{ item.listing_date }} {{ item.name }}{% if item.code %}({{ item.code }}){% endif %}</a>
              {% else %}
                <span class="meta">최근 상장 일정 자동조회 결과가 없습니다.</span>
              {% endfor %}
            </div>
            <form method="GET" action="/ipo-intraday">
              <input name="code" placeholder="종목코드 선택입력" value="{{ selected_code }}">
              <input name="name" placeholder="종목명 예: 채비" value="{{ selected_name }}">
              <input name="listing_date" placeholder="상장일 YYYY-MM-DD" value="{{ selected_listing_date }}">
              <button type="submit">직접 조회</button>
            </form>
            {% if selected_candidates %}
              <div class="meta">종목명 검색 결과가 다수입니다. 후보를 선택하세요.</div>
              <div class="chips">
                {% for code, name in selected_candidates %}
                  <a class="chip" href="/ipo-intraday?code={{ code }}&name={{ name }}{% if selected_listing_date %}&listing_date={{ selected_listing_date }}{% endif %}">{{ code }} {{ name }}</a>
                {% endfor %}
              </div>
            {% endif %}
            <div class="meta">일정 출처: {{ schedule_source }} / 분봉 출처: Kiwoom ka10080</div>
          </div>

          <div class="panel">
            <h3>다음 상장 예정 추정</h3>
            <table>
              <thead><tr><th>상장예정일</th><th>종목</th><th>공모가</th><th>첫날 추정범위</th></tr></thead>
              <tbody>
              {% for item in upcoming %}
                <tr>
                  <td>{{ item.listing_date }}</td>
                  <td>{{ item.name }}{% if item.code %}<br><span class="meta">{{ item.code }}</span>{% endif %}</td>
                  <td>{{ fmt(item.offer_price) }}</td>
                  <td>{{ fmt(item.day1_low) }} ~ {{ fmt(item.day1_high) }}</td>
                </tr>
              {% else %}
                <tr><td colspan="4" class="meta">향후 10일 내 자동조회된 IPO 예정 종목이 없습니다.</td></tr>
              {% endfor %}
              </tbody>
            </table>
            <div class="meta">추정범위는 공모가가 있을 때 첫 거래일 가격제한폭 60%~400%를 단순 적용한 값입니다. 상장 후에는 위 실거래 분봉 기준으로 대체합니다.</div>
          </div>
        </div>

        <div class="panel" style="margin-top:16px;">
          <h3>수요예측 결과</h3>
          <div class="demand-grid">
            <div class="demand-card"><div class="demand-label">대상</div><div class="demand-value">{{ demand_result.name }}</div><div class="meta">{{ demand_result.code }} / 상장일 {{ demand_result.listing_date }}</div></div>
            <div class="demand-card"><div class="demand-label">주간사</div><div class="demand-value">{{ demand_result.underwriter }}</div></div>
            <div class="demand-card"><div class="demand-label">공모가 밴드</div><div class="demand-value">{{ demand_result.offer_band }}</div></div>
            <div class="demand-card"><div class="demand-label">확정 공모가</div><div class="demand-value">{{ demand_result.final_offer_price }}</div><div class="meta">출처: {{ demand_result.source }}</div></div>
          </div>
          <div class="meta">현재 자동 일정 fallback은 상장일/코드 중심입니다. 경쟁률·밴드·확정공모가가 비어 있으면 외부 IPO 일정 소스 또는 수동 메타데이터 연동이 필요합니다.</div>
        </div>

        <div class="panel" style="margin-top:16px;">
          <h3>{% if selected_name %}{{ selected_name }} {% endif %}{% if selected_code %}{{ selected_code }}{% endif %} 30분 구간 체결가 라인차트</h3>
          {% if bars %}
            <div class="chips">
              <div class="chip">구간 평균가 평균: {{ line_chart.avg_price_display }}</div>
              <div class="chip">최저 평균가: {{ line_chart.min_price_display }}</div>
              <div class="chip">최고 평균가: {{ line_chart.max_price_display }}</div>
            </div>
            <div class="chart">
              <svg class="line-svg" viewBox="0 0 {{ line_chart.width }} {{ line_chart.height }}" width="{{ line_chart.width }}" height="{{ line_chart.height }}" role="img">
                <polyline class="line-path" points="{{ line_chart.points }}"></polyline>
                {% for point in line_chart.circles %}
                  <circle class="line-dot" cx="{{ '%.1f'|format(point.x) }}" cy="{{ '%.1f'|format(point.y) }}" r="5"></circle>
                {% endfor %}
                {% for label in line_chart.labels %}
                  <text class="price-label" x="{{ '%.1f'|format(label.x) }}" y="{{ '%.1f'|format(label.y - 12) }}">{{ label.price }}</text>
                  <text class="axis-label" x="{{ '%.1f'|format(label.x) }}" y="{{ line_chart.height - 52 }}" transform="rotate(45 {{ '%.1f'|format(label.x) }} {{ line_chart.height - 52 }})">{{ label.label }}</text>
                {% endfor %}
              </svg>
            </div>
            <div class="legend"><span><i class="dot blue"></i>30분 구간 평균 체결가격</span></div>
            <table>
              <thead><tr><th>일차</th><th>구간</th><th>시가</th><th>고가</th><th>저가</th><th>종가</th><th>평균가</th></tr></thead>
              <tbody>
              {% for row in bars %}
                <tr><td>{{ row.day_label }}</td><td>{{ row.slot }}</td><td>{{ fmt(row.open) }}</td><td>{{ fmt(row.high) }}</td><td>{{ fmt(row.low) }}</td><td>{{ fmt(row.close) }}</td><td>{{ row.avg_price_display }}</td></tr>
              {% endfor %}
              </tbody>
            </table>
          {% else %}
            <div class="meta">분봉 실거래 데이터가 아직 없거나 Kiwoom 조회 범위 밖입니다. 상장 당일/익일에는 실거래 기준으로 자동 표시됩니다.</div>
          {% endif %}
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        recent=recent,
        upcoming=upcoming,
        selected_code=selected_code,
        selected_name=selected_name,
        selected_listing_date=selected_listing_date.isoformat() if selected_listing_date else "",
        selected_candidates=selected_candidates,
        schedule_source=schedule_source,
        bars=bars,
        line_chart=line_chart,
        demand_result=demand_result,
        fmt=_format_number,
    )
