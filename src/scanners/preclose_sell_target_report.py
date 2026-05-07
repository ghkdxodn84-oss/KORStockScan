"""
preclose_sell_target_report.py

15:00 KST 기준 익일 매도 목표 종목 선정 리포트.
크론탭 또는 수동으로 단독 실행한다. bot_main.py와 무관하게 동작한다.

실행:
    python src/scanners/preclose_sell_target_report.py

크론탭:
    0 6 * * 1-5 cd /home/ubuntu/KORStockScan && .venv/bin/python src/scanners/preclose_sell_target_report.py

의존성:
    - src/database/db_manager.py
    - src/database/models.py
    - src/core/event_bus.py
    - src/utils/constants.py (TRADING_RULES.AI_MODEL_TIER3)
    - src/utils/logger.py
    - google.genai (직접 호출)

순환참조 금지:
    - bot_main, eod_analyzer, daily_report_service, ai_engine(GeminiSniperEngine) import 불가
"""

import sys
import os
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory, DailyStockQuote
from src.core.event_bus import EventBus
from src.utils.constants import TRADING_RULES
from src.utils.logger import log_error

REPORT_SCHEMA_VERSION = 1
PRE_CLOSE_REPORT_DIR = PROJECT_ROOT / "data" / "report" / "preclose_sell_target"

# Google GenAI 직접 호출 (신규 SDK google.genai)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google.genai 모듈이 설치되지 않았습니다. AI 호출을 건너뜁니다.")

# 설정 파일 로드 (API 키 획득용)
from src.utils.constants import CONFIG_PATH, DEV_PATH

def _load_config():
    """환경에 맞는 설정 파일(JSON)을 로드합니다."""
    target_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else DEV_PATH
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 설정 파일 로드 실패: {e}")
        return {}


def _gemini_key_sort_key(name: str) -> Tuple[int, str]:
    suffix = name.replace("GEMINI_API_KEY", "", 1).lstrip("_")
    if suffix == "":
        return (1, name)
    try:
        return (int(suffix), name)
    except ValueError:
        return (999, name)


