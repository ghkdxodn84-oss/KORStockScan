import sys
import os
import json
import telebot
from telebot import types
import time
from datetime import datetime
from pathlib import Path

# ==========================================
# 🚀 1. 경로 자동 탐지 (어느 위치에서 실행해도 OK)
# ==========================================
# 현재 파일: src/managers/telegram_manager.py
# .parent(managers) -> .parent(src) -> .parent(KORStockScan)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.constants import CONFIG_PATH, DEV_PATH  # 💡 중앙 관리 경로 활용
from src.utils.logger import log_error
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.utils import kiwoom_utils


# ==========================================
# ⚙️ 2. 설정 로드 및 봇 초기화 (함수화로 깔끔하게)
# ==========================================
def _load_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 설정 로드 실패: {e}")
        exit(1)

CONF = _load_config()
TOKEN = CONF.get('TELEGRAM_TOKEN')
ADMIN_ID = str(CONF.get('ADMIN_ID', ''))

# 💡 봇 객체 생성 (Lazy Initialization)
bot = telebot.TeleBot(TOKEN)
db_manager = DBManager()
event_bus = EventBus()

# ==========================================
# 3. [Refactored] 핵심 객체 싱글톤 인스턴스화
# ==========================================
# 💡 [우아함 3] 주석 대신 명확한 명칭과 로깅으로 흐름 파악 용이성 증대
try:
    bot = telebot.TeleBot(TOKEN)
    db_manager = DBManager()
    event_bus = EventBus() # 💡 싱글톤 인스턴스 획득
    
    print(f"🤖 Telegram Bot ({bot.get_me().first_name}) 온라인 - 관리자 ID: {ADMIN_ID}")
except Exception as e:
    log_error(f"🚨 텔레그램 매니저 초기화 실패: {e}")
    exit(1)

# ==========================================
# 📢 4. 핵심 발송 로직 (내부 함수화)
# ==========================================
def _send_to_admin(message_text, parse_mode='HTML'):
    """시스템 에러나 관리자 전용 정보를 ADMIN_ID에게 발송"""
    if not ADMIN_ID: return
    try:
        bot.send_message(chat_id=ADMIN_ID, text=message_text, parse_mode=parse_mode)
    except Exception as e:
        print(f"⚠️ 관리자 다이렉트 발송 실패: {e}")
        log_error(f"⚠️ 관리자 다이렉트 발송 실패: {e}")

def _broadcast_alert(message_text, audience='VIP_ALL', parse_mode='HTML'): 
    """권한(Audience)에 따라 가입자에게 브로드캐스트 (중복 함수 병합 완료)"""
    chat_ids = db_manager.get_telegram_chat_ids()
    
    for chat_id in chat_ids:
        user_level = db_manager.get_user_level(chat_id)
        
        should_send = False
        if user_level == 'A':
            should_send = True  # Admin은 무조건 수신
        elif user_level == 'V' and audience == 'VIP_ALL':
            should_send = True  # VIP는 일반 알림 수신

        if should_send:
            try:
                bot.send_message(chat_id, message_text, parse_mode=parse_mode)
                time.sleep(0.05) # 텔레그램 API 도배(Rate Limit) 방지
            except Exception:
                pass # 봇을 차단한 유저 등 예외 무시

