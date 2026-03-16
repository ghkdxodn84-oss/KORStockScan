"""
================================================================================
💡 [KORStockScan 아키텍처 노트] Level 2: 하이브리드(Hybrid) 이벤트/데이터 처리 모델
================================================================================
본 스나이퍼 엔진은 시스템 결합도를 낮추면서도 초단타(SCALPING)의 극한 성능을 뽑아내기 위해 
두 가지 아키텍처 패턴을 혼용(Hybrid)하여 설계되었습니다.

1. 제어 흐름 (Control Flow) -> Event-Driven (Push 방식)
   - 텔레그램 발송, 스캐너의 신규 감시 지시, DB 상태 변경 알림 등은 `EventBus`를 통한 
     완벽한 Pub/Sub 모델을 적용하여 모듈 간 강결합을 제거했습니다.

2. 데이터 흐름 (Data Flow) -> Memory Snapshot & Polling (Pull 방식)
   - 초당 수백 번씩 쏟아지는 웹소켓 틱/호가 데이터를 EventBus에 싣게 되면, 
     이벤트 큐(Queue) 병목 현상과 파이썬 GIL 한계로 인해 치명적인 타점 지연(Latency)이 발생합니다.
   - 따라서 실시간 시장 데이터(`ws_data`)는 KiwoomWSManager가 내부 메모리(Dictionary)에 
     항상 '최신 상태만 덮어쓰기'를 하고, 스나이퍼 루프는 자신의 분석 템포에 맞춰 
     가장 신선한 데이터만 당겨오는(Pull) 방식을 고수합니다.
================================================================================
"""
import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
	
import os
import time
from datetime import datetime
import threading   
import numpy as np
import pandas as pd
import json

# 💡 Level 1 & 2 공통 모듈 (경로 및 패키지 구조에 맞게 통일)
from src.utils import kiwoom_utils
from src.utils.logger import log_error
from src.utils.constants import TRADING_RULES, CREDENTIALS_PATH, CONFIG_PATH, DEV_PATH
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.utils.google_sheets_utils import GoogleSheetsManager
from src.database.models import RecommendationHistory

# 💡 뇌(AI)와 눈(웹소켓, 레이더) 임포트
from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.signal_radar import SniperRadar
from src.engine.ai_engine import GeminiSniperEngine
# from src.engine.ai_engine_openai import OpenAISniperEngine

# 스캐너 모듈 (장중 스캔 호출용)
import src.scanners.final_ensemble_scanner as final_ensemble_scanner

# --- [전역 상태 변수] -----------------------------------------------
highest_prices = {}
alerted_stocks = set()
cooldowns = {}  # 스캘핑 뇌동매매 방지용 쿨타임 관리

def load_system_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}

CONF = load_system_config()
KIWOOM_TOKEN = None
WS_MANAGER = None
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager()  
event_bus = EventBus() # 💡 [신규] 전역 이벤트 버스 장착!

global ACTIVE_TARGETS
ACTIVE_TARGETS = []
LAST_AI_CALL_TIMES = {}
# -------------------------------------------------------------------