def _load_gemini_api_keys(conf: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Return configured Gemini keys in deterministic key1/key2/key3 order."""
    keys: List[Tuple[str, str]] = []
    for name, value in sorted(conf.items(), key=lambda item: _gemini_key_sort_key(str(item[0]))):
        if not str(name).startswith("GEMINI_API_KEY"):
            continue
        if value in (None, "", "-"):
            continue
        keys.append((str(name), str(value)))
    return keys

# --- Public API ---
def run_preclose_sell_target_report(
    report_date: Optional[str] = None,
    *,
    use_ai: bool = True,
    broadcast: bool = True,
    write_legacy_markdown: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """크론탭 / 수동 실행 진입점. 예외 발생 시 로그 후 종료."""
    try:
        print(f"[{datetime.now().isoformat()}] 익일 매도 목표 리포트 시작")
        report_date = report_date or date.today().isoformat()
        
        # 1. DB 연결
        db = DBManager()
        
        # 2. Track A: 보유 정리 후보
        holding_candidates = _fetch_holding_candidates(db)
        print(f"Track A 후보: {len(holding_candidates)}개")
        
        # 3. Track B: 신규 스윙 진입 후보
        swing_candidates = _fetch_daily_quote_candidates(db)
        print(f"Track B 후보: {len(swing_candidates)}개")
        
        # 4. T-1 ML 스코어 로드
        t1_scores, t1_date = _load_t1_ml_scores()
        print(f"T-1 ML 스코어 로드: {len(t1_scores)}개 (날짜: {t1_date})")
        
        # 5. 스코어링
        scored_holding = []
        for row in holding_candidates:
            scored = _score_holding(row)
            scored_holding.append(scored)
        
        # Track B에 T-1 스코어 병합 및 스코어링
        for row in swing_candidates:
            row["t1_score"] = t1_scores.get(row["stock_code"], 0.0)
        scored_swing = sorted(swing_candidates, key=_score_swing, reverse=True)[:10]
        
        # 6. AI 호출 (가능한 경우)
        if use_ai and GENAI_AVAILABLE and len(scored_holding) + len(scored_swing) > 0:
            ai_result = _call_gemini_preclose(scored_holding, scored_swing)
        else:
            if not use_ai:
                ai_summary = "AI 호출 비활성화"
                ai_caution = "AI 미사용(--no-ai)"
            elif not GENAI_AVAILABLE:
                ai_summary = "AI 호출 불가"
                ai_caution = "google.genai 미설치"
            else:
                ai_summary = "후보 없음"
                ai_caution = "AI 미사용"
            ai_result = {
                "sell_targets": [],
                "summary": ai_summary,
                "market_caution": ai_caution
            }
        
        # 7. 리포트 생성
        markdown = _render_markdown(ai_result, report_date, scored_holding, scored_swing, t1_date)
        structured_report = _build_structured_report(
            result=ai_result,
            report_date=report_date,
            holding_candidates=scored_holding,
            swing_candidates=scored_swing,
            t1_date=t1_date,
            use_ai=use_ai,
        )
        
        # 8. 파일 저장
        artifact_paths = {}
        if not dry_run:
            artifact_paths = _save_report_artifacts(
                markdown,
                structured_report,
                report_date,
                write_legacy_markdown=write_legacy_markdown,
            )
            print(f"리포트 저장: {artifact_paths}")
        else:
            print("dry-run: 리포트 파일 저장 생략")
        
        # 9. Telegram 전송
        if broadcast and not dry_run:
            _broadcast_telegram(ai_result, markdown, report_date)
        
        print(f"[{datetime.now().isoformat()}] 익일 매도 목표 리포트 완료")
        return {
            "report": structured_report,
            "markdown": markdown,
            "artifact_paths": {k: str(v) for k, v in artifact_paths.items()},
        }
        
    except Exception as e:
        log_error(f"preclose_sell_target_report 실패: {e}", exc_info=True)
        raise

# --- 데이터 수집 ---
def _fetch_holding_candidates(db: DBManager) -> List[Dict[str, Any]]:
    """Track A: 오늘 HOLDING/BUY_ORDERED 종목 조회 + 최신 일봉 조인"""
    with db.get_session() as session:
        # 가장 최근 일봉 날짜
        latest_date = session.query(DailyStockQuote.quote_date)\
            .order_by(DailyStockQuote.quote_date.desc())\
            .first()
        if not latest_date:
            return []
        latest_date = latest_date[0]
        
        # 쿼리
        query = session.query(
            RecommendationHistory.stock_code,
            RecommendationHistory.stock_name,
            RecommendationHistory.buy_price,
            RecommendationHistory.profit_rate,
            RecommendationHistory.position_tag,
            RecommendationHistory.strategy,
            RecommendationHistory.trade_type,
            DailyStockQuote.close_price,
            DailyStockQuote.volume,
            DailyStockQuote.ma20,
            DailyStockQuote.rsi,
            DailyStockQuote.bbu,
            DailyStockQuote.bbl,
            DailyStockQuote.foreign_net,
            DailyStockQuote.inst_net
        ).join(
            DailyStockQuote,
            (RecommendationHistory.stock_code == DailyStockQuote.stock_code) &
            (DailyStockQuote.quote_date == latest_date)
        ).filter(
            RecommendationHistory.status.in_(['HOLDING', 'BUY_ORDERED'])
            # rec_date 조건 삭제 — 진입일 무관하게 현재 보유 종목 전체 대상
        ).order_by(RecommendationHistory.profit_rate.desc())
        
        rows = query.all()
        candidates = []
        for row in rows:
            candidates.append({
                "stock_code": row.stock_code,
                "stock_name": row.stock_name,
                "buy_price": row.buy_price,
                "profit_rate": row.profit_rate,
                "position_tag": row.position_tag,
                "strategy": row.strategy,
                "trade_type": row.trade_type,
                "close_price": row.close_price,
                "volume": row.volume,
                "ma20": row.ma20,
                "rsi": row.rsi,
                "bbu": row.bbu,
                "bbl": row.bbl,
                "foreign_net": row.foreign_net,
                "inst_net": row.inst_net
            })
        return candidates

def _fetch_daily_quote_candidates(db: DBManager) -> List[Dict[str, Any]]:
    """Track B용 DB 후보: 정배열 + RSI 골든존 + 수급 동시 매수 종목"""
    with db.get_session() as session:
        latest_date = session.query(DailyStockQuote.quote_date)\
            .order_by(DailyStockQuote.quote_date.desc())\
            .first()
        if not latest_date:
            return []
        latest_date = latest_date[0]
        
        # 필터: close > ma20, RSI 50~72, foreign_net > 0, inst_net > 0
        query = session.query(DailyStockQuote).filter(
            DailyStockQuote.quote_date == latest_date,
            DailyStockQuote.close_price > DailyStockQuote.ma20,
            DailyStockQuote.rsi >= 50,
            DailyStockQuote.rsi <= 72,
            DailyStockQuote.foreign_net > 0,
            DailyStockQuote.inst_net > 0
        ).order_by(DailyStockQuote.volume.desc())
        
        rows = query.all()
        candidates = []
        for row in rows:
            candidates.append({
                "stock_code": row.stock_code,
                "stock_name": row.stock_name,
                "close_price": row.close_price,
                "volume": row.volume,
                "ma20": row.ma20,
                "rsi": row.rsi,
                "bbu": row.bbu,
                "bbl": row.bbl,
                "foreign_net": row.foreign_net,
                "inst_net": row.inst_net
            })
        return candidates

def _load_t1_ml_scores() -> Tuple[Dict[str, float], str]:
    """daily_recommendations_v2.csv에서 T-1 스코어 로드 (가장 최근 date 기준)"""
    csv_path = Path(PROJECT_ROOT) / "data" / "daily_recommendations_v2.csv"
    if not csv_path.exists():
        return {}, ""
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return {}, ""
        # 가장 최근 날짜 기준
        latest_date = df["date"].max()
        latest_df = df[df["date"] == latest_date]
        # stock_code는 문자열로 변환 (앞쪽 0 유지)
        latest_df["code"] = latest_df["code"].astype(str).str.zfill(6)
        scores = dict(zip(latest_df["code"], latest_df["score"]))
        return scores, latest_date
    except Exception as e:
        log_error(f"T-1 ML 스코어 로드 실패: {e}")
        return {}, ""

# --- 스코어링 ---
def _score_holding(row: Dict[str, Any]) -> Dict[str, Any]:
    """Track A 복합 스코어 + label(SELL_TOMORROW_STRONG / HOLD_MONITOR / CUT_LOSS_CONSIDER) 반환"""
    profit_rate = row.get("profit_rate", 0.0)
    rsi = row.get("rsi", 50)
    ma20 = row.get("ma20", 0)
    close = row.get("close_price", 0)
    foreign_net = row.get("foreign_net", 0)
    inst_net = row.get("inst_net", 0)
    bbu = row.get("bbu", 0)
    bbl = row.get("bbl", 0)
    
    # 점수 계산 (가중치 반영)
    score_profit = min(max(profit_rate, -10), 10) / 10.0 * 40  # -10%~10% 범위, 40점 만점
    score_momentum = 0
    if close > ma20 and 55 <= rsi <= 75:
        score_momentum = 30
    elif close > ma20 and rsi > 75:
        score_momentum = 10
    else:
        score_momentum = 5
    
    score_flow = 0
    if foreign_net > 0 and inst_net > 0:
        score_flow = 20
    elif foreign_net > 0 or inst_net > 0:
        score_flow = 10
    
    score_bb = 0
    if bbu != bbl:
        bb_ratio = (close - bbl) / (bbu - bbl)
        if bb_ratio < 0.6:
            score_bb = 10
        else:
            score_bb = 2
    
    total_score = score_profit + score_momentum + score_flow + score_bb
    
    # 라벨 결정
    label = "HOLD_MONITOR"
    if profit_rate > 0 and total_score >= 60:
        label = "SELL_TOMORROW_STRONG"
    elif profit_rate < -2:
        label = "CUT_LOSS_CONSIDER"
    
    row["score"] = total_score
    row["label"] = label
    return row

def _score_swing(row: Dict[str, Any]) -> float:
    """Track B 복합 스코어 (T-1 ML 35% + BB스퀴즈 25% + 수급 25% + RSI 15%)"""
    t1_score = row.get("t1_score", 0.0)
    close = row.get("close_price", 1)
    bbu = row.get("bbu", close)
    bbl = row.get("bbl", close)
    foreign_net = row.get("foreign_net", 0)
    inst_net = row.get("inst_net", 0)
    rsi = row.get("rsi", 50)
    
    # BB 스퀴즈: 밴드 폭이 좁을수록 높은 점수
    if bbu != bbl:
        bb_width = (bbu - bbl) / close
        bb_squeeze = 1.0 - min(bb_width, 0.2) * 5  # 0~1 범위
    else:
        bb_squeeze = 0.5
    
    # 수급 동시 매수 여부
    flow_score = 1.0 if (foreign_net > 0 and inst_net > 0) else 0.0
    
    # RSI 위치 점수
    if 50 <= rsi <= 65:
        rsi_score = 1.0
    elif 66 <= rsi <= 72:
        rsi_score = 0.5
    else:
        rsi_score = 0.0
    
    # 가중합
    composite = (t1_score * 0.35) + (bb_squeeze * 0.25) + (flow_score * 0.25) + (rsi_score * 0.15)
    row["composite_score"] = round(composite, 4)  # 추가
    return composite

# --- AI 호출 ---
def _call_gemini_preclose(
    holding_candidates: List[Dict[str, Any]],
    swing_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    google.genai 직접 호출 (TRADING_RULES.AI_MODEL_TIER3 사용).
    GeminiSniperEngine import 없이 독립 구현.
    반환: {"sell_targets": [...], "summary": str, "market_caution": str}
    """
    if not GENAI_AVAILABLE:
        return {"sell_targets": [], "summary": "AI 호출 불가", "market_caution": "AI 미사용"}
    
    model_name = TRADING_RULES.AI_MODEL_TIER3
    CONF = _load_config()
    api_keys = _load_gemini_api_keys(CONF)
    if not api_keys:
        return {"sell_targets": [], "summary": "GEMINI_API_KEY 미설정", "market_caution": "API 키 없음"}
    
    # 프롬프트 작성 (작업지시서에 제시된 프롬프트 사용)
    prompt = f"""
너는 한국 주식 단기 트레이더다.
오늘 15:00 기준으로 내일 매도를 목표로 하는 종목을 선정한다.

[참고: 입력 데이터 특성]
- Track A 보유 종목은 오늘 현재 HOLDING 상태이며, 오버나이트 유지 후 익일 매도 여부를 판단한다.
- Track B 후보는 오늘 일봉 기준 기술적 조건을 충족하며, T-1(전일) ML 스코어로 품질을 검증했다.
  T-1 스코어는 전날 종가 기준으로 생성된 ML 예측값이므로 오늘 시장 변화를 반영하지 않는다.
  따라서 당일 일봉 지표(RSI, BB, 수급)를 T-1 스코어보다 우선하여 판단한다.

[입력 데이터 A - 현재 보유 종목]
{json.dumps(holding_candidates, ensure_ascii=False, indent=2)}

[입력 데이터 B - 신규 스윙 진입 후보 (상위 10개)]
{json.dumps(swing_candidates, ensure_ascii=False, indent=2)}

[판단 기준]
1. 익일 시가~오전 매도가 유리한 종목을 최대 5개 선정한다.
2. Track A는 현재 수익률, 모멘텀 지속성, 수급 방향을 종합하여 SELL/HOLD/CUT_LOSS를 판정한다.
3. Track B는 당일 BB 스퀴즈 + 수급 동시 매수를 우선하고, T-1 ML 스코어는 보조 신호로 참고한다.
4. 익일 되돌림 리스크(BB 상단 근접, RSI 70 초과, 외인/기관 이탈)가 있는 종목은 제외한다.
5. 각 종목별로 매도 근거 1줄과 리스크 1줄을 명시한다.

[출력 형식 - JSON only, 다른 텍스트 출력 금지]
{{
  "sell_targets": [
    {{
      "rank": 1,
      "stock_code": "000100",
      "stock_name": "유한양행",
      "track": "A",
      "sell_rationale": "익일 시가 강세 기대, 수급 3일 연속 매수",
      "risk_note": "RSI 68로 단기 과열 주의",
      "sell_timing": "익일 09:05~09:30 시초가 근처",
      "confidence": 78
    }}
  ],
  "summary": "오늘 장 막판 모멘텀 강세 종목 중심, 익일 오전 차익 실현 전략",
  "market_caution": "시장 전반 과열 여부 또는 주의 사항 1줄"
}}
"""
    
    attempt_errors = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            text = response.text.strip()
            # JSON 파싱
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
            else:
                result = {"sell_targets": [], "summary": "AI 응답 파싱 실패", "market_caution": "파싱 실패"}
            result["ai_provider_status"] = {
                "provider": "gemini",
                "status": "success",
                "key_name": key_name,
                "attempt_index": attempt_index,
                "attempted_keys": len(api_keys),
            }
            return result
        except Exception as e:
            attempt_errors.append({"key_name": key_name, "error": str(e)})
            log_error(f"Gemini 호출 실패({key_name}, attempt={attempt_index}/{len(api_keys)}): {e}")

    last_error = attempt_errors[-1]["error"] if attempt_errors else "unknown"
    return {
        "sell_targets": [],
        "summary": "AI 호출 오류",
        "market_caution": f"Gemini API key fallback 모두 실패: {last_error}",
        "ai_provider_status": {
            "provider": "gemini",
            "status": "failed",
            "attempted_keys": len(api_keys),
            "errors": attempt_errors,
        },
    }

# --- 출력 ---
def _render_markdown(
    result: Dict[str, Any],
    report_date: str,
    holding_candidates: List[Dict[str, Any]],
    swing_candidates: List[Dict[str, Any]],
    t1_date: str
) -> str:
    """Markdown 리포트 문자열 생성"""
    # 헤더
    md = f"""# 📋 [{report_date}] 익일 매도 목표 종목 리포트 (15:00 기준)

> 생성시각: {report_date} 15:00 KST | Track A: 보유 정리 | Track B: 신규 스윙 (T-1 ML + 당일 일봉)

## 시장 종합 판단
{result.get('market_caution', 'AI 판단 없음')}

## 익일 매도 목표 TOP 5
"""
    sell_targets = result.get("sell_targets", [])
    if sell_targets:
        md += """
| 순위 | 종목 | 트랙 | 수익률 | 매도 타이밍 | 신뢰도 |
|---|---|---|---|---|---|
"""
        for target in sell_targets[:5]:
            stock_name = target.get("stock_name", "N/A")
            stock_code = target.get("stock_code", "")
            track = target.get("track", "")
            # 수익률은 Track A만 존재할 수 있음
            profit_rate = "—"
            if track == "A":
                # holding_candidates에서 찾기
                for h in holding_candidates:
                    if h.get("stock_code") == stock_code:
                        profit_rate = f"{h.get('profit_rate', 0):+.1f}%"
                        break
            sell_timing = target.get("sell_timing", "")
            confidence = target.get("confidence", 0)
            md += f"| {target.get('rank', '')} | {stock_name} ({stock_code}) | {track} | {profit_rate} | {sell_timing} | {confidence} |\n"
    else:
        md += "AI가 선정한 매도 목표가 없습니다.\n"
    
    md += "\n"
    # 상세 설명
    for idx, target in enumerate(sell_targets[:5], start=1):
        stock_name = target.get("stock_name", "N/A")
        stock_code = target.get("stock_code", "")
        track = target.get("track", "")
        sell_rationale = target.get("sell_rationale", "")
        risk_note = target.get("risk_note", "")
        md += f"### {idx}위: {stock_name} ({stock_code}) [Track {track} — {'보유 정리' if track == 'A' else '신규 스윙'}]\n"
        md += f"- **매도 근거**: {sell_rationale}\n"
        md += f"- **리스크**: {risk_note}\n\n"
    
    md += f"## 전략 요약\n{result.get('summary', '요약 없음')}\n\n"
    md += "---\n"
    md += f"*본 리포트는 15:00 스냅샷 기준. Track B의 T-1 ML 스코어는 전일({t1_date}) 종가 기준입니다.*\n"
    md += "*이후 장중 변동 및 오늘 밤 생성되는 오늘 기준 ML 스코어는 반영되지 않습니다.*\n"
    return md

def _save_report(markdown: str, report_date: str) -> Path:
    """data/report/preclose_sell_target_YYYY-MM-DD.md 저장"""
    report_dir = PROJECT_ROOT / "data" / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"preclose_sell_target_{report_date}.md"
    report_path.write_text(markdown, encoding="utf-8")
    return report_path

def _build_structured_report(
    *,
    result: Dict[str, Any],
    report_date: str,
    holding_candidates: List[Dict[str, Any]],
    swing_candidates: List[Dict[str, Any]],
    t1_date: str,
    use_ai: bool,
) -> Dict[str, Any]:
    """Future threshold/ADM consumers should read this JSON, not parse Markdown."""
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": "preclose_sell_target",
        "date": report_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "automation_stage": "R1_daily_report",
        "policy_status": "report_only",
        "live_runtime_effect": False,
        "consumer_contract": {
            "primary_consumer": "operator_preclose_review",
            "future_consumers": [
                "holding_overnight_decision_support",
                "threshold_cycle_report_context",
                "swing_trailing_policy_review",
                "ADM_ladder_context",
            ],
            "forbidden_use_before_acceptance": [
                "live_threshold_mutation",
                "bot_restart",
                "automatic_order_submit",
                "automatic_sell_submit",
            ],
        },
        "input_summary": {
            "track_a_holding_count": len(holding_candidates),
            "track_b_swing_count": len(swing_candidates),
            "t1_ml_score_date": t1_date,
            "ai_requested": bool(use_ai),
            "ai_available": bool(GENAI_AVAILABLE),
        },
        "decision_summary": {
            "sell_target_count": len(result.get("sell_targets", [])),
            "summary": result.get("summary", ""),
            "market_caution": result.get("market_caution", ""),
            "ai_provider_status": result.get("ai_provider_status") or {},
        },
        "sell_targets": result.get("sell_targets", []),
        "track_a_holding_candidates": holding_candidates,
        "track_b_swing_candidates": swing_candidates,
        "quality_notes": [
            "Track B T-1 ML score is stale by design and must not override current-day flow.",
            "Markdown is human-readable; JSON is canonical for automation.",
            "Report-only artifact. Runtime action requires a separate checklist owner and acceptance gate.",
        ],
    }