# ==========================================
# 🎧 5. EventBus 구독 (Subscriber) 핸들러
# ==========================================
def handle_telegram_event(event_data):
    """
    💡 [핵심 아키텍처] 스나이퍼나 스캐너가 발행한 이벤트를 수신하여 텔레그램으로 쏘는 역할
    """
    # 1. 단순 메시지 형태 (update_kospi.py 등에서 보냄)
    if 'message' in event_data:
        msg = event_data.get('message', '')
        audience = event_data.get('audience', 'VIP_ALL')
        parse_mode = event_data.get('parse_mode', 'HTML')
        
        if not msg: return

        if audience == 'ADMIN_ONLY':
            _send_to_admin(msg, parse_mode)
        else:
            _broadcast_alert(msg, audience, parse_mode)
            
    # 2. 💡 [신규] 장전 리포트 형태 (final_ensemble_scanner.py 에서 보냄)
    elif event_data.get('type') == 'START_OF_DAY_REPORT':
        perf = event_data.get('performance_report', '')
        ai_brief = event_data.get('ai_briefing', '')
        main_picks = event_data.get('main_picks', [])
        
        # 메시지를 예쁘게 조립합니다.
        msg = f"🏆 <b>[오늘의 AI 리포트]</b>\n\n{perf}"
        if main_picks:
            msg += "🔥 <b>[오늘의 강력 추천]</b>\n"
            for p in main_picks:
                msg += f"• {p['Name']} ({p['Code']}) - AI확신: {p['Prob']*100:.1f}%\n"
        
        msg += f"\n🤖 <b>[AI 수석 브리핑]</b>\n{ai_brief}"
        
    # 3. 💡 [핵심 추가] 코스닥 장중 스캐너 리포트 수신 처리
    elif event_data.get('type') == 'KOSDAQ_REPORT':
        picks = event_data.get('picks', [])
        if not picks: return
        
        msg = "⚡ <b>[KOSDAQ AI 수급 폭발 포착]</b>\n\n"
        for p in picks:
            msg += f"🎯 <b>{p['Name']}</b> (<code>{p['Code']}</code>)\n"
            msg += f" ├ 현재가: {p['Price']:,}원\n"
            msg += f" ├ AI확신: {p['Prob']*100:.1f}%\n"
            msg += f" └ 수급상태: {p['ProgramStatus']}\n\n"
            
        msg += "<i>※ 해당 종목은 즉시 실시간 스나이퍼 감시망에 투입되었습니다.</i>"
        
        # 장중 속보이므로 VIP에게 즉시 쏩니다.
        _broadcast_alert(msg, audience='VIP_ALL', parse_mode='HTML')

def handle_admin_notify(event_data):
    """💡 [신규] TELEGRAM_ADMIN_NOTIFY 전용 수신기"""
    msg = event_data.get('text', '')
    if msg:
        _send_to_admin(msg, parse_mode='Markdown')

# 🚀 모듈이 로드될 때 EventBus에 텔레그램 수신기를 등록합니다!
event_bus.subscribe('TELEGRAM_BROADCAST', handle_telegram_event)
event_bus.subscribe('TELEGRAM_ADMIN_NOTIFY', handle_admin_notify)
# ==========================================
# 6. 텔레그램 UI 및 헬퍼 함수
# ==========================================
def has_special_auth(chat_id):
    chat_id_str = str(chat_id)
    try:
        if chat_id_str == ADMIN_ID: return True
        return db_manager.check_special_auth(chat_id_str)
    except Exception as e:
        print(f"⚠️ 권한 체크 중 DB 에러: {e}")
        log_error(f"⚠️ 권한 체크 중 DB 에러: {e}")
    return False

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏆 오늘의 추천종목", "🔍 실시간 종목분석")
    markup.add("📜 감시/보유 리스트", "➕ 수동 종목 추가")
    markup.add("☕ 서버 운영 후원하기", "🤖 AI 확신지수란?")
    return markup

def get_user_badge(chat_id):
    level = db_manager.get_user_level(chat_id)
    return "👑 [VIP 후원자] " if level == 'V' else ("🛡️ [관리자] " if level == 'A' else "👤 [일반] ")

