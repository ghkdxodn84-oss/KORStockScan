import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests

import final_ensemble_scanner
import kiwoom_orders
import kiwoom_utils
from constants import TRADING_RULES
from google_sheets_utils import GoogleSheetsManager
from kiwoom_websocket import KiwoomWSManager
from db_manager import DBManager
from ai_engine import GeminiSniperEngine # 💡 새로 만든 두뇌 파일 임포트
from signal_radar import SniperRadar  # 💡 레이더 부품 가져오기

# ==========================================
# 1. 경로 설정 (상대 참조 통일)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
STOCK_DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
CREDENTIALS_PATH = os.path.join(DATA_DIR, 'credentials.json')

# --- [전역 상태 변수] -----------------------------------------------
highest_prices = {}
alerted_stocks = set()
cooldowns = {}  # 💡 [신규] 스캘핑 뇌동매매 방지용 쿨타임 관리
CONF = None
KIWOOM_TOKEN = None
WS_MANAGER = None
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager()  # 💡 전역 객체 생성
global ACTIVE_TARGETS
ACTIVE_TARGETS = []
LAST_AI_CALL_TIMES = {}
# -------------------------------------------------------------------

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# 초기 설정 로드
try:
    CONF = load_config()
except:
    pass


def reload_config():
    global CONF
    try:
        CONF = load_config()
        print("✅ JSON 설정 파일이 새로고침 되었습니다!")
        return True
    except Exception as e:
        print(f"❌ 설정 새로고침 실패: {e}")
        return False