def _save_report_artifacts(
    markdown: str,
    structured_report: Dict[str, Any],
    report_date: str,
    *,
    write_legacy_markdown: bool = True,
) -> Dict[str, Path]:
    """Save canonical JSON/Markdown pair and optional legacy Markdown path."""
    PRE_CLOSE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = PRE_CLOSE_REPORT_DIR / f"preclose_sell_target_{report_date}.json"
    md_path = PRE_CLOSE_REPORT_DIR / f"preclose_sell_target_{report_date}.md"
    json_path.write_text(json.dumps(structured_report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    paths = {"json": json_path, "markdown": md_path}
    if write_legacy_markdown:
        paths["legacy_markdown"] = _save_report(markdown, report_date)
    return paths

def _broadcast_telegram(result: Dict[str, Any], markdown: str, report_date: str) -> None:
    """EventBus를 통해 Telegram VIP_ALL 전송"""
    try:
        # Telegram 리스너 등록을 위해 임포트
        import src.notify.telegram_manager
        event_bus = EventBus()
        # 축약 메시지 생성 (첫 부분만) — 생성시각 줄 제외
        lines = markdown.split('\n')
        summary = ""
        for line in lines:
            if line.startswith("## 익일 매도 목표 TOP 5"):
                break
            if line.strip() and not line.startswith("#") and not line.startswith("> 생성시각:"):
                summary += line.strip() + " "
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        # Telegram 메시지 포맷팅
        telegram_msg = "오늘 장마감전 매수 내일 매도 추천종목\n\n"
        # sell_targets 직접 순회
        sell_targets = result.get("sell_targets", [])
        for i, target in enumerate(sell_targets[:5], start=1):
            stock_name = target.get("stock_name", "N/A")
            stock_code = target.get("stock_code", "")
            track = target.get("track", "")
            label = "보유" if track == "A" else "스윙"
            telegram_msg += f"{i}. {stock_name}({stock_code}) [{label}]\n"
        
        telegram_msg += f"\n📄 상세: data/report/preclose_sell_target/preclose_sell_target_{report_date}.md"
        
        event_bus.publish('TELEGRAM_BROADCAST', {
            'message': telegram_msg,
            'audience': 'VIP_ALL',
            'parse_mode': 'HTML'
        })
    except Exception as e:
        log_error(f"Telegram 전송 실패: {e}")

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate preclose sell target report artifacts.")
    parser.add_argument("--date", dest="report_date", default=None, help="Report date in YYYY-MM-DD. Default: today.")
    parser.add_argument("--no-ai", action="store_true", help="Skip Gemini call and emit deterministic report-only artifacts.")
    parser.add_argument("--no-telegram", action="store_true", help="Skip Telegram broadcast.")
    parser.add_argument("--no-legacy-markdown", action="store_true", help="Do not write data/report/preclose_sell_target_YYYY-MM-DD.md.")
    parser.add_argument("--dry-run", action="store_true", help="Build the report in memory without writing files or broadcasting.")
    return parser.parse_args()

# --- 진입점 ---
if __name__ == "__main__":
    args = _parse_args()
    run_preclose_sell_target_report(
        report_date=args.report_date,
        use_ai=not args.no_ai,
        broadcast=not args.no_telegram,
        write_legacy_markdown=not args.no_legacy_markdown,
        dry_run=args.dry_run,
    )