# ==========================================
# 7. 텔레그램 메시지/명령어 핸들러 (@bot.message_handler)
# ==========================================
# 💡 [기술 부채 노트] 
# 향후 Level 3 아키텍처에서는 사용자의 명령어 입력도 이벤트(예: USER_COMMAND_RECEIVED)로 
# 변환하여 EventBus에 태우는 것이 이상적입니다. 현재는 임포트 지옥을 막기 위해 함수 내 지역 임포트를 유지합니다.

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    db_manager.add_new_user(message.chat.id)
    welcome_msg = (
    "🎯 **[KORStockScan V13.0] 스나이퍼 엔진 온라인**\n\n"
    "감정을 배제한 기계의 심장. 백테스트 승률 **63.3%**의 AI 앙상블 타격망이 전개되었습니다.\n\n"
    "⚡ **Sniper Protocol Activating...**\n"
    "✓ `[Targeting]` 다중 AI 합의체 교차 검증 기반 정예 타점 스캐닝\n"
    "✓ `[Radar]` FDR ✖️ Kiwoom 2중 지수 판독 및 실시간 수급 추적\n"
    "✓ `[Action]` 찰나를 파고드는 가변 익절/손절 스마트 트레일링 스탑\n\n"
    "* `시장의 노이즈를 뚫고, 가장 완벽한 타점만 저격합니다."
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    from src.engine.signal_radar import SniperRadar

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    token = kiwoom_utils.get_kiwoom_token(CONF)
    regime = SniperRadar.get_market_regime(token)
    regime_icon = "🐂 (상승장)" if regime == 'BULL' else "🐻 (조정장)"

    msg = f"🟢 *[상태 보고]*\n⏱ `{now_str}`\n📊 시장판독: **{regime_icon}**\n"
    bot.send_message(message.chat.id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.reply_to(message, "🔄 시스템을 재시작합니다.")
        # os._exit(0)
        with open("restart.flag", "w") as f: f.write("restart")

@bot.message_handler(func=lambda message: message.text == "🔍 실시간 종목분석")
def handle_analyze_btn(message):
    msg = bot.reply_to(message, "🔍 분석할 **종목코드 6자리** 입력", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_analyze_logic(m, m.text.strip()) if m.text.strip().isdigit() else None)

@bot.message_handler(func=lambda message: message.text == "📜 감시/보유 리스트")
def handle_watch_list(message):
    import pandas as pd
    from src.utils.constants import TRADING_RULES # 상수 안전 임포트

    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 💡 [아키텍처 포인트 1] 원시 Connection 대신 안전한 ORM Session Bind 활용
        with db_manager.get_session() as session:
            query = f"SELECT * FROM recommendation_history WHERE date='{today}' OR status='HOLDING'"
            df = pd.read_sql(query, session.bind)

        if df.empty:
            bot.reply_to(message, "📭 현재 감시 중이거나 보유 중인 종목이 없습니다.")
            return

        # 스나이퍼 엔진과 동일하게 중복 제거 (HOLDING 우선)
        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')

        # 💡 [핵심 방어] 구버전 DB라서 prob 컬럼이 아예 없다면, V3 기본값(70%)을 채워줍니다.
        if 'prob' not in df.columns:
            df['prob'] = TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70)

        # 💡 [아키텍처 포인트 2] 스나이퍼 V13.0 상태 머신과 완벽 동기화 (PENDING 삭제 -> BUY_ORDERED 반영)
        watching = df[df['status'] == 'WATCHING']
        buy_ordered = df[df['status'] == 'BUY_ORDERED']
        sell_ordered = df[df['status'] == 'SELL_ORDERED']
        holding = df[df['status'] == 'HOLDING']
        completed = df[df['status'] == 'COMPLETED']

        msg = "📜 *[KORStockScan 감시/보유 현황]*\n"
        msg += "━━━━━━━━━━━━━━\n"

        # 1. 감시 중 (WATCHING)
        msg += f"👀 *감시 대기 (WATCHING)* : {len(watching)}종목\n"
        for _, row in watching.iterrows():
            prob_val = row['prob'] if pd.notna(row['prob']) else TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70)
            msg += f" • {row['name']} ({row['code']}) | AI확신: {prob_val * 100:.0f}%\n"

        # 2. 주문/체결 대기 (BUY_ORDERED / SELL_ORDERED)
        if not buy_ordered.empty or not sell_ordered.empty:
            total_ordered = len(buy_ordered) + len(sell_ordered)
            msg += f"\n⏳ *주문 전송/대기* : {total_ordered}종목\n"
            for _, row in buy_ordered.iterrows():
                buy_price = row.get('buy_price', 0)
                msg += f" • [매수대기] {row['name']} | {int(buy_price) if pd.notna(buy_price) else 0:,}원\n"
            for _, row in sell_ordered.iterrows():
                msg += f" • [매도대기] {row['name']} | 체결 확인 중...\n"

        # 3. 보유 중 (HOLDING)
        if not holding.empty:
            msg += f"\n💰 *보유 중 (HOLDING)* : {len(holding)}종목\n"
            for _, row in holding.iterrows():
                buy_price = row.get('buy_price', 0)
                buy_qty = row.get('buy_qty', 0)
                msg += f" • {row['name']} ({row['code']}) | {int(buy_price) if pd.notna(buy_price) else 0:,}원 ({int(buy_qty) if pd.notna(buy_qty) else 0}주)\n"

        # 4. 오늘 매매 완료 (COMPLETED)
        if not completed.empty:
            msg += f"\n🏁 *금일 매매 완료* : {len(completed)}종목\n"
            for _, row in completed.iterrows():
                msg += f" • {row['name']}\n"

        msg += "━━━━━━━━━━━━━━"
        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        # 에러 발생 시 시스템 로그에도 남깁니다.
        from src.utils.logger import log_error
        log_error(f"감시 리스트 조회 에러: {e}")
        bot.reply_to(message, f"❌ 리스트 조회 중 시스템 에러 발생: {e}")