def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다. (ORM 완벽 적용)"""
    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")
    
    real_inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN) 
    
    if real_inventory is None:
        print("⚠️ [동기화 보류] 잔고 조회 API 통신에 실패하여 DB 동기화를 건너뜁니다.")
        return

    real_codes = {item['code']: item for item in real_inventory}

    try:
        with DB.get_session() as session:
            # 💡 [ORM 교정 1] SELECT 쿼리 대신 객체 리스트로 가져옵니다.
            db_holdings = session.query(RecommendationHistory).filter_by(status='HOLDING').all()

            for record in db_holdings:
                code = record.stock_code
                name = record.stock_name
                safe_db_qty = record.buy_qty or 0
                    
                if code not in real_codes:
                    print(f"⚠️ [동기화] {name}({code}): 실제 잔고 0주. 상태를 COMPLETED로 강제 변경.")
                    # 💡 [ORM 교정 2] UPDATE 쿼리 대신 파이썬 객체의 속성만 바꿔줍니다.
                    record.status = 'COMPLETED'
                else:
                    real_qty = real_codes[code]['qty']
                    if safe_db_qty != real_qty:
                        print(f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)")
                        # 💡 [ORM 교정 3] 마찬가지로 파이썬 객체 속성만 바꿉니다.
                        record.buy_qty = real_qty
                        
            # 💡 with 블록이 종료될 때, 변경된 객체들이 알아서 DB에 commit() 됩니다!
            
    except Exception as e:
        log_error(f"🚨 DB 동기화 중 에러 발생: {e}")

    print("✅ [데이터 동기화] 완료. 봇 메모리가 실제 계좌와 완벽히 일치합니다.")

# --- [외부 요청용 분석 리포트 (텔레그램 봇 응답용)] ---
def analyze_stock_now(code):
    global KIWOOM_TOKEN, WS_MANAGER
    
    now_time = datetime.now().time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    market_close = datetime.strptime("15:30:00", "%H:%M:%S").time()

    if not (market_open <= now_time <= market_close):
        return f"🌙 현재는 정규장 운영 시간(09:00~15:30)이 아닙니다.\n실시간 종목 분석은 장중에만 이용 가능합니다."

    if not WS_MANAGER: return "⏳ 시스템 초기화 중..."
    WS_MANAGER.subscribe([code])

    try:
        stock_name = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)['Name']
    except:
        stock_name = code

    ws_data = {}
    for _ in range(30):
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        if ws_data and ws_data.get('curr', 0) > 0: break
        time.sleep(0.1)

    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ **{stock_name}**({code}) 호가창 수신 대기 중...\n(거래가 멈춰있거나 일시적인 통신 지연일 수 있습니다.)"

    curr_price = ws_data.get('curr', 0)
    trailing_pct = getattr(TRADING_RULES, 'TRAILING_START_PCT', 3.0)
    target_price = int(curr_price * (1 + (trailing_pct / 100)))
    target_reason = f"기본 시스템 익절선 (+{trailing_pct}%)"

    try:
        df = DB.get_stock_data(code, limit=20)
        if df is not None and len(df) >= 10:
            high_20d = df['High'].max()
            ma20 = df['Close'].mean()
            std20 = df['Close'].std()
            upper_bb = ma20 + (2 * std20)

            chart_resistance = max(high_20d, upper_bb)
            if chart_resistance > curr_price:
                target_price = int(chart_resistance)
                expected_rtn = ((target_price / curr_price) - 1) * 100
                target_reason = f"차트 저항대 도달 (예상 +{expected_rtn:.1f}%)"
            else:
                rally_pct = getattr(TRADING_RULES, 'RALLY_TARGET_PCT', 5.0)
                target_price = int(curr_price * (1 + (rally_pct / 100)))
                target_reason = f"신고가 돌파 랠리 (단기 추세 +{rally_pct}%)"
    except Exception as e:
        log_error(f"⚠️ 목표가 계산 중 에러: {e}")

    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, 0.5, 70)

    return (
        f"🔍 *[{stock_name}]({code}) 실시간 분석*\n"
        f"💰 현재가: `{curr_price:,}원`\n"
        f"{visual}\n"
        f"🎯 1차 목표가: `{target_price:,}원`\n"
        f"   └ 📝 사유: *{target_reason}*\n"
        f"🤖 기계 익절선: `+{trailing_pct}%` (도달 시 트레일링 스탑 가동)\n"
        f"📝 확신지수: `{score:.1f}점`\n"
        f"{conclusion}"
    )

def get_detailed_reason(code):
    global ACTIVE_TARGETS, KIWOOM_TOKEN
    targets = ACTIVE_TARGETS
    target = next((t for t in targets if t['code'] == code), None)

    if not target: return f"🔍 `{code}` 종목은 현재 AI 감시 대상이 아닙니다."

    ws_data = WS_MANAGER.get_latest_data(code)
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ `{code}` 데이터 수신 중..."

    ai_prob = target.get('prob', 0.75)
    radar = SniperRadar(KIWOOM_TOKEN)
    score, details, visual, prices, conclusion, checklist = radar.analyze_signal_integrated(ws_data, ai_prob)

    report = f"🧐 **[{target['name']}] 미진입 사유 분석**\n━━━━━━━━━━━━━━━━━━\n"
    for label, status in checklist.items():
        icon = "✅" if status['pass'] else "❌"
        report += f"{icon} {label}: `{status['val']}`\n"

    buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 80)
    report += f"🎯 **종합 점수:** `{int(score)}점` (매수기준: {buy_threshold}점)\n"
    report += f"📝 **현재 상태:** {conclusion}\n"
    return report

def check_and_run_intraday_scanner(targets, last_scan_time):
    watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
    max_slots = getattr(TRADING_RULES, 'MAX_WATCHING_SLOTS', 5)
    scan_interval = getattr(TRADING_RULES, 'SCAN_INTERVAL_SEC', 1800)

    if watching_count < max_slots and (time.time() - last_scan_time > scan_interval):
        print(f"🔄 [시스템] 감시 슬롯 부족({watching_count}개). 신규 종목을 스캔합니다...")
        try:
            # 🚀 스캐너가 알아서 EventBus로 웹소켓 등록 및 텔레그램 발송을 수행합니다.
            # 스나이퍼는 스캐너를 호출만 하고 결괏값을 메모리에 넣기만 하면 됩니다.
            new_picks = final_ensemble_scanner.run_intraday_scanner(KIWOOM_TOKEN)
            
            if new_picks:
                for np in new_picks:
                    if not any(t['code'] == np['code'] for t in targets):
                        targets.append(np)
                        # 웹소켓 구독은 스캐너가 발행한 "COMMAND_WS_REG" 이벤트에 의해 
                        # WS_MANAGER가 알아서 처리하므로 여기서 중복 호출하지 않아도 됩니다.
            return time.time()
        except Exception as e:
            log_error(f"⚠️ 장중 스캔 중 오류: {e}")
            
    return last_scan_time

# =====================================================================
# 🧠 상태 머신 (State Machine) 핸들러 
# =====================================================================
def handle_watching_state(stock, code, ws_data, admin_id, radar=None, ai_engine=None):
    """
    [WATCHING 상태] 진입 타점 감시 및 AI 교차 검증
    * 변경점: broadcast_callback 파라미터 파괴 -> EventBus 적용
    """
    strategy = stock.get('strategy', 'KOSPI_ML')
    now = datetime.now()
    now_t = now.time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    strategy_start = datetime.strptime("09:05:00", "%H:%M:%S").time()

    # 🛡️ 9시 ~ 9시 5분: 데이터 수집 및 관찰 기간 (진입 금지)
    if market_open <= now_t < strategy_start:
        if now.second % 30 == 0:  # 30초마다 로그
            print(f"📡 [관찰 모드] 주도주 에너지 집계 중... (현재 {len(ACTIVE_TARGETS)}종목 모니터링)")
        return
    
    MIN_PRICE = getattr(TRADING_RULES, 'MIN_PRICE', 5000)
    MAX_SURGE = getattr(TRADING_RULES, 'MAX_SCALP_SURGE_PCT', 20.0) 
    MAX_INTRADAY_SURGE = getattr(TRADING_RULES, 'MAX_INTRADAY_SURGE', 15.0)
    MIN_LIQUIDITY = getattr(TRADING_RULES, 'MIN_SCALP_LIQUIDITY', 300_000_000)

    # 🚀 1. 쿨타임(휴식기) 검사
    if code in cooldowns and time.time() < cooldowns[code]:
        return

    # 🚀 2. 초단타 장 후반 진입 금지 (15:00 이후)
    if strategy == 'SCALPING' and now_t >= datetime.strptime("15:00:00", "%H:%M:%S").time():
        return

    if code in alerted_stocks: return

    curr_price = ws_data.get('curr', 0)
    current_vpw = ws_data.get('v_pw', 0)

    # 🚨 3. 실시간 동전주/저가주 컷오프 (MIN_PRICE 방어막)
    if 0 < curr_price < MIN_PRICE:
        if time.time() % 60 < 1: 
            print(f"🚫 [저가주 방어] {stock['name']} 현재가 {curr_price:,}원. (5,000원 미만 진입 금지)")
        return 

    is_trigger = False
    msg = ""
    ratio = 0.10

    ai_prob = stock.get('prob', getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70))
    buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 80)
    strong_vpw = getattr(TRADING_RULES, 'VPW_STRONG_LIMIT', 120)

    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':
        ratio = getattr(TRADING_RULES, 'INVEST_RATIO_SCALPING', 0.05)
        
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        fluctuation = float(ws_data.get('fluctuation', 0.0)) 
        open_price = float(ws_data.get('open', curr_price))

        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price

        # 🚨 [이중 방어막] 과매수 위험 차단
        if fluctuation >= MAX_SURGE or intraday_surge >= MAX_INTRADAY_SURGE:
            if time.time() % 60 < 1:
                print(f"🚫 [SCALP 제외] {stock['name']} | 전일대비: +{fluctuation}%, 시가대비: +{intraday_surge:.1f}% (과매수 위험)")
            return 
        
        # 💡 [기본 조건 검사] 수급과 호가잔량이 최소 기준을 넘어야 함
        if current_vpw >= getattr(TRADING_RULES, 'VPW_SCALP_LIMIT', 120) and liquidity_value >= MIN_LIQUIDITY:
            
            scanner_price = stock.get('buy_price', 0)
            if scanner_price > 0:
                gap_pct = (curr_price - scanner_price) / scanner_price * 100
                if gap_pct >= 1.5: 
                    if code not in cooldowns:
                        print(f"⚠️ [{stock['name']}] 포착가 대비 너무 오름 (갭 +{gap_pct:.1f}%). 추격매수 포기.")
                        cooldowns[code] = time.time() + 1200
                    return
                
            # =========================================================
            # 💎 4. [핵심] AI 감시 종목 VIP 필터링 & 타점 계산
            # =========================================================
            # 💡 이전 AI 점수를 가져와서 일단 1차적으로 타점을 계산해 봅니다.
            current_ai_score = stock.get('rt_ai_prob', 0.5) * 100 
            
            target_buy_price, used_drop_pct = radar.get_smart_target_price(
                curr_price, 
                v_pw=current_vpw, 
                ai_score=current_ai_score,
                ask_tot=ask_tot, # 👈 추가됨 (위에서 ws_data.get('ask_tot', 0)로 이미 구해둠)
                bid_tot=bid_tot  # 👈 추가됨
            )

            global LAST_AI_CALL_TIMES
            last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
            time_elapsed = time.time() - last_ai_time
            
            # 💡 [VIP 필터링] 현재가가 목표 매수가(target_buy_price)에 1.5% 이내로 접근했는가?
            # (즉, 호가창을 밑으로 조금만 더 내리면 체결될 것 같은 임박한 상황인가?)
            is_vip_target = (target_buy_price > 0) and (curr_price <= target_buy_price * 1.015)

            # 💡 VIP 종목이면서 쿨타임(10초)이 지났을 때만 AI 합의체 개입 (실시간 타점 검증)
            if ai_engine and radar and is_vip_target and (time_elapsed > 10.0):
            
                recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=5)
                
                if ws_data.get('orderbook') and recent_ticks:
                    # 💡 Non-blocking 호출
                    ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)
                    
                    action = ai_decision.get('action', 'WAIT')
                    ai_score = ai_decision.get('score', 50)  
                    reason = ai_decision.get('reason', '사유 없음')
                    
                    # 50점(Bypass/Error)이 아닐 때만 점수 갱신
                    if ai_score != 50:
                        stock['rt_ai_prob'] = ai_score / 100.0
                        current_ai_score = ai_score # 로컬 변수도 즉시 업데이트
                        print(f"💎 [VIP AI 분석: {stock['name']}] {action} | 점수: {ai_score}점 | {reason}")
                    
                    LAST_AI_CALL_TIMES[code] = time.time()

                    # 텔레그램 발송 (AI가 확실한 신호를 주었을 때만)
                    if action in ["BUY", "DROP"] and ai_score != 50:
                        ai_msg = f"🤖 <b>[VIP 종목 실시간 분석]</b>\n"
                        ai_msg += f"🎯 종목: {stock['name']}\n"
                        ai_msg += f"⚡ 행동: <b>{action} ({ai_score}점)</b>\n"
                        ai_msg += f"🧠 사유: {reason}"
                        
                        target_audience = 'VIP_ALL' if liquidity_value >= getattr(TRADING_RULES, 'VIP_LIQUIDITY_THRESHOLD', 500_000_000) else 'ADMIN_ONLY'
                        event_bus.publish('TELEGRAM_BROADCAST', {'message': ai_msg, 'audience': target_audience, 'parse_mode': 'HTML'})
            
            # =========================================================
            # 🚨 5. AI 거부권 및 최종 매수 대기열(그물망) 투척
            # =========================================================
            if current_ai_score <= 40:
                if time.time() - last_ai_time < 1.0: 
                    print(f"🚫 [AI 매수 차단] {stock['name']} 진입 불가! (AI 점수: {current_ai_score}점)")
                cooldowns[code] = time.time() + 180 
                return  
            
            # 최신 AI 점수를 반영하여 목표가 재계산 (방금 AI 점수가 갱신되었을 수 있으므로)
            final_target_buy_price, final_used_drop_pct = radar.get_smart_target_price(
                curr_price, 
                v_pw=current_vpw, 
                ai_score=current_ai_score 
            )

            stock['target_buy_price'] = final_target_buy_price
            is_trigger = True
            
            msg = (f"⚡ **[{stock['name']}]({code}) 초단타(SCALP) 그물망 투척!**\n"
                   f"현재가: `{curr_price:,}원` ➡️ **매수대기: `{final_target_buy_price:,}원` (-{final_used_drop_pct:.1f}% 눌림목)**\n"
                   f"호가잔량대금: `{liquidity_value / 100_000_000:.1f}억` | 수급강도: `{current_vpw:.1f}%`")
            
            stock['msg_audience'] = 'VIP_ALL' if liquidity_value >= getattr(TRADING_RULES, 'VIP_LIQUIDITY_THRESHOLD', 500_000_000) else 'ADMIN_ONLY'
      
    # 2️⃣ 코스닥 우량주 스윙 (KOSDAQ_ML) 전략
    elif strategy == 'KOSDAQ_ML':
        ratio = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ', 0.10)
        score, details, visual, p, conclusion, checklist = radar.analyze_signal_integrated(ws_data, ai_prob)

        v_pw_limit = getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105) if ai_prob >= getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70) else strong_vpw
        is_shooting = current_vpw >= v_pw_limit

        if (score >= buy_threshold or is_shooting) and current_vpw >= getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105):
            is_trigger = True
            msg = (f"🚀 **[{stock['name']}]({code}) 코스닥(KOSDAQ) 스나이퍼 포착!**\n"
                   f"현재가: `{curr_price:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{current_vpw:.1f}%` {visual}")

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        ratio = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI', 0.20)
        ai_prob = stock.get('prob', getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.8))
        score, details, visual, p, conclusion, checklist = radar.analyze_signal_integrated(ws_data, ai_prob)

        strong_vpw = getattr(TRADING_RULES, 'VPW_STRONG_LIMIT', 115)
        buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 80)
        v_pw_limit = 100 if ai_prob >= getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.8) else strong_vpw
        is_shooting = current_vpw >= v_pw_limit

        if (score >= buy_threshold or is_shooting) and current_vpw >= 103:
            is_trigger = True
            msg = (f"🚀 **[{stock['name']}]({code}) 스나이퍼 포착! (스윙)**\n"
                   f"현재가: `{curr_price:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{current_vpw:.1f}%` {visual}")

    # ==========================================
    # 🎯 매수 실행 공통 로직
    # ==========================================
    if is_trigger:
        if not admin_id:
            print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID가 없습니다.")
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        real_buy_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio)

        if real_buy_qty <= 0:
            print(f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다. (자금 부족으로 20분 제외)")
            # 💡 [교정] 0주일 때도 쿨타임을 적용해 무한 루프 차단
            cooldowns[code] = time.time() + 1200 
            return

        # 🚀 [상호 검증 반영] 전략별 주문 세팅
        if strategy == 'SCALPING':
            order_type_code = "00"  # 지정가
            final_price = stock.get('target_buy_price', curr_price)
        else:
            order_type_code = "6"  # 스윙은 최유리지정가
            final_price = 0

        # 주문 발송
        res = kiwoom_orders.send_buy_order_market(
            code=code, qty=real_buy_qty, token=KIWOOM_TOKEN,
            order_type=order_type_code, price=final_price
        )

        is_success = False
        ord_no = ''

        # 💡 [핵심 교정] 응답값을 정확히 분석하여 성공 여부 판단
        if isinstance(res, dict):
            if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            elif strategy == 'SCALPING':
                cooldowns[code] = time.time() + 1200
        elif res:
            is_success = True

        # 💡 [핵심 교정] 주문이 "정상 접수" 되었을 때만 메모리와 DB 상태를 'BUY_ORDERED'로 변경!
        if is_success:
            print(f"🛒 [{stock['name']}] 매수 주문 전송 완료. 체결 영수증 대기 중...")
            # 📢 EventBus 퍼블리싱 (매수 주문 알림)
            event_bus.publish('TELEGRAM_BROADCAST', {'message': msg, 'audience': stock.get('msg_audience', 'VIP_ALL')})
            alerted_stocks.add(code)
            
            stock.update({'status': 'BUY_ORDERED', 'order_price': final_price if final_price > 0 else curr_price, 'buy_qty': real_buy_qty, 'odno': ord_no, 'order_time': time.time()})
            highest_prices[code] = curr_price
            try:
                with DB.get_session() as session:
                    # 1. 수정할 객체를 조회 (WATCHING 상태인 녀석만)
                    record = session.query(RecommendationHistory).filter_by(
                        stock_code=code, 
                        status='WATCHING'
                    ).first()
                    
                    # 2. 파이썬 객체의 속성을 변경하면 ORM이 알아서 UPDATE 쿼리를 날려줍니다.
                    if record:
                        record.status = 'BUY_ORDERED'
                        record.buy_price = final_price if final_price > 0 else curr_price
                        
                    # with 블록이 끝나면 자동으로 commit() 됩니다.
            except Exception as e:
                kiwoom_utils.log_error(f"🚨 [DB 에러] {stock['name']} 상태 업데이트 실패: {e}")
                print(f"🚨 [DB 에러] {stock['name']} 상태 업데이트 실패: {e}")

def handle_holding_state(stock, code, ws_data, admin_id, market_regime, radar=None, ai_engine=None):
    """
    [HOLDING 상태] 보유 종목 익절/손절 감시 및 AI 조기 개입
    * 변경점: broadcast_callback 파라미터 파괴 -> EventBus 적용
    """
    curr_p = ws_data['curr']
    buy_p = stock.get('buy_price', 0)
    if buy_p <= 0: return

    if code not in highest_prices: highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)

    profit_rate = (curr_p - buy_p) / buy_p * 100
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100

    strategy = stock.get('strategy', 'KOSPI_ML')
    is_sell_signal = False
    reason = ""

    now_t = datetime.now().time()

    # =========================================================
    # 🤖 [AI 보유 종목 실시간 감시] 문지기(Gatekeeper) 적용
    # =========================================================
    global LAST_AI_CALL_TIMES
    last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
    current_ai_score = stock.get('rt_ai_prob', 0.8) * 100 
    
    last_ai_profit = stock.get('last_ai_profit', profit_rate)
    price_change = abs(profit_rate - last_ai_profit)
    time_elapsed = time.time() - last_ai_time

    # 💡 [보유 종목 문지기] 5초 쿨타임 + (수익률 0.3% 변동 OR 30초 경과) 시에만 AI 호출
    if strategy == 'SCALPING' and ai_engine and radar and time_elapsed > 5.0 and (price_change >= 0.3 or time_elapsed > 30.0):
        
        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=5)
        
        if ws_data.get('orderbook') and recent_ticks:
            ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)
            current_ai_score = ai_decision.get('score', 50)
            
            stock['rt_ai_prob'] = current_ai_score / 100.0
            LAST_AI_CALL_TIMES[code] = time.time()
            stock['last_ai_profit'] = profit_rate 
            
            print(f"👁️ [AI 보유감시: {stock['name']}] 수익: {profit_rate:+.2f}% | 변동: {price_change:.2f}% | AI점수: {current_ai_score}점")
    # =========================================================

    # ==========================================
    # 🚀 [멀티 전략] 보유 종목 청산 분기 처리
    # ==========================================
    # 1️⃣ 초단타 (SCALPING) 전략 (AI 매도 로직 결합)
    if strategy == 'SCALPING':
        # --- [STEP 1] 보유 시간(held_time_min) 계산 ---
        held_time_min = 0
        if 'order_time' in stock:
            # 메모리에 order_time이 있을 때 (가장 정확)
            held_time_min = (time.time() - stock['order_time']) / 60
        elif 'buy_time' in stock and stock['buy_time']:
            # DB 등에서 가져온 문자열 포맷일 때
            try:
                b_time = datetime.strptime(stock['buy_time'], '%H:%M:%S').time()
                b_dt = datetime.combine(datetime.now().date(), b_time)
                held_time_min = (datetime.now() - b_dt).total_seconds() / 60
            except:
                pass

        # --- [STEP 2] 익절/손절 기준선 및 하락폭(Drawdown) 설정 ---
        target_pct = getattr(TRADING_RULES, 'SCALP_TARGET', 2.0)
        base_stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -2.5)
        scalp_trailing_limit = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT', 0.5)
        drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100

        # AI 점수에 따른 동적 파라미터 분기
        if current_ai_score >= 75:
            dynamic_stop_pct = base_stop_pct - 1.0  # 수급 폭발 시 -3.5%까지 허용
            current_trailing_limit = scalp_trailing_limit
        else:
            dynamic_stop_pct = base_stop_pct        # 평소 -2.5%
            current_trailing_limit = 0.3            # 보통일 땐 더 보수적으로 관리

        # --- [STEP 3] 매도 판단 실행 (우선순위 순서) ---
        
        # 1. 하드 리밋 (최우선: 물리적 손절선 이탈)
        if profit_rate <= dynamic_stop_pct:
            is_sell_signal = True
            reason = f"🔪 무호흡 칼손절 ({dynamic_stop_pct}%) [AI: {current_ai_score}]"

        # 2. 트레일링 스탑 (수익 보존)
        elif profit_rate >= 0.3:
            if profit_rate >= target_pct and drawdown >= current_trailing_limit:
                is_sell_signal = True
                reason = f"🔥 [AI 트레일링] 목표달성 후 고점대비 -{drawdown:.2f}% 밀림"
            elif drawdown >= 0.8:
                is_sell_signal = True
                reason = f"⚠️ [심리적 고점] 수익권 고점 대비 급락 (-{drawdown:.2f}%)"

        # 3. AI 지능형 조기 개입
        if not is_sell_signal:
            if current_ai_score < 50 and profit_rate >= 0.5:
                is_sell_signal = True
                reason = f"🤖 AI 모멘텀 둔화 ({current_ai_score}점). 조기 익절 (+{profit_rate:.2f}%)"
            elif current_ai_score <= 35 and profit_rate < 0:
                is_sell_signal = True
                reason = f"🚨 AI 하방 리스크 포착 ({current_ai_score}점). 조기 손절 ({profit_rate:.2f}%)"

        # 4. 시간 초과 및 장 마감 (가장 하위 우선순위)
        if not is_sell_signal:
            if held_time_min >= getattr(TRADING_RULES, 'SCALP_TIME_LIMIT_MIN', 30) and profit_rate >= getattr(TRADING_RULES, 'MIN_FEE_COVER', 0.1):
                is_sell_signal = True
                reason = f"⏱️ {getattr(TRADING_RULES, 'SCALP_TIME_LIMIT_MIN', 30)}분 타임아웃 (순환매 우선)"
            elif now_t >= datetime.strptime("15:15:00", "%H:%M:%S").time():
                is_sell_signal = True
                reason = "⏰ 장 마감 전 현금화"

    # 2️⃣ 코스닥 AI 스윙 (KOSDAQ_ML) 전용 전략
    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= getattr(TRADING_RULES, 'KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
        except:
            pass

        if not is_sell_signal and peak_profit >= getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= 1.0:
                is_sell_signal = True
                reason = f"🏆 KOSDAQ 트레일링 익절 (+{getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0)}% 돌파 후 하락)"

        elif not is_sell_signal and profit_rate <= getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0)}%)"

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        pos_tag = stock.get('position_tag', 'MIDDLE')
        if pos_tag == 'BREAKOUT':
            current_stop_loss = TRADING_RULES.STOP_LOSS_BREAKOUT
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = TRADING_RULES.STOP_LOSS_BOTTOM
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = TRADING_RULES.STOP_LOSS_BULL if market_regime == 'BULL' else TRADING_RULES.STOP_LOSS_BEAR
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= TRADING_RULES.HOLDING_DAYS:
                is_sell_signal = True
                reason = f"⏳ {TRADING_RULES.HOLDING_DAYS}일 스윙 보유 만료"
        except:
            pass

        if not is_sell_signal and peak_profit >= TRADING_RULES.TRAILING_START_PCT:
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= TRADING_RULES.TRAILING_DRAWDOWN_PCT:
                is_sell_signal = True
                reason = f"🏆 가변익절 (+{TRADING_RULES.TRAILING_START_PCT}% 도달 후 하락)"
            elif profit_rate <= TRADING_RULES.MIN_PROFIT_PRESERVE:
                is_sell_signal = True
                reason = f"수익 보존 (최소 {TRADING_RULES.MIN_PROFIT_PRESERVE}%)"

        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"

    # ==========================================
    # 🎯 매도 실행 공통 로직 (Smart Sell 반영 버전)
    # ==========================================
    if is_sell_signal:
        # 1. 매매 성격 판별 (PROFIT vs LOSS)
        # profit_rate가 0보다 크면 익절(PROFIT), 작거나 같으면 손절(LOSS)로 분류
        sell_reason_type = 'PROFIT' if profit_rate > 0 else 'LOSS'
        
        sign = "🎊 [익절 주문]" if sell_reason_type == 'PROFIT' else "📉 [손절 주문]"
        msg = (f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n사유: `{reason}`\n"
               f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)")

        is_success = False
        buy_qty = stock.get('buy_qty', 0)

        if not admin_id:
            print(f"🚨 [매도실패] {stock['name']}: 관리자 ID가 없습니다.")
        elif int(buy_qty) <= 0:
            print(f"🚨 [매도실패] {stock['name']}: 수량이 0주입니다! 강제 완료(COMPLETED) 처리.")
            try:
                with DB.get_session() as session:
                    # 💡 [ORM Bulk Update] code가 일치하는 레코드의 status를 한 번에 업데이트합니다.
                    session.query(RecommendationHistory).filter_by(stock_code=code).update({"status": "COMPLETED"})
                    # with 블록 종료 시 자동 commit
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} COMPLETED 전환 실패: {e}")
                log_error(f"🚨 [DB 에러] {stock['name']} COMPLETED 전환 실패: {e}")
            
            stock['status'] = 'COMPLETED'

        else:
            # 💡 [핵심 방어 1] 장부 잠금
            try:
                with DB.get_session() as session:
                    # 💡 [ORM 조건부 Update] code가 일치하고 status가 'HOLDING'인 녀석만 타겟팅합니다.
                    session.query(RecommendationHistory).filter_by(
                        stock_code=code, 
                        status='HOLDING'
                    ).update({"status": "SELL_ORDERED"})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")
                log_error(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")

            stock['status'] = 'SELL_ORDERED'
            
            try: highest_prices.pop(code, None)
            except: pass

            # 💡 [핵심 방어 2] 스마트 매도 호출 (슬리피지 방어 가동!)
            # ws_data를 함께 넘겨서 호가창을 분석하게 합니다.
            res = kiwoom_orders.send_smart_sell_order(
                code=code, 
                qty=int(buy_qty), 
                token=KIWOOM_TOKEN, 
                ws_data=ws_data,      # 호가창 분석용
                reason_type=sell_reason_type
            )
            
            if isinstance(res, dict):
                rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
                if rt_cd == '0':
                    is_success = True
                else:
                    print(f"❌ [매도거절] {stock['name']}: {res.get('return_msg')}")
            elif res:
                is_success = True

            if is_success:
                print(f"✅ [{stock['name']}] 매도 주문 전송 완료. 체결 영수증 처리 대기 중...")
                # 📢 EventBus 퍼블리싱 (매도 알림)
                event_bus.publish('TELEGRAM_BROADCAST', {'message': msg})

                # 스캘핑 쿨타임 (기존 로직 유지)
                if strategy in ['SCALPING', 'SCALP'] and now_t < datetime.strptime("15:15:00", "%H:%M:%S").time():
                    cooldowns[code] = time.time() + 1200
                    try: alerted_stocks.discard(code)
                    except: pass
                    print(f"♻️ [{stock['name']}] 스캘핑 청산 완료 후 20분 쿨타임 진입.")
            else:
                # 💡 [핵심 교정] 에러 메시지를 읽고 영구 탈출(COMPLETED)할지, 복구(HOLDING)할지 결정합니다.
                err_msg = res.get('return_msg', '') if isinstance(res, dict) else ''
                
                # 1. 분기 처리를 통해 목표 상태(new_status)를 먼저 결정합니다.
                if '매도가능수량' in err_msg:
                    print(f"🚨 [{stock['name']}] 잔고 0주(이미 매도됨). 무한루프를 막기 위해 COMPLETED로 강제 전환합니다.")
                    new_status = 'COMPLETED'
                else:
                    print(f"🚨 [{stock['name']}] 일시적 매도 전송 실패! 상태를 다시 HOLDING으로 원상복구합니다.")
                    new_status = 'HOLDING'

                # 2. 결정된 상태로 메모리(스나이퍼 루프)를 업데이트합니다.
                stock['status'] = new_status

                # 3. 전역 DB 객체를 사용하여 단일 트랜잭션으로 상태를 일괄 업데이트(Bulk Update) 합니다.
                try:
                    with DB.get_session() as session:
                        session.query(RecommendationHistory).filter_by(
                            stock_code=code
                        ).update({"status": new_status})
                        # with 블록이 끝나면 자동으로 commit() 됩니다.
                except Exception as e:
                    print(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")
                    log_error(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")

def handle_buy_ordered_state(stock, code):
    """
    주문 전송 후(BUY_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 로직을 호출합니다.
    """
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time
    
    strategy = stock.get('strategy', 'KOSPI_ML')
    # 💡 [개선] AI 예약 주문(target_buy_price가 명시된 경우)은 20분(1200초) 대기
    if stock.get('target_buy_price', 0) > 0:
        timeout_sec = getattr(TRADING_RULES, 'RESERVE_TIMEOUT_SEC', 1200) # 20분
    else:
        # 일반 장중 추격 매수 타임아웃
        timeout_sec = 20 if strategy == 'SCALPING' else getattr(TRADING_RULES, 'ORDER_TIMEOUT_SEC', 30)
        
    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 매수 대기 {timeout_sec}초 초과. 취소 절차 진입.")
        orig_ord_no = stock.get('odno')
        db = DBManager()

        # [CASE 1] 원주문번호가 없는 경우 (예외적 상황)
        if not orig_ord_no:
            # 1. 메모리(스나이퍼 루프) 상태 복구
            stock['status'] = 'WATCHING'
            stock.pop('order_time', None)
            
            # 2. 전역 DB 객체를 사용하여 단일 트랜잭션으로 상태와 매수가를 일괄 업데이트
            try:
                with DB.get_session() as session:
                    # 💡 [ORM Bulk Update] 상태(status)와 매수가(buy_price) 두 개의 컬럼을 한 번에 업데이트합니다.
                    session.query(RecommendationHistory).filter_by(
                        stock_code=code, 
                        status='BUY_ORDERED'
                    ).update({
                        "status": "WATCHING", 
                        "buy_price": 0
                    })
                    # with 블록이 끝나면 자동으로 commit() 됩니다.
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 매수 타임아웃 복구(WATCHING) 실패: {e}")
                
            return

        # [CASE 2] 정상적인 취소 로직 호출
        process_order_cancellation(stock, code, orig_ord_no, db, strategy)

def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    """
    미체결 주문의 실제 취소 처리와 DB/메모리 청소를 담당합니다.
    """
    # 1. 취소 주문 전송
    res = kiwoom_orders.send_cancel_order(
        code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0
    )

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    # 2. 취소 성공 시: 상태 초기화 및 쿨타임 적용
    if is_success:
        print(f"✅ [{stock['name']}] 미체결 매수 취소 성공. 감시 상태로 복귀합니다.")
        stock['status'] = 'WATCHING'
        stock.pop('odno', None)
        stock.pop('order_time', None)
        try: highest_prices.pop(code, None)
        except: pass
        
        # DB 업데이트 (영구 상태 반영) - ORM 적용
        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(
                    stock_code=code, 
                    status='BUY_ORDERED'
                ).update({
                    "status": "WATCHING", 
                    "buy_price": 0
                })
                # with 블록 종료 시 자동 commit
        except Exception as e:
            print(f"🚨 [DB 에러] {stock['name']} 매수 취소 후 WATCHING 복구 실패: {e}")

        if strategy == 'SCALPING':
            try: alerted_stocks.discard(code)
            except: pass
            cooldowns[code] = time.time() + 1200 # 20분간 휴식
            print(f"♻️ [{stock['name']}] 스캘핑 취소 완료. 20분 쿨타임 진입.")
        return True

    # 3. 취소 실패 시: 이미 체결되었는지 확인
    else:
        print(f"🚨 [{stock['name']}] 매수 취소 실패! (사유: {err_msg})")
        if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음']):
            print(f"💡 [{stock['name']}] 이미 전량 체결된 것으로 판단. HOLDING으로 강제 전환.")
            stock['status'] = 'HOLDING'
            
            # DB 업데이트 (영구 상태 반영) - ORM 적용
            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(
                        stock_code=code, 
                        status='BUY_ORDERED'
                    ).update({
                        "status": "HOLDING"
                    })
                    # with 블록 종료 시 자동 commit
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 매수 취소 실패 후 HOLDING 전환 실패: {e}")
                
        return False

# ==========================================
# 💡 실시간 체결 영수증 처리 (콜백 함수)
# ==========================================
def handle_real_execution(exec_data):
    """
    웹소켓에서 주문 체결(00) 통보가 오면 이 함수가 즉시 실행됩니다.
    실제 체결가를 DB에 덮어쓰고, 스나이퍼의 메모리를 변경합니다.
    """
    code = exec_data['code']
    exec_type = exec_data['type']
    exec_price = exec_data['price']
    
    now_t = datetime.now().time()
    
    # ==========================================
    # 1️⃣ DB 상태 업데이트 (영구 기록) - ORM 적용
    # ==========================================
    if exec_type == 'BUY':
        try:
            with DB.get_session() as session:
                # 🎯 실제 매수 체결: 상태가 WATCHING 이나 BUY_ORDERED 인 녀석을 HOLDING 으로 변경
                session.query(RecommendationHistory).filter(
                    RecommendationHistory.stock_code == code,
                    RecommendationHistory.status.in_(['WATCHING', 'BUY_ORDERED'])
                ).update({
                    "buy_price": exec_price,
                    "status": "HOLDING"
                }, synchronize_session=False)
                # with 블록 종료 시 자동 commit
            print(f"✅ [영수증 확인] {code} 실제 매수 체결가 {exec_price:,}원 DB 반영 완료!")
        except Exception as e:
            print(f"🚨 [DB 에러] {code} BUY 체결 영수증 처리 중 에러: {e}")
            log_error(f"🚨 [DB 에러] {code} BUY 체결 영수증 처리 중 에러: {e}")
            
    elif exec_type == 'SELL':
        try:
            with DB.get_session() as session:
                # 🏁 실제 매도 체결: 매수가(buy_price)를 가져오기 위해 객체를 SELECT 합니다.
                record = session.query(RecommendationHistory).filter(
                    RecommendationHistory.stock_code == code,
                    RecommendationHistory.status.in_(['HOLDING', 'SELL_ORDERED'])
                ).first()

                if record and record.buy_price > 0:
                    buy_price = record.buy_price
                    # 실제 수익률 계산 (슬리피지 모두 반영됨)
                    profit_rate = round(((exec_price - buy_price) / buy_price) * 100, 2)
                    strategy = record.strategy

                    # 💡 [핵심 1] ORM 객체 속성 변경으로 'COMPLETED' 기록 영구 보존
                    record.status = 'COMPLETED'
                    record.sell_price = exec_price  # (모델에 필드가 있다면)
                    record.profit_rate = profit_rate # (모델에 필드가 있다면)
                    
                    print(f"🎉 [매매 완료] {code} 실매도가 {exec_price:,}원 / 최종 수익률: {profit_rate}% (기록 보존 완료)")

                    # 💡 [핵심 2] 스캘핑 부활 조건 (새로운 레코드 INSERT)
                    is_scalp_revive = (strategy == 'SCALPING') and (now_t < datetime.strptime("15:15:00", "%H:%M:%S").time())
                    
                    if is_scalp_revive:
                        today = datetime.now().strftime('%Y-%m-%d')
                        stock_info = next((s for s in ACTIVE_TARGETS if s['code'] == code), None)
                        
                        if stock_info:
                            name = stock_info.get('name', code)
                            prob = stock_info.get('prob', 0.8)
                            
                            # 완전히 새로운 레코드를 ORM 객체로 생성하여 DB에 추가 (INSERT)
                            new_record = RecommendationHistory(
                                rec_date=today, 
                                stock_code=code, 
                                stock_name=name, 
                                status='WATCHING',
                                strategy='SCALPING',
                                trade_type='SCALP', # 추가
                                prob=prob
                            )
                            session.add(new_record)
                            print(f"♻️ [스캘핑 재진입 준비] {name}({code}) 새로운 매매를 위해 DB에 신규 감시(WATCHING) 등록!")
                            
                # with 블록 종료 시 UPDATE와 INSERT가 한 번에 commit 됩니다.
        except Exception as e:
            print(f"🚨 [DB 에러] {code} 매도 체결 영수증 처리 중 에러: {e}")
            log_error(f"🚨 [DB 에러] {code} 매도 체결 영수증 처리 중 에러: {e}")

    # ==========================================
    # 2️⃣ 스나이퍼 메모리(ACTIVE_TARGETS) 즉시 동기화
    # ==========================================
    
    for stock in ACTIVE_TARGETS:
        if stock['code'] == code:
            if exec_type == 'BUY':
                stock['status'] = 'HOLDING'
                stock['buy_price'] = exec_price  # 🎯 진짜 체결가로 메모리 업데이트!
            
            elif exec_type == 'SELL':
                strategy = stock.get('strategy', 'KOSPI_ML')
                
                # 스캘핑 부활 조건 검사 (DB 로직과 동일)
                if strategy == 'SCALPING' and now_t < datetime.strptime("15:15:00", "%H:%M:%S").time():
                    stock['status'] = 'WATCHING'
                    stock['buy_price'] = 0
                    stock['buy_qty'] = 0
                else:
                    stock['status'] = 'COMPLETED'
            break

# ==========================================
# 💡 09:05 주도주 분석, 리포트 발송, 매수 예약 주문을 일괄 처리
# ==========================================        
def execute_morning_strategy_batch(targets, ws_manager, radar, ai_engine):
    """
    [v13.0] 09:05 주도주 분석, 리포트 발송, 매수 예약 주문을 일괄 처리합니다.
    * 변경점: broadcast_callback 파라미터 파괴 -> EventBus 적용
    * 변경점: db 파라미터 파괴 -> 전역 DB 및 ORM 적용
    """
    print("🤖 [전략 집행] 09:05 주도주 정렬 및 AI 예약 매매를 시작합니다.")
    
    # 1. 수급 기반 우선순위 재정렬
    for stock in targets:
        ws_data = ws_manager.get_latest_data(stock['code'])
        stock['priority_score'] = radar.calculate_market_leader_score(ws_data)
    
    targets.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    top_3 = targets[:3]
    
    # 2. 통합 리포트 작성을 위한 변수 초기화
    full_report = "🚀 **[AI 주도주 TOP 3 정밀 분석]**\n"
    full_report += f"📅 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    full_report += "━━━━━━━━━━━━━━━━━━\n\n"

    for i, s in enumerate(top_3):
        code = s['code']
        ws_data = ws_manager.get_latest_data(code)
        ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=5)
        
        # AI 분석 호출 (블로킹 구간 - 향후 비동기 분리 권장)
        ai_json_str = ai_engine.analyze_morning_leader(s['name'], ws_data, ticks, candles)
        
        try:
            import json
            res = json.loads(ai_json_str)
            raw_price = str(res.get('target_price', '0'))
            clean_price = raw_price.replace(',', '').replace('원', '').replace(' ', '').strip()
            ai_price = int(clean_price) if clean_price.isdigit() else 0
            
            # 리포트 텍스트 조립
            full_report += f"📍 **{i+1}위. {s['name']}** ({code})\n"
            full_report += f"💬 `{res.get('one_liner', '분석 중...')}`\n"
            full_report += f"📈 패턴: **{res.get('pattern', '-')}**\n"
            full_report += f"🎯 권장타점: `{res.get('target_price', '-')}원` 부근\n"
            full_report += f"⚠️ 리스크: {res.get('risk_factor', '-')}\n"
            full_report += "━━━━━━━━━━━━━━━━━━\n"

            # 🎯 [핵심] 실제 매수 예약 주문 실행
            # 🎯 [핵심 방어] 목표가가 0원(AI가 판단을 보류했거나 포맷이 깨짐)이면 주문을 넣지 않습니다.
            if ai_price > 0:
                deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
                order_res = kiwoom_orders.reserve_buy_order_ai(
                    code=code,
                    ai_target_price=ai_price,
                    deposit=deposit,
                    token=KIWOOM_TOKEN
                )

            # 주문 성공 시 상태 업데이트 (ORM 적용)
            if order_res:
                # 1. 스나이퍼 메모리 즉시 갱신
                s.update({
                    'status': 'BUY_ORDERED',
                    'target_buy_price': ai_price,
                    'order_time': time.time()
                })
                
                # 2. DB 상태 영구 기록 (ORM 단일 트랜잭션)
                try:
                    with DB.get_session() as session:
                        session.query(RecommendationHistory).filter_by(
                            stock_code=code
                        ).update({
                            "status": "BUY_ORDERED",
                            "buy_price": ai_price
                        })
                except Exception as e:
                    print(f"🚨 [DB 에러] {s['name']} 아침 예약매수 DB 업데이트 실패: {e}")
                    log_error(f"🚨 [DB 에러] {s['name']} 아침 예약매수 DB 업데이트 실패: {e}")
            else:
                print(f"⚠️ [{s['name']}] AI 타점 산출 보류 (응답: '{raw_price}'). 매수 예약을 건너뜁니다.")

        except Exception as e:
            print(f"❌ {s['name']} 전략 집행 중 에러: {e}")
            log_error(f"❌ {s['name']} 전략 집행 중 에러: {e}")

    # 최종 리포트 발송 (EventBus 적용)
    event_bus.publish('TELEGRAM_BROADCAST', {'message': full_report})
    print("✅ 09:05 전략 배치 작업이 완료되었습니다.")

# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (Phase 3: Event-Driven & 비동기 아키텍처 완전 적용)
# ==============================================================================
def run_sniper(is_test_mode=False):
    global KIWOOM_TOKEN, WS_MANAGER, ACTIVE_TARGETS

    run_sniper.morning_report_done = False  # 함수 속성으로 아침 보고 완료 여부 추적

    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V12.2 멀티 엔진 가동 (관리자: {admin_id})")

    is_open, reason = kiwoom_utils.is_trading_day()
    if not is_test_mode and not is_open:
        msg = f"🛑 오늘은 {reason} 휴장일이므로 스나이퍼 매매 엔진을 가동하지 않습니다."
        print(msg)
        # 📢 [콜백 파괴] EventBus 퍼블리싱으로 대체
        event_bus.publish('TELEGRAM_BROADCAST', {'message': msg})
        return

    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        log_error("❌ 토큰 발급 실패로 엔진을 중단합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [시스템 에러] 토큰 발급 실패로 엔진을 중단합니다."}) # 이벤트 발행
        return
    
    radar = SniperRadar(KIWOOM_TOKEN)
    sync_balance_with_db()
    # 1. 💡 콜백 파라미터를 완전히 제거하여 결합도를 낮춥니다.
    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)

    # 2. 💡 대신, EventBus에 수신기를 등록합니다. 
    # (웹소켓이 'ORDER_EXECUTED' 이벤트를 허공에 외치면 스나이퍼가 알아서 이 함수를 실행합니다)
    event_bus.subscribe('ORDER_EXECUTED', handle_real_execution)
    
    WS_MANAGER.start()
    time.sleep(2)

    # ==========================================
    # 🤖 [신규] 제미나이 엔진 가동
    # ==========================================
    # 1. CONF에서 GEMINI_API_KEY 관련 값들만 추출
    # GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3 등을 모두 가져옵니다.
    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]
    
    # 2. 추출된 키 리스트가 비어있는지 확인 후 엔진 생성
    if not api_keys:
        kiwoom_utils.log_error("❌ 제미나이 키 발급 실패로 엔진을 중단합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [시스템 에러] 제미나이 키 발급 실패로 엔진을 중단합니다."})
    else:
        ai_engine = GeminiSniperEngine(api_keys=api_keys)
        print(f"🤖 제미나이 AI 엔진이 {len(api_keys)}개의 API 키로 가동됩니다.")

    # 💡 DB에서 가져온 타겟을 전역 변수에 연결합니다.
    ACTIVE_TARGETS = DB.get_active_targets()
    targets = ACTIVE_TARGETS  # targets는 ACTIVE_TARGETS의 별칭이 되어 동기화됨
    last_scan_time = time.time()

    # 🚀 [핵심] 외부 스캐너가 DB에 밀어넣은 신규 종목을 감지하기 위한 타이머
    last_db_poll_time = time.time()

    current_market_regime = radar.get_market_regime(KIWOOM_TOKEN)
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다.")

    target_codes = [t['code'] for t in targets]
    event_bus.publish("COMMAND_WS_REG", {"codes": target_codes})
    last_msg_min = -1

    try:
        while True:
            # 💡 [신규 추가] 'restart.flag' 파일이 생성되었는지 확인
            if os.path.exists("restart.flag"):
                print("🔄 [우아한 종료] 재시작 깃발을 확인했습니다. 시스템을 안전하게 정지합니다.")
                event_bus.publish('TELEGRAM_BROADCAST', {'message': "🛑 스나이퍼 엔진이 하던 작업을 마치고 우아하게 재시작됩니다."})
                os.remove("restart.flag")  
                break  # 무자비한 종료가 아닌, 루프를 스무스하게 빠져나감

            now = datetime.now()
            now_t = now.time()

            if not is_test_mode and now_t >= datetime.strptime("15:30:00", "%H:%M:%S").time():
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                # 🧹 [메모리 누수 방지] 내일을 위해 전역 메모리 초기화
                highest_prices.clear()
                alerted_stocks.clear()
                cooldowns.clear()
                LAST_AI_CALL_TIMES.clear()
                ACTIVE_TARGETS.clear() # targets 리스트도 함께 비워주면 좋습니다.
                break

            # 1. 내부 장중 스캐너 가동 (KOSPI)
            last_scan_time = check_and_run_intraday_scanner(targets, last_scan_time)

            # 🚀 2. [신규 추가] 5초마다 외부(초단타 스캐너 등)에서 DB에 새로 넣은 종목이 있는지 확인
            if time.time() - last_db_poll_time > 5:
                db_targets = DB.get_active_targets()
                for dt in db_targets:
                    if not any(t['code'] == dt['code'] for t in targets):
                        targets.append(dt)
                        event_bus.publish("COMMAND_WS_REG", {"codes": [dt['code']]})
                        print(f"🔄 [멀티 스캐너 연동] {dt['name']}({dt['code']}) 감시망 쾌속 합류! (전략: {dt.get('strategy')})")
                last_db_poll_time = time.time()
            
            # =========================================================
            # 🎯 [신규] 09:05:00 주도주 우선순위 재정렬 (딱 한 번 실행)
            # =========================================================
            now_t = datetime.now().time()
            strategy_start = datetime.strptime("09:05:00", "%H:%M:%S").time()
            
            if now_t >= strategy_start and not getattr(run_sniper, 'morning_report_done', False):
                print("🤖 Gemini AI가 주도주 TOP 3의 차트와 수급을 정밀 분석합니다...")
                # 💡 메인 루프가 멈추지 않도록 별도의 데몬 쓰레드로 작업을 던집니다!
                morning_thread = threading.Thread(
                    target=execute_morning_strategy_batch,
                    args=(targets, WS_MANAGER, radar, ai_engine), # DB, callback 파라미터 완전히 제거됨
                    daemon=True # 스나이퍼 엔진이 강제 종료되면 이 쓰레드도 미련 없이 함께 종료됨
                )
                morning_thread.start()

                run_sniper.morning_report_done = True
            # =========================================================

            # 3. 콘솔 가동 상태 로그 (1분 주기)
            if now_t.minute != last_msg_min:
                watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
                holding_count = len([t for t in targets if t['status'] == 'HOLDING'])
                print(f"💓 [{now.strftime('%H:%M:%S')}] 다중 감시망 가동 중... (감시: {watching_count} / 보유: {holding_count})")
                last_msg_min = now_t.minute

            # 4. 개별 종목 상태 라우팅
            for stock in targets[:]:
                code = str(stock['code'])[:6]
                status = stock['status']

                # -------------------------------------------------------------------------
                # 💡 [아키텍처 포인트] 이벤트 큐 병목을 피하기 위한 메모리 폴링(Pull) 구간
                # 웹소켓에서 모든 틱마다 이벤트를 발행(Push)하면 스캘핑 타점에 치명적인 지연이 
                # 발생하므로, 엔진이 루프를 돌며 가장 최신의 스냅샷 메모리만 읽어옵니다.
                # -------------------------------------------------------------------------

                ws_data = WS_MANAGER.get_latest_data(code)
                if not ws_data or ws_data.get('curr', 0) == 0: 
                    # 1분에 한 번 정도만 출력되게 하거나, 특정 종목 하나만 지정해서 확인 (디버깅용)
                    #if time.time() % 60 < 1: 
                    #    print(f"❓ [{stock['name']}] 데이터를 기다리는 중... (현재가: {ws_data.get('curr')})")
                    continue

                if status == 'WATCHING':
                    handle_watching_state(
                        stock, 
                        code, 
                        ws_data, 
                        admin_id,  
                        radar=radar,         # 🚀 추가
                        ai_engine=ai_engine  # 🚀 추가
                    )
                elif status == 'HOLDING':
                    handle_holding_state(
                        stock, 
                        code, 
                        ws_data, 
                        admin_id,  
                        current_market_regime,
                        radar=radar,         # 🚀 추가
                        ai_engine=ai_engine  # 🚀 추가
                    )
                
                # 👇 [수정] PENDING 대신 BUY_ORDERED 로 확인하고, 방금 만든 새 함수를 호출합니다!
                elif status == 'BUY_ORDERED':
                    handle_buy_ordered_state(stock, code)

            # 💡 [신규] 매매가 끝난 종목(COMPLETED)은 메모리(targets)에서 제거하여 속도 저하 방지
            # 반드시 targets[:] 를 사용하여 전역 변수인 ACTIVE_TARGETS와 메모리를 동기화해야 합니다!
            targets[:] = [t for t in targets if t['status'] != 'COMPLETED']

            time.sleep(1)

    except Exception as e:
        log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}")
        print(f"🔥 스나이퍼 루프 치명적 에러: {e}")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': f"🚨 [시스템 에러] 스나이퍼 엔진 치명적 에러: {e}"})

    except KeyboardInterrupt:
        print("\n🛑 스나이퍼 매매 엔진 종료")

if __name__ == "__main__":
    """
    python src/engine/kiwoom_sniper_v2.py 로 직접 실행할 때만 작동합니다.
    운영 환경(bot_main.py) 배포 시 이 블록은 투명인간 취급되므로 지울 필요가 없습니다!
    """
        
    # 1. 텔레그램 매니저 로드 (이벤트 리스너 가동)
    try:
        import src.notify.telegram_manager
        print("🔔 [Test Mode] 텔레그램 알림 리스너가 가동되었습니다.")
    except ImportError as e:
        print(f"⚠️ 텔레그램 매니저 로드 실패. 알림 없이 진행합니다: {e}")
        
    # 3. 스나이퍼 엔진 단독 실행!
    try:
        run_sniper(is_test_mode=True)
    except KeyboardInterrupt:
        print("\n🛑 테스트를 사용자에 의해 종료합니다.")