def send_admin_msg(text):
    if not CONF: return
    admin_id = CONF.get('ADMIN_ID')
    if not admin_id: return

    bot_token = CONF.get('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': admin_id, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ 관리자 메시지 전송 실패: {e}")

def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다."""
    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")
    
    # 💡 [교정 1] 전역 변수와 이미 임포트된 모듈을 직접 사용합니다.
    real_inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN, CONF) 
    
    # 🚨 [방어막 1] API 통신 실패 시 (None 반환 등) DB 강제 초기화 대참사 방지
    if real_inventory is None:
        print("⚠️ [동기화 보류] 잔고 조회 API 통신에 실패하여 DB 동기화를 건너뜁니다.")
        return

    real_codes = {item['code']: item for item in real_inventory}

    # 💡 [교정 2] 전역 인스턴스인 DB.execute_query를 사용합니다.
    db_holdings = DB.execute_query(
        "SELECT code, name, buy_qty FROM recommendation_history WHERE status = 'HOLDING'"
    ) 
    
    if not db_holdings:
        db_holdings = []

    # 3. 대조 및 강제 교정 시작
    for row in db_holdings:
        code, name, db_qty = row[0], row[1], row[2]
        
        # 🚨 [방어막 2] db_qty가 비어있거나 NULL일 경우 다운되는 현상 방지
        try:
            safe_db_qty = int(db_qty) if db_qty else 0
        except ValueError:
            safe_db_qty = 0
            
        if code not in real_codes:
            # 실제 계좌에 없다면? 이미 팔았는데 DB만 쥐고 있는 상태!
            print(f"⚠️ [동기화] {name}({code}): 실제 잔고 0주. 상태를 COMPLETED로 강제 변경.")
            DB.execute_query(
                "UPDATE recommendation_history SET status = 'COMPLETED' WHERE code = ? AND status = 'HOLDING'", 
                (code,)
            )
        else:
            # 계좌에 있는데 수량이 다르다면? (수동 매도, 혹은 이전 에러로 인한 누락)
            real_qty = real_codes[code]['qty']
            if safe_db_qty != real_qty:
                print(f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)")
                DB.execute_query(
                    "UPDATE recommendation_history SET buy_qty = ? WHERE code = ? AND status = 'HOLDING'", 
                    (real_qty, code)
                )

    print("✅ [데이터 동기화] 완료. 봇 메모리가 실제 계좌와 완벽히 일치합니다.")

def get_active_targets():
    targets = []
    try:
        today = datetime.now().strftime('%Y-%m-%d')

        with DB._get_connection() as conn:
            query = "SELECT * FROM recommendation_history WHERE date=? OR status='HOLDING'"
            df = pd.read_sql(query, conn, params=(today,))

        if df.empty:
            return targets

        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')
        targets = df.to_dict('records')

        for t in targets:
            t['prob'] = t.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8))
            t['buy_qty'] = t.get('buy_qty', 0)
            # 🚀 [추가] DB에 strategy 값이 없으면 기본적으로 KOSPI_ML 로 취급합니다.
            t['strategy'] = t.get('strategy', 'KOSPI_ML')

        return targets
    except Exception as e:
        print(f"🔥 [DB 로드 에러] 감시 대상을 불러오는 중 문제가 발생했습니다: {e}")
        return targets


# --- [외부 요청용 분석 리포트] ---
def analyze_stock_now(code):
    global KIWOOM_TOKEN, WS_MANAGER
    import time
    from datetime import datetime

    # 🚀 1. 장 운영 시간(09:00 ~ 15:30) 체크 로직
    now_time = datetime.now().time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    market_close = datetime.strptime("15:30:00", "%H:%M:%S").time()

    if not (market_open <= now_time <= market_close):
        return f"🌙 현재는 정규장 운영 시간(09:00~15:30)이 아닙니다.\n실시간 종목 분석은 장중에만 이용 가능합니다."

    # 2. 웹소켓 및 구독 상태 체크
    if not WS_MANAGER: return "⏳ 시스템 초기화 중..."
    WS_MANAGER.subscribe([code])

    try:
        stock_name = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)['Name']
    except:
        stock_name = code

    # 3. 실시간 호가 데이터 수신 대기 (최대 3초)
    ws_data = {}
    for _ in range(30):
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        if ws_data and ws_data.get('curr', 0) > 0: break
        time.sleep(0.1)

    # 💡 안내 메시지 개선: 단순히 '대기 중'이 아니라 이유를 함께 설명
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ **{stock_name}**({code}) 호가창 수신 대기 중...\n(거래가 멈춰있거나 일시적인 통신 지연일 수 있습니다.)"

    # 4. 분석 및 목표가 계산
    curr_price = ws_data.get('curr', 0)
    trailing_pct = TRADING_RULES.get('TRAILING_START_PCT', 3.0)
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
                rally_pct = TRADING_RULES.get('RALLY_TARGET_PCT', 5.0)
                target_price = int(curr_price * (1 + (rally_pct / 100)))
                target_reason = f"신고가 돌파 랠리 (단기 추세 +{rally_pct}%)"
    except Exception as e:
        print(f"⚠️ 목표가 계산 중 에러: {e}")

    # 5. 종합 평가
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
    targets = get_active_targets()
    target = next((t for t in targets if t['code'] == code), None)

    if not target: return f"🔍 `{code}` 종목은 현재 AI 감시 대상이 아닙니다."

    ws_data = WS_MANAGER.get_latest_data(code)
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ `{code}` 데이터 수신 중..."

    ai_prob = target.get('prob', 0.75)
    score, details, visual, prices, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

    report = f"🧐 **[{target['name']}] 미진입 사유 분석**\n━━━━━━━━━━━━━━━━━━\n"
    for label, status in checklist.items():
        icon = "✅" if status['pass'] else "❌"
        report += f"{icon} {label}: `{status['val']}`\n"

    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
    report += f"🎯 **종합 점수:** `{int(score)}점` (매수기준: {buy_threshold}점)\n"
    report += f"📝 **현재 상태:** {conclusion}\n"
    return report


def check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback):
    watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
    max_slots = TRADING_RULES.get('MAX_WATCHING_SLOTS', 5)
    scan_interval = TRADING_RULES.get('SCAN_INTERVAL_SEC', 1800)

    if watching_count < max_slots and (time.time() - last_scan_time > scan_interval):
        print(f"🔄 [시스템] 감시 슬롯 부족({watching_count}개). 신규 종목을 스캔합니다...")
        try:
            new_picks = final_ensemble_scanner.run_intraday_scanner(KIWOOM_TOKEN)
            if new_picks:
                added_count = 0
                msg_body = ""

                for np in new_picks:
                    if not any(t['code'] == np['code'] for t in targets):
                        targets.append(np)
                        WS_MANAGER.subscribe([np['code']])
                        added_count += 1
                        msg_body += f"• **{np['name']}** ({np['code']}) - AI 확신도: {np['prob']:.1%}\n"

                if added_count > 0:
                    alert_msg = f"🔄 **[장중 주도주 재스캔 완료]**\n빈 슬롯을 채우기 위해 다음 {added_count}개 종목의 실시간 감시를 시작합니다.\n\n{msg_body}"
                    broadcast_callback(alert_msg)

            return time.time()
        except Exception as e:
            kiwoom_utils.log_error(f"⚠️ 장중 스캔 중 오류: {e}")
    return last_scan_time

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
    
    db = DBManager()
    now_t = datetime.now().time()
    
    # ==========================================
    # 1️⃣ DB 상태 업데이트 (영구 기록)
    # ==========================================
    if exec_type == 'BUY':
        # 🎯 실제 매수 체결: 정확한 단가(buy_price)를 적고 '보유(HOLDING)' 상태로 전환!
        query = """
            UPDATE recommendation_history 
            SET buy_price = ?, status = 'HOLDING' 
            WHERE code = ? AND status IN ('WATCHING', 'BUY_ORDERED')
        """
        db.execute_query(query, (exec_price, code))
        print(f"✅ [영수증 확인] {code} 실제 매수 체결가 {exec_price:,}원 DB 반영 완료!")
        
    elif exec_type == 'SELL':
        # 🏁 실제 매도 체결: 기존 buy_price를 가져와서 정확한 수익률을 계산
        try:
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT buy_price FROM recommendation_history WHERE code = ? AND status IN ('HOLDING', 'SELL_ORDERED')", (code,))
                row = cursor.fetchone()

                buy_price = 0
                profit_rate = 0.0
                
                if row and row[0] > 0:
                    buy_price = row[0]
                    # 실제 수익률 계산 (슬리피지 모두 반영됨)
                    profit_rate = round(((exec_price - buy_price) / buy_price) * 100, 2)

                    cursor.execute("SELECT strategy FROM recommendation_history WHERE code = ?", (code,))
                    strategy_row = cursor.fetchone()
                    
                    # 💡 [핵심 1] 무조건 현재 매매 사이클은 'COMPLETED'로 쾅 닫아서 기록을 영구 보존합니다!
                    db.update_sell_record(code, exec_price, profit_rate, status='COMPLETED')
                    print(f"🎉 [매매 완료] {code} 실매도가 {exec_price:,}원 / 최종 수익률: {profit_rate}% (기록 보존 완료)")

                    # 💡 [핵심 2] 스캘핑 부활 조건이 맞으면, 덮어쓰지 않고 '새로운 줄'을 만들어냅니다.
                    is_scalp_revive = (strategy_row and strategy_row[0] == 'SCALPING') and (now_t < datetime.strptime("15:15:00", "%H:%M:%S").time())
                    if is_scalp_revive:
                        today = datetime.now().strftime('%Y-%m-%d')
                        stock_info = next((s for s in ACTIVE_TARGETS if s['code'] == code), None)
                        
                        if stock_info:
                            name = stock_info.get('name', code)
                            prob = stock_info.get('prob', 0.8)
                            
                            # 완전히 새로운 WATCHING 레코드를 INSERT 합니다.
                            insert_query = """
                                INSERT INTO recommendation_history 
                                (date, code, name, status, strategy, prob)
                                VALUES (?, ?, ?, 'WATCHING', 'SCALPING', ?)
                            """
                            db.execute_query(insert_query, (today, code, name, prob))
                            print(f"♻️ [스캘핑 재진입 준비] {name}({code}) 새로운 매매를 위해 DB에 신규 감시(WATCHING) 등록!")

        except Exception as e:
            print(f"🚨 매도 체결 영수증 처리 중 에러: {e}")

    # ==========================================
    # 2️⃣ 스나이퍼 메모리(ACTIVE_TARGETS) 즉시 동기화
    # ==========================================
    # 💡 [핵심 교정] if exec_type == 'BUY': 밖으로 빼서 무조건 실행되게 함!
    
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
        

def handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback, radar=None, ai_engine=None):
    
    strategy = stock.get('strategy', 'KOSPI_ML')
    now = datetime.now()
    now_t = now.time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    strategy_start = datetime.strptime("09:05:00", "%H:%M:%S").time()
    db = DBManager()

    # 🛡️ 9시 ~ 9시 5분: 데이터 수집 및 관찰 기간 (진입 금지)
    if market_open <= now_t < strategy_start:
        if now.second % 30 == 0:  # 30초마다 로그
            print(f"📡 [관찰 모드] 주도주 에너지 집계 중... (현재 {len(ACTIVE_TARGETS)}종목 모니터링)")
        return
    
    MIN_PRICE = TRADING_RULES.get('MIN_PRICE', 5000)
    MAX_SURGE = TRADING_RULES.get('MAX_SCALP_SURGE_PCT', 20.0) 
    MAX_INTRADAY_SURGE = TRADING_RULES.get('MAX_INTRADAY_SURGE', 15.0)
    MIN_LIQUIDITY = TRADING_RULES.get('MIN_SCALP_LIQUIDITY', 300_000_000)

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

    ai_prob = stock.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70))
    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
    strong_vpw = TRADING_RULES.get('VPW_STRONG_LIMIT', 120)

    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':
        ratio = TRADING_RULES.get('INVEST_RATIO_SCALPING', 0.05)
        
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        fluctuation = float(ws_data.get('fluctuation', 0.0)) 
        open_price = float(ws_data.get('open', curr_price))

        if open_price > 0:
            intraday_surge = ((curr_price - open_price) / open_price) * 100
        else:
            intraday_surge = fluctuation
        
        liquidity_value = (ask_tot + bid_tot) * curr_price

        # 🚨 [이중 방어막] 과매수 위험 차단
        if fluctuation >= MAX_SURGE or intraday_surge >= MAX_INTRADAY_SURGE:
            if time.time() % 60 < 1:
                print(f"🚫 [SCALP 제외] {stock['name']} | 전일대비: +{fluctuation}%, 시가대비: +{intraday_surge:.1f}% (과매수 위험)")
            return 
        
        # 💡 [기본 조건 검사] 수급과 호가잔량이 최소 기준을 넘어야 함
        if current_vpw >= TRADING_RULES.get('VPW_SCALP_LIMIT', 120) and liquidity_value >= MIN_LIQUIDITY:
            
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
            
            target_buy_price, used_drop_pct = kiwoom_utils.get_smart_target_price(
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

            # 💡 VIP 종목이면서 쿨타임(10초)이 지났을 때만 AI를 호출!
            if ai_engine and radar and is_vip_target and (time_elapsed > 10.0):
                
                recent_ticks = radar.get_tick_history_ka10003(code, limit=10)
                recent_candles = radar.get_minute_candles_ka10080(code, limit=5)
                
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
                        
                        target_audience = 'VIP_ALL' if liquidity_value >= TRADING_RULES.get('VIP_LIQUIDITY_THRESHOLD', 500_000_000) else 'ADMIN_ONLY'
                        try:
                            broadcast_callback(ai_msg, audience=target_audience, parse_mode='HTML')
                        except Exception as e:
                            print(f"AI 알림 발송 실패: {e}")
            
            # =========================================================
            # 🚨 5. AI 거부권 및 최종 매수 대기열(그물망) 투척
            # =========================================================
            if current_ai_score <= 40:
                if time.time() - last_ai_time < 1.0: 
                    print(f"🚫 [AI 매수 차단] {stock['name']} 진입 불가! (AI 점수: {current_ai_score}점)")
                cooldowns[code] = time.time() + 180 
                return  
            
            # 최신 AI 점수를 반영하여 목표가 재계산 (방금 AI 점수가 갱신되었을 수 있으므로)
            final_target_buy_price, final_used_drop_pct = kiwoom_utils.get_smart_target_price(
                curr_price, 
                v_pw=current_vpw, 
                ai_score=current_ai_score 
            )

            stock['target_buy_price'] = final_target_buy_price
            is_trigger = True
            
            msg = (f"⚡ **[{stock['name']}]({code}) 초단타(SCALP) 그물망 투척!**\n"
                   f"현재가: `{curr_price:,}원` ➡️ **매수대기: `{final_target_buy_price:,}원` (-{final_used_drop_pct:.1f}% 눌림목)**\n"
                   f"호가잔량대금: `{liquidity_value / 100_000_000:.1f}억` | 수급강도: `{current_vpw:.1f}%`")
            
            stock['msg_audience'] = 'VIP_ALL' if liquidity_value >= TRADING_RULES.get('VIP_LIQUIDITY_THRESHOLD', 500_000_000) else 'ADMIN_ONLY'

            # ==========================================
            # 🚀 6. 상태 변경 및 주문 실행 대기열로 이동
            # ==========================================
            if is_trigger:
                stock['status'] = 'BUY_ORDERED'
                stock['buy_time'] = now_t.strftime("%H:%M:%S")
                stock['strategy'] = strategy
                stock['invest_ratio'] = ratio

                alerted_stocks.add(code)
                
                kiwoom_utils.log_trade(db, {
                    'code': code,
                    'name': stock['name'],
                    'status': 'BUY_ORDERED',
                    'strategy': strategy,
                    'price': curr_price,
                    'target_buy_price': stock.get('target_buy_price', 0),
                    'v_pw': current_vpw,
                    'time': now_t.strftime("%H:%M:%S"),
                    'ai_score': current_ai_score
                })

                if msg:
                    kiwoom_utils.send_telegram_msg(msg, stock.get('msg_audience', 'ADMIN_ONLY'), broadcast_callback)

                print(f"🎯 [{stock['name']}] 감시 완료 ➡️ [BUY_ORDERED] 상태 전환 (목표가: {stock.get('target_buy_price')}원)")

    # 2️⃣ 코스닥 우량주 스윙 (KOSDAQ_ML) 전략
    elif strategy == 'KOSDAQ_ML':
        ratio = TRADING_RULES.get('INVEST_RATIO_KOSDAQ', 0.10)
        score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

        v_pw_limit = TRADING_RULES.get('VPW_KOSDAQ_LIMIT', 105) if ai_prob >= TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70) else strong_vpw
        is_shooting = current_vpw >= v_pw_limit

        if (score >= buy_threshold or is_shooting) and current_vpw >= TRADING_RULES.get('VPW_KOSDAQ_LIMIT', 105):
            is_trigger = True
            msg = (f"🚀 **[{stock['name']}]({code}) 코스닥(KOSDAQ) 스나이퍼 포착!**\n"
                   f"현재가: `{curr_price:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{current_vpw:.1f}%` {visual}")

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        ratio = TRADING_RULES.get('INVEST_RATIO_KOSPI', 0.20)
        ai_prob = stock.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8))
        score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

        strong_vpw = TRADING_RULES.get('VPW_STRONG_LIMIT', 115)
        buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
        v_pw_limit = 100 if ai_prob >= TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8) else strong_vpw
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

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN, config=CONF)
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
            config=CONF, order_type=order_type_code, price=final_price
        )

        is_success = False
        ord_no = ''

        # 💡 [핵심 교정] 응답값을 정확히 분석하여 성공 여부 판단
        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                err_msg = res.get('return_msg', '사유 없음')
                print(f"❌ [주문거절] {stock['name']} 서버 거절: {err_msg}")
                if strategy == 'SCALPING':
                    cooldowns[code] = time.time() + 1200
        elif res:
            is_success = True

        # 💡 [핵심 교정] 주문이 "정상 접수" 되었을 때만 메모리와 DB 상태를 'BUY_ORDERED'로 변경!
        if is_success:
            print(f"🛒 [{stock['name']}] 매수 주문 전송 완료. 체결 영수증 대기 중...")
            # 💡 [신규 추가] 스윙 종목 등 꼬리표가 없는 애들은 기본적으로 모두(VIP_ALL)에게 보냅니다.
            audience = stock.get('msg_audience', 'VIP_ALL')
            # 콜백 함수에 발송 권한 정보를 함께 넘겨줍니다.
            broadcast_callback(msg, audience=audience)
            alerted_stocks.add(code)
            
            kiwoom_utils.log_error(f"💰 [주문접수] {stock['name']} {real_buy_qty}주 (전략: {strategy})", config=CONF)

            # 1. 메모리 업데이트 (BUY_ORDERED 통일)
            stock.update({
                'status': 'BUY_ORDERED',
                'order_price': final_price if final_price > 0 else curr_price,
                'buy_qty': real_buy_qty,
                'odno': ord_no,
                'order_time': time.time()
            })
            highest_prices[code] = curr_price

            # 2. DB 업데이트 (영수증 콜백이 찾을 수 있도록 BUY_ORDERED로 설정) [수정] AND status = 'WATCHING' 추가 하여 이미 매수 주문이 들어간 종목은 중복 업데이트 방지   
            db.execute_query(
                "UPDATE recommendation_history SET status = 'BUY_ORDERED', buy_price = ? WHERE code = ? AND status = 'WATCHING'", 
                (final_price if final_price > 0 else curr_price, code)
            )

def handle_holding_state(stock, code, ws_data, admin_id, broadcast_callback, market_regime, radar=None, ai_engine=None): # 🚀 파라미터 추가
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
    db = DBManager()

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
        
        recent_ticks = radar.get_tick_history_ka10003(code, limit=10)
        recent_candles = radar.get_minute_candles_ka10080(code, limit=5)
        
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
        target_pct = TRADING_RULES.get('SCALP_TARGET', 2.0)
        base_stop_pct = TRADING_RULES.get('SCALP_STOP', -2.5)
        scalp_trailing_limit = TRADING_RULES.get('SCALP_TRAILING_LIMIT', 0.5)
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
            if held_time_min >= TRADING_RULES['SCALP_TIME_LIMIT_MIN'] and profit_rate >= TRADING_RULES['MIN_FEE_COVER']:
                is_sell_signal = True
                reason = f"⏱️ {TRADING_RULES['SCALP_TIME_LIMIT_MIN']}분 타임아웃 (순환매 우선)"
            elif now_t >= datetime.strptime("15:15:00", "%H:%M:%S").time():
                is_sell_signal = True
                reason = "⏰ 장 마감 전 현금화"

    # 2️⃣ 코스닥 AI 스윙 (KOSDAQ_ML) 전용 전략
    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= TRADING_RULES.get('KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
        except:
            pass

        if not is_sell_signal and peak_profit >= TRADING_RULES.get('KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= 1.0:
                is_sell_signal = True
                reason = f"🏆 KOSDAQ 트레일링 익절 (+{TRADING_RULES.get('KOSDAQ_TARGET', 4.0)}% 돌파 후 하락)"

        elif not is_sell_signal and profit_rate <= TRADING_RULES.get('KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({TRADING_RULES.get('KOSDAQ_STOP', -2.0)}%)"

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        pos_tag = stock.get('position_tag', 'MIDDLE')
        if pos_tag == 'BREAKOUT':
            current_stop_loss = TRADING_RULES['STOP_LOSS_BREAKOUT']
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = TRADING_RULES['STOP_LOSS_BOTTOM']
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = TRADING_RULES['STOP_LOSS_BULL'] if market_regime == 'BULL' else TRADING_RULES['STOP_LOSS_BEAR']
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= TRADING_RULES['HOLDING_DAYS']:
                is_sell_signal = True
                reason = f"⏳ {TRADING_RULES['HOLDING_DAYS']}일 스윙 보유 만료"
        except:
            pass

        if not is_sell_signal and peak_profit >= TRADING_RULES['TRAILING_START_PCT']:
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= TRADING_RULES['TRAILING_DRAWDOWN_PCT']:
                is_sell_signal = True
                reason = f"🏆 가변익절 (+{TRADING_RULES['TRAILING_START_PCT']}% 도달 후 하락)"
            elif profit_rate <= TRADING_RULES['MIN_PROFIT_PRESERVE']:
                is_sell_signal = True
                reason = f"수익 보존 (최소 {TRADING_RULES['MIN_PROFIT_PRESERVE']}%)"

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
            db.execute_query("UPDATE recommendation_history SET status = 'COMPLETED' WHERE code = ?", (code,))
            stock['status'] = 'COMPLETED'
        else:
            # 💡 [핵심 방어 1] 장부 잠금
            db.execute_query("UPDATE recommendation_history SET status = 'SELL_ORDERED' WHERE code = ? AND status = 'HOLDING'", (code,))
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
                reason_type=sell_reason_type, 
                config=CONF
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
                broadcast_callback(msg)

                # 스캘핑 쿨타임 (기존 로직 유지)
                if strategy in ['SCALPING', 'SCALP'] and now_t < datetime.strptime("15:15:00", "%H:%M:%S").time():
                    cooldowns[code] = time.time() + 1200
                    try: alerted_stocks.discard(code)
                    except: pass
                    print(f"♻️ [{stock['name']}] 스캘핑 청산 완료 후 20분 쿨타임 진입.")
            else:
                # 💡 [핵심 교정] 에러 메시지를 읽고 영구 탈출(COMPLETED)할지, 복구(HOLDING)할지 결정합니다.
                err_msg = res.get('return_msg', '') if isinstance(res, dict) else ''
                
                if '매도가능수량' in err_msg:
                    print(f"🚨 [{stock['name']}] 잔고 0주(이미 매도됨). 무한루프를 막기 위해 COMPLETED로 강제 전환합니다.")
                    db.execute_query("UPDATE recommendation_history SET status = 'COMPLETED' WHERE code = ?", (code,))
                    stock['status'] = 'COMPLETED'
                else:
                    print(f"🚨 [{stock['name']}] 일시적 매도 전송 실패! 상태를 다시 HOLDING으로 원상복구합니다.")
                    db.execute_query("UPDATE recommendation_history SET status = 'HOLDING' WHERE code = ?", (code,))
                    stock['status'] = 'HOLDING'

def handle_buy_ordered_state(stock, code):
    """
    주문 전송 후(BUY_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 로직을 호출합니다.
    """
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time
    
    strategy = stock.get('strategy', 'KOSPI_ML')
    # 💡 [개선] AI 예약 주문(target_buy_price가 명시된 경우)은 20분(1200초) 대기
    if stock.get('target_buy_price', 0) > 0:
        timeout_sec = TRADING_RULES.get('RESERVE_TIMEOUT_SEC', 1200) # 20분
    else:
        # 일반 장중 추격 매수 타임아웃
        timeout_sec = 20 if strategy == 'SCALPING' else TRADING_RULES.get('ORDER_TIMEOUT_SEC', 30)
        
    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 매수 대기 {timeout_sec}초 초과. 취소 절차 진입.")
        orig_ord_no = stock.get('odno')
        db = DBManager()

        # [CASE 1] 원주문번호가 없는 경우 (예외적 상황)
        if not orig_ord_no:
            stock['status'] = 'WATCHING'
            stock.pop('order_time', None)
            db.execute_query("UPDATE recommendation_history SET status = 'WATCHING', buy_price = 0 WHERE code = ? AND status = 'BUY_ORDERED'", (code,))
            return

        # [CASE 2] 정상적인 취소 로직 호출
        process_order_cancellation(stock, code, orig_ord_no, db, strategy)

def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    """
    미체결 주문의 실제 취소 처리와 DB/메모리 청소를 담당합니다.
    """
    # 1. 취소 주문 전송
    res = kiwoom_orders.send_cancel_order(
        code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0, config=CONF
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
        
        # DB 업데이트 (영구 상태 반영)
        db.execute_query(
            "UPDATE recommendation_history SET status = 'WATCHING', buy_price = 0 WHERE code = ? AND status = 'BUY_ORDERED'", 
            (code,)
        )

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
            db.execute_query(
                "UPDATE recommendation_history SET status = 'HOLDING' WHERE code = ? AND status = 'BUY_ORDERED'", 
                (code,)
            )
        return False

def execute_morning_strategy_batch(targets, ws_manager, radar, ai_engine, db, broadcast_callback):
    """
    [v13.0] 09:05 주도주 분석, 리포트 발송, 매수 예약 주문을 일괄 처리합니다.
    """
    print("🤖 [전략 집행] 09:05 주도주 정렬 및 AI 예약 매매를 시작합니다.")
    
    # 1. 수급 기반 우선순위 재정렬
    for stock in targets:
        ws_data = ws_manager.get_latest_data(stock['code'])
        stock['priority_score'] = kiwoom_utils.calculate_market_leader_score(ws_data)
    
    targets.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    top_3 = targets[:3]
    
    # 2. 통합 리포트 작성을 위한 변수 초기화
    full_report = "🚀 **[Gemini 주도주 TOP 3 정밀 분석]**\n"
    full_report += f"📅 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    full_report += "━━━━━━━━━━━━━━━━━━\n\n"

    for i, s in enumerate(top_3):
        code = s['code']
        ws_data = ws_manager.get_latest_data(code)
        ticks = radar.get_tick_history_ka10003(code, limit=10)
        candles = radar.get_minute_candles_ka10080(code, limit=5)
        
        # AI 분석 호출
        ai_json_str = ai_engine.analyze_morning_leader(s['name'], ws_data, ticks, candles)
        
        try:
            import json
            res = json.loads(ai_json_str)
            ai_price = res.get('target_price')
            
            # 리포트 텍스트 조립
            full_report += f"📍 **{i+1}위. {s['name']}** ({code})\n"
            full_report += f"💬 `{res.get('one_liner', '분석 중...')}`\n"
            full_report += f"📈 패턴: **{res.get('pattern', '-')}**\n"
            full_report += f"🎯 권장타점: `{res.get('target_price', '-')}원` 부근\n"
            full_report += f"⚠️ 리스크: {res.get('risk_factor', '-')}\n"
            full_report += "━━━━━━━━━━━━━━━━━━\n"

            # 🎯 [핵심] 실제 매수 예약 주문 실행
            deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN, config=CONF)
            order_res = kiwoom_orders.reserve_buy_order_ai(
                code=code,
                ai_target_price=ai_price,
                deposit=deposit,
                token=KIWOOM_TOKEN,
                config=CONF
            )

            # 주문 성공 시 상태 업데이트
            if order_res:
                s.update({
                    'status': 'BUY_ORDERED',
                    'target_buy_price': ai_price,
                    'order_time': time.time()
                })
                db.execute_query(
                    "UPDATE recommendation_history SET status = 'BUY_ORDERED', buy_price = ? WHERE code = ?", 
                    (ai_price, code)
                )

        except Exception as e:
            print(f"❌ {s['name']} 전략 집행 중 에러: {e}")

    # 최종 리포트 발송
    broadcast_callback(full_report)
    print("✅ 09:05 전략 배치 작업이 완료되었습니다.")

# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (교통 정리 전담)
# ==============================================================================
def run_sniper(broadcast_callback):
    # 💡 전역 변수 ACTIVE_TARGETS를 선언합니다.
    global KIWOOM_TOKEN, WS_MANAGER, ACTIVE_TARGETS

    run_sniper.morning_report_done = False  # 함수 속성으로 아침 보고 완료 여부 추적

    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V12.2 멀티 엔진 가동 (관리자: {admin_id})")

    is_open, reason = kiwoom_utils.is_trading_day()
    if not is_open:
        msg = f"🛑 오늘은 {reason} 휴장일이므로 스나이퍼 매매 엔진을 가동하지 않습니다."
        print(msg)
        broadcast_callback(msg)
        return

    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        kiwoom_utils.log_error("❌ 토큰 발급 실패로 엔진을 중단합니다.", config=CONF, send_telegram=True)
        return
    
    radar = SniperRadar(KIWOOM_TOKEN)

    # 👇 [여기입니다!] 토큰 발급 직후에 동기화를 먼저 싹 돌립니다.
    sync_balance_with_db()
    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN, on_execution_callback=handle_real_execution)
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
        kiwoom_utils.log_error("🚨 [설정 에러] GEMINI_API_KEY를 찾을 수 없습니다.", config=CONF, send_telegram=True)
    else:
        ai_engine = GeminiSniperEngine(api_keys=api_keys)
        print(f"🤖 제미나이 AI 엔진이 {len(api_keys)}개의 API 키로 가동됩니다.")

    # 💡 DB에서 가져온 타겟을 전역 변수에 연결합니다.
    ACTIVE_TARGETS = get_active_targets()
    targets = ACTIVE_TARGETS  # targets는 ACTIVE_TARGETS의 별칭이 되어 동기화됨
    last_scan_time = time.time()

    # 🚀 [핵심] 외부 스캐너가 DB에 밀어넣은 신규 종목을 감지하기 위한 타이머
    last_db_poll_time = time.time()

    current_market_regime = kiwoom_utils.get_market_regime(KIWOOM_TOKEN)
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다.")

    target_codes = [t['code'] for t in targets]
    WS_MANAGER.subscribe([c for c in target_codes])
    last_msg_min = -1

    try:
        while True:
            # 💡 [신규 추가] 'restart.flag' 파일이 생성되었는지 확인
            if os.path.exists("restart.flag"):
                print("🔄 [우아한 종료] 재시작 깃발을 확인했습니다. 시스템을 안전하게 정지합니다.")
                broadcast_callback("🛑 스나이퍼 엔진이 하던 작업을 마치고 우아하게 재시작됩니다.")
                os.remove("restart.flag")  # 깃발 수거
                break  # 무자비한 종료가 아닌, 루프를 스무스하게 빠져나감

            now = datetime.now()
            now_t = now.time()

            if now_t >= datetime.strptime("15:30:00", "%H:%M:%S").time():
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                # 🧹 [메모리 누수 방지] 내일을 위해 전역 메모리 초기화
                highest_prices.clear()
                alerted_stocks.clear()
                cooldowns.clear()
                LAST_AI_CALL_TIMES.clear()
                ACTIVE_TARGETS.clear() # targets 리스트도 함께 비워주면 좋습니다.
                break

            # 1. 내부 장중 스캐너 가동 (KOSPI)
            last_scan_time = check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback)

            # 🚀 2. [신규 추가] 5초마다 외부(초단타 스캐너 등)에서 DB에 새로 넣은 종목이 있는지 확인
            if time.time() - last_db_poll_time > 5:
                db_targets = get_active_targets()
                for dt in db_targets:
                    if not any(t['code'] == dt['code'] for t in targets):
                        targets.append(dt)
                        WS_MANAGER.subscribe([dt['code']])
                        print(f"🔄 [멀티 스캐너 연동] {dt['name']}({dt['code']}) 감시망 쾌속 합류! (전략: {dt.get('strategy')})")
                last_db_poll_time = time.time()
            
            # =========================================================
            # 🎯 [신규] 09:05:00 주도주 우선순위 재정렬 (딱 한 번 실행)
            # =========================================================
            now_t = datetime.now().time()
            strategy_start = datetime.strptime("09:05:00", "%H:%M:%S").time()
            
            if now_t >= strategy_start and not getattr(run_sniper, 'morning_report_done', False):
                print("🤖 Gemini AI가 주도주 TOP 3의 차트와 수급을 정밀 분석합니다...")
                execute_morning_strategy_batch(
                    targets, WS_MANAGER, radar, ai_engine, DB, broadcast_callback
                )
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
                        broadcast_callback, 
                        radar=radar,         # 🚀 추가
                        ai_engine=ai_engine  # 🚀 추가
                    )
                elif status == 'HOLDING':
                    handle_holding_state(
                        stock, 
                        code, 
                        ws_data, 
                        admin_id, 
                        broadcast_callback, 
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
        kiwoom_utils.log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}", config=CONF, send_telegram=True)

    except KeyboardInterrupt:
        print("\n🛑 스나이퍼 매매 엔진 종료")