@bot.message_handler(func=lambda message: message.text == "🤖 AI 확신지수란?")
def handle_ai_confidence_info(message):
    info_msg = (
        "🤖 *[KORStockScan AI 확신지수 안내]*\n\n"
        "**AI 확신지수(Probability)**는 4개의 머신러닝 앙상블 모델(XGBoost, LightGBM 등)이 "
        "과거 3년 치의 차트 패턴, 외국인/기관 수급, 호가창 체결 데이터를 입체적으로 학습하여 도출한 **'이 종목이 당일 단기 상승할 확률'**을 의미합니다.\n\n"
        "📊 *확신지수 구간별 의미*\n"
        "• `90% 이상` : 🌟 **[초고확신]** 알고리즘이 찾아낸 완벽한 조건의 S급 타점\n"
        "• `80% ~ 89%` : 🔥 **[고확신]** 강력한 매집 수급이 포착된 주도주 (기본 스나이핑 대상)\n"
        "• `70% ~ 79%` : 🎯 **[유망]** 폭락장/조정장에서 기술적 반등이 예상되는 낙폭과대주\n"
        "• `70% 미만` : 🛑 **[관망]** 하락 리스크가 높아 시스템이 매수를 보류하는 구간\n\n"
        "💡 *스나이퍼 매매 작동 원리*\n"
        "현재 봇은 **AI 확신지수 80% 이상**(폭락장 세팅 시 70% 이상)인 종목 중에서도, "
        "단순히 차트만 보지 않고 **실시간 체결강도가 100을 돌파**하며 세력의 진짜 돈이 들어오는 순간에만 정밀하게 방아쇠를 당깁니다 🔫"
    )
    bot.reply_to(message, info_msg, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🏆 오늘의 추천종목")
def handle_today_picks(message):
    chat_id = message.chat.id
    try:
        from src.database.models import RecommendationHistory # 💡 ORM 모델 임포트
        
        # 💡 [아키텍처 포인트 1] 원시 SQL과 커넥션을 버리고 안전한 ORM 세션 활용
        today = datetime.now().strftime('%Y-%m-%d')
        with db_manager.get_session() as session:
            # ORM을 통해 파이썬 객체 리스트로 결과를 가져옵니다.
            picks = session.query(RecommendationHistory).filter_by(date=today).all()

        if not picks:
            bot.send_message(chat_id, "🧐 오늘은 아직 추천 종목이 없습니다.")
            return

        # 💡 [핵심 방어] 마크다운 에러로 인한 '읽씹'을 막기 위해 가장 안전한 HTML 포맷으로 변경
        msg = "🏆 <b>[오늘의 AI 추천 종목]</b>\n\n"

        # 💡 [아키텍처 포인트 2] 튜플 인덱스(p[2]) 대신 직관적인 ORM 객체 속성(p.type) 사용
        main_picks = [p for p in picks if getattr(p, 'type', '') == 'MAIN']
        runner_picks = [p for p in picks if getattr(p, 'type', '') == 'RUNNER']
        
        # SCALP는 type 컬럼에 있을 수도 있고, 우리가 새로 개편한 strategy 컬럼에 있을 수도 있으므로 둘 다 확인합니다.
        scalp_picks = [p for p in picks if getattr(p, 'type', '') == 'SCALP' or getattr(p, 'strategy', '') == 'SCALPING'] 

        if main_picks:
            msg += "🔥 <b>[고확신 스윙]</b>\n"
            for p in main_picks:
                safe_price = int(p.buy_price) if p.buy_price else 0
                msg += f"• <b>{p.name}</b> (<code>{safe_price:,}원</code>)\n"
            msg += "\n"

        if runner_picks:
            msg += "🥈 <b>[관심 종목 TOP 10]</b>\n"
            for p in runner_picks[:10]:
                safe_price = int(p.buy_price) if p.buy_price else 0
                msg += f"• <b>{p.name}</b> (<code>{safe_price:,}원</code>)\n"
            msg += "\n"

        if scalp_picks:
            msg += "⚡ <b>[초단타(SCALP) 포착 리스트]</b>\n"
            for p in scalp_picks[:10]:
                safe_price = int(p.buy_price) if p.buy_price else 0
                msg += f"• <b>{p.name}</b> (<code>{safe_price:,}원</code>)\n"

        # parse_mode를 무조건 HTML로 던집니다.
        bot.send_message(chat_id, msg, parse_mode='HTML')

    except Exception as e:
        # 혹시라도 에러가 나면 시스템 로거와 텔레그램에 모두 찍어서 원인을 즉시 파악
        from src.utils.logger import log_error
        log_error(f"오늘의 추천종목 에러: {e}")
        bot.send_message(chat_id, f"❌ 추천 종목 로드 실패: {e}")

@bot.message_handler(func=lambda message: message.text == "➕ 수동 종목 추가")
def handle_manual_add_btn(message):
    # 🛡️ 권한 체크: 어드민(A) 또는 VIP(V)
    if not has_special_auth(message.chat.id):
        bot.reply_to(message, "🚫 권한이 없습니다. 봇 관리자(A) 또는 VIP(V) 등급만 사용할 수 있는 기능입니다.")
        return

    msg = bot.reply_to(message, "📝 실시간 감시망에 추가할 **종목코드 6자리**를 입력해 주세요.\n*(예: 005930)*", parse_mode='Markdown')
    # 다음 입력값을 process_manual_add_step 함수로 넘깁니다.
    bot.register_next_step_handler(msg, process_manual_add_step)

def process_manual_add_step(message):
    """
    사용자가 입력한 종목코드를 검증하고 DB에 WATCHING 상태로 추가합니다.
    """
    code = message.text.strip()
    chat_id = message.chat.id
    
    # 💡 [핵심 방어 1] 정규화 및 방어 코드 (정확히 6자리 숫자인지 확인)
    if not code.isdigit() or len(code) != 6:
        bot.send_message(chat_id, "❌ 잘못된 입력입니다. 6자리 숫자 종목코드를 입력해 주세요.")
        return

    bot.send_message(chat_id, f"🔄 `{code}` 종목을 분석하여 스나이퍼 감시망에 투입합니다...", parse_mode='Markdown')

    try:
        from src.utils import kiwoom_utils
        from src.database.models import RecommendationHistory
        from src.utils.constants import TRADING_RULES

        # 1. API를 통한 종목명 조회 (실패 시 코드로 대체하여 봇 멈춤 방지)
        token = kiwoom_utils.get_kiwoom_token(CONF)
        try:
            info = kiwoom_utils.get_basic_info_ka10001(token, code)
            stock_name = info.get('Name', code)
        except Exception as e:
            stock_name = code
            print(f"⚠️ API 종목명 조회 실패, 코드로 대체: {e}")

        # 2. DB에 데이터 삽입 (ORM 적용)
        today = datetime.now().strftime('%Y-%m-%d')
        high_prob = TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8)
        
        with db_manager.get_session() as session:
            # 💡 [아키텍처 포인트] INSERT ON CONFLICT 대신 ORM의 우아한 분기 처리
            record = session.query(RecommendationHistory).filter_by(date=today, code=code).first()
            
            if record:
                # 이미 오늘 등록된 이력이 있다면 상태를 강제로 감시(WATCHING)로 멱등성 업데이트
                record.status = 'WATCHING'
                record.strategy = 'MANUAL'  # 💡 Phase 2 규격 반영
                record.prob = high_prob
            else:
                # 없다면 신규 생성
                new_record = RecommendationHistory(
                    date=today,
                    code=code,
                    name=stock_name,
                    prob=high_prob,
                    status='WATCHING',
                    strategy='MANUAL' # 💡 레거시 type='MANUAL' 대신 strategy 컬럼 사용
                )
                session.add(new_record)
            # with 블록 종료 시 자동 commit()
        
        # 3. 완료 메시지 발송
        msg_text = f"✅ *[{stock_name}]({code}) 수동 감시 투입 완료!*\n\n"
        msg_text += "📡 스나이퍼 엔진이 최대 5초 이내에 해당 종목의 호가창 감시를 시작합니다."
        bot.send_message(chat_id, msg_text, parse_mode='Markdown')

    except Exception as e:
        from src.utils.logger import log_error
        log_error(f"수동 종목 추가 에러: {e}")
        bot.send_message(chat_id, f"❌ 종목 추가 중 시스템 에러 발생: {e}")

@bot.message_handler(commands=['사유', 'why'])
def handle_why_not(message):
    chat_id = message.chat.id
    parts = message.text.split()
    
    if len(parts) < 2: 
        bot.send_message(chat_id, "⚠️ 종목코드를 함께 입력해 주세요. (예: `/why 005930`)", parse_mode='Markdown')
        return
        
    code = parts[1].strip()
    
    # 💡 [핵심 방어 1] 종목코드 6자리 유효성 검사 (엔진 크래시 완벽 차단)
    if not code.isdigit() or len(code) != 6:
        bot.send_message(chat_id, "❌ 잘못된 입력입니다. 6자리 숫자 종목코드를 입력해 주세요.")
        return

    # 대기 메시지를 먼저 띄워주어 체감 반응 속도를 높입니다.
    bot.send_message(chat_id, f"🔄 `{code}` 종목의 AI 타점 미달 사유를 분석 중입니다...", parse_mode='Markdown')
    
    try:
        # 💡 [아키텍처 포인트] 모듈 최상단이 아닌 지역(Local) 임포트를 유지하여 
        # 텔레그램 매니저와 스나이퍼 엔진 간의 치명적인 '순환 참조(Circular Import)'를 방지합니다.
        import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2
        
        report = kiwoom_sniper_v2.get_detailed_reason(code)
        bot.send_message(chat_id, report, parse_mode='Markdown')
        
    except Exception as e:
        # 💡 [핵심 방어 2] 에러 발생 시 시스템 로거로 추적 가능하게 기록
        from src.utils.logger import log_error
        log_error(f"미진입 사유 분석 에러 ({code}): {e}")
        bot.send_message(chat_id, f"❌ 사유 분석 중 오류 발생: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    """결제 직전 유효성 검사 (Telegram 결제 필수 콜백)"""
    try:
        # 무조건 승인 (추가적인 재고/금액 검증이 필요하다면 여기에 로직 추가)
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        from src.utils.logger import log_error
        log_error(f"결제 사전 승인 에러: {e}")

@bot.message_handler(content_types=['successful_payment'])
def handle_payment_success(message):
    """결제 완료 및 VIP 등급 승격 처리"""
    chat_id = message.chat.id
    
    try:
        # 💡 [아키텍처 포인트 1] 레거시(level=1) 대신 규격화된 문자열 'V' 사용
        db_manager.upgrade_user_level(chat_id, level='V')
        
        # 💡 [아키텍처 포인트 2] 마크다운 적용 및 VIP 혜택 안내 강화
        msg = (
            "🎊 **VIP 등급으로 승격되었습니다!**\n\n"
            "이제부터 KORStockScan의 **모든 VIP 전용 알림(초단타 타점, AI 교차 검증 리포트 등)**을 "
            "실시간으로 받아보실 수 있습니다. 후원해 주셔서 진심으로 감사합니다! 👑"
        )
        bot.send_message(chat_id, msg, parse_mode='Markdown')
        
        # 💡 [아키텍처 포인트 3] EventBus를 통한 관리자 다이렉트 보고
        from src.core.event_bus import EventBus
        event_bus = EventBus()
        admin_msg = f"💸 **[결제 발생]** Chat ID `{chat_id}` 님이 VIP로 승격되었습니다."
        event_bus.publish('TELEGRAM_BROADCAST', {'message': admin_msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'})
        
    except Exception as e:
        from src.utils.logger import log_error
        log_error(f"결제 완료 처리 중 시스템 에러: {e}")
        # 결제는 됐는데 DB가 뻗었을 경우를 대비한 최소한의 고객 대응 로직
        bot.send_message(chat_id, "✅ 결제는 확인되었으나 시스템 지연으로 등급 반영이 지연되고 있습니다. 관리자가 곧 수동으로 처리해 드릴 예정입니다.")

@bot.message_handler(commands=['reload'])
def handle_reload(message):
    chat_id = message.chat.id
    
    # 💡 [핵심 방어 1] 이미 선언해둔 전역 변수 ADMIN_ID를 깔끔하게 활용합니다.
    if str(chat_id) != ADMIN_ID:
        bot.send_message(chat_id, "⛔ 관리 권한이 없습니다.")
        return

    # 대기 메시지 발송
    msg_obj = bot.send_message(chat_id, "🔄 시스템 설정을 다시 읽어오는 중입니다...")

    try:
        from src.utils import kiwoom_utils
        import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2  # 💡 [핵심 방어 2] 순환 참조 방지를 위한 지역 임포트
        
        global CONF
        # 💡 [핵심 방어 3] 삭제된 구형 load_config() 대신 검증된 유틸 함수 사용
        CONF = kiwoom_utils.load_config()
        
        # 스나이퍼 엔진의 설정도 동기화
        if kiwoom_sniper_v2.reload_config():
            bot.edit_message_text("✅ 설정 파일(JSON)이 시스템 전반에 성공적으로 새로고침 되었습니다!", chat_id, msg_obj.message_id)
        else:
            bot.edit_message_text("⚠️ 텔레그램 설정은 갱신되었으나, 스나이퍼 엔진 갱신에 실패했습니다.", chat_id, msg_obj.message_id)
            
    except Exception as e:
        from src.utils.logger import log_error
        log_error(f"설정 새로고침 오류: {e}")
        bot.edit_message_text(f"❌ 새로고침 중 치명적 오류 발생: {e}", chat_id, msg_obj.message_id)

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    bot.send_message(message.chat.id, "메뉴 버튼을 이용해 주세요.", reply_markup=get_main_keyboard())

# ==========================================
# 🚀 8. 봇 구동 진입점 (bot_main.py에서 호출됨)
# ==========================================
def start_telegram_bot():
    print("🤖 텔레그램 봇 수신 대기 시작...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ 텔레그램 연결 순단 ({e}). 5초 후 재접속...")
            time.sleep(5)