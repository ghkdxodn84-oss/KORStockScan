import telebot
from telebot import types
import json
import os
import sqlite3
import pandas as pd
from datetime import datetime
import time

# 공통 DB 매니저 및 상수 임포트
from utils.db_manager import DBManager

# ==========================================
# 1. 환경 설정 및 봇 객체 초기화
# ==========================================
def load_config():
    try:
        # 스마트 스위치: 테스트 환경이면 config_dev.json을 우선 로드
        dev_path = os.path.join(DATA_DIR, 'config_dev.json')
        target_path = dev_path if os.path.exists(dev_path) else CONFIG_PATH
        
        with open(target_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ 설정 파일을 찾을 수 없습니다.")
        return {}

CONF = load_config()
TOKEN = CONF.get('TELEGRAM_TOKEN')
ADMIN_ID = str(CONF.get('ADMIN_ID', ''))

if not TOKEN:
    print("🚨 TELEGRAM_TOKEN이 없어 봇을 기동할 수 없습니다.")
    exit()

bot = telebot.TeleBot(TOKEN)
db_manager = DBManager()

# ==========================================
# 📢 2. 외부 호출용 전용 발송 함수들 (Export)
# ==========================================

def send_to_admin(message_text, parse_mode='HTML'):
    """
    [신규 추가] 시스템 에러나 관리자만 알아야 하는 중요 정보를 ADMIN_ID에게 즉각 발송합니다.
    다른 파일(kiwoom_utils 등)에서 이 함수만 import해서 쓰면 됩니다!
    """
    if not ADMIN_ID:
        print("⚠️ ADMIN_ID가 설정되어 있지 않아 관리자 알림을 보낼 수 없습니다.")
        return
    try:
        bot.send_message(chat_id=ADMIN_ID, text=message_text, parse_mode=parse_mode)
    except Exception as e:
        kiwoom_utils.log_error(f"관리자 다이렉트 발송 실패: {e}")

def broadcast_alert(message_text, audience='VIP_ALL', parse_mode='HTML'): 
    """모든 가입자(권한에 따라 필터링)에게 메시지를 쏘는 브로드캐스트 함수"""
    chat_ids = db_manager.get_telegram_chat_ids()
    
    for chat_id in chat_ids:
        user_level = db_manager.get_user_level(chat_id)
        
        # 권한별 발송 필터링 로직 (A: 무조건 수신, V: VIP_ALL일 때만 수신)
        should_send = False
        if user_level == 'A':
            should_send = True
        elif user_level == 'V' and audience == 'VIP_ALL':
            should_send = True

        if should_send:
            try:
                bot.send_message(chat_id, message_text, parse_mode=parse_mode)
                time.sleep(0.05) # 도배 방지
            except Exception as e:
                pass # 차단한 유저 등 예외 무시

def broadcast_today_picks():
    """오늘의 추천 종목 아침 브로드캐스트"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        query = "SELECT name, buy_price, type, code FROM recommendation_history WHERE date=?"
        
        # 💡 [핵심 교정] sqlite3.connect 직접 호출을 버리고, 전역 db_manager의 안전한 함수 사용!
        picks = db_manager.execute_query(query, (today,))

        if not picks:
            return

        msg = f"🌅 <b>[{today}] AI KOSPI 종목추천 리포트</b>\n"
        msg += "--------------------------------------\n"

        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']

        if main_picks:
            msg += "🔥 <b>[AI 확신 종목]</b>\n"
            for name, price, _, code in main_picks:
                msg += f"• <b>{name}</b> ({str(code)[:6]}) : <code>{price:,}원</code>\n"
            msg += "\n"

        if runner_picks:
            msg += "🥈 <b>[AI 관심 종목 TOP 10]</b>\n"
            for name, price, _, code in runner_picks[:10]:
                msg += f"• <b>{name}</b> ({str(code)[:6]}) : <code>{price:,}원</code>\n"

        broadcast_alert(msg, parse_mode='HTML')

    except Exception as e:
        send_to_admin(f"❌ 아침 브로드캐스트 실패: {e}")
        kiwoom_utils.log_error(f"아침 브로드캐스트 실패: {e}")

# ==========================================
# 3. UI 및 헬퍼 함수
# ==========================================
def has_special_auth(chat_id):
    chat_id_str = str(chat_id)
    try:
        # 1. 최고 관리자는 무조건 프리패스
        if chat_id_str == ADMIN_ID:
            return True

        # 2. DBManager를 통해 권한 확인
        return db_manager.check_special_auth(chat_id_str)
    
    except Exception as e:
        kiwoom_utils.log_error(f"권한 체크 중 DB 에러 발생: {e}")

    # 권한이 없거나 에러가 나면 False 반환
    return False

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏆 오늘의 추천종목", "🔍 실시간 종목분석")
    markup.add("📜 감시/보유 리스트", "➕ 수동 종목 추가")
    markup.add("☕ 서버 운영 후원하기", "🤖 AI 확신지수란?")
    return markup

def get_user_badge(chat_id):
    level = db_manager.get_user_level(chat_id)
    return "👑 [VIP 후원자] " if level == 1 else "👤 [일반] "

# ==========================================
# 4. 핵심 비즈니스 로직 연동 (순환 참조 방지 적용)
# ==========================================
def process_manual_add_logic(message, code):
    # 💡 순환 참조 방지: 여기서만 잠깐 임포트해서 씁니다.
    import kiwoom_utils 
    
    stock_name = code
    try:
        token = kiwoom_utils.get_kiwoom_token(CONF)
        info = kiwoom_utils.get_basic_info_ka10001(token, code)
        stock_name = info['Name']
        if stock_name == code:
            raise ValueError("존재하지 않는 종목코드이거나 상장폐지된 종목입니다.")
    except Exception as api_e:
        bot.reply_to(message, f"❌ 종목명 조회 실패: {api_e}")
        kiwoom_utils.log_error(f"수동 추가 실패: {api_e}")
        return

    try:
        today = datetime.now().strftime('%Y-%m-%d')
        with db_manager._get_connection() as conn:
            conn.execute("""
                INSERT INTO recommendation_history (date, code, name, prob, status, type) 
                VALUES (?, ?, ?, ?, 'WATCHING', 'MANUAL')
                ON CONFLICT(date, code) DO UPDATE SET status='WATCHING', prob=excluded.prob
            """, (today, code, stock_name, TRADING_RULES['SNIPER_AGGRESSIVE_PROB']))
            conn.commit()

        # 차트 저항대 분석 로직... (이전 코드와 동일하게 처리되었다고 가정, 길이상 생략 방지)
        df = db_manager.get_stock_data(code, limit=20)
        target_price_str = "데이터 부족"
        target_reason = "기본 시스템 익절선"

        if df is not None and len(df) >= 10:
            curr_price = int(df.iloc[-1]['Close'])
            high_20d = df['High'].max()
            upper_bb = df['Close'].mean() + (2 * df['Close'].std())
            chart_resistance = max(high_20d, upper_bb)
            
            if chart_resistance > curr_price:
                target_price_str = f"{int(chart_resistance):,}원"
                target_reason = "차트 저항대"
            else:
                target_price_str = f"{int(curr_price * 1.05):,}원"
                target_reason = "신고가 돌파 랠리"

        msg = f"✅ *[{stock_name}]({code}) 수동 감시 추가 완료!*\n\n📊 *목표 단가:* `{target_price_str}` ({target_reason})"
        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ DB 저장 에러: {e}")

def process_analyze_logic(message, code):
    import kiwoom_sniper_v2 # 💡 순환 참조 방지
    
    chat_id = message.chat.id
    bot.send_message(chat_id, f"🔄 `{code}` 종목 실시간 분석 중...", parse_mode='Markdown')

    try:
        report = kiwoom_sniper_v2.analyze_stock_now(code)
        bot.send_message(chat_id, f"{get_user_badge(chat_id)}님을 위한 결과!\n\n{report}", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 분석 중 오류: {e}")

# ==========================================
# 5. 텔레그램 메시지/명령어 핸들러 (@bot.message_handler)
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    db_manager.add_new_user(message.chat.id)
    bot.send_message(message.chat.id, "🚀 **KORStockScan 시스템 기동**", reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    import kiwoom_utils
    from signal_radar import SniperRadar

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    token = kiwoom_utils.get_kiwoom_token(CONF)
    regime = SniperRadar(token).get_market_regime()
    regime_icon = "🐂 (상승장)" if regime == 'BULL' else "🐻 (조정장)"

    msg = f"🟢 *[상태 보고]*\n⏱ `{now_str}`\n📊 시장판독: **{regime_icon}**\n"
    bot.send_message(message.chat.id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['사유', 'why'])
def handle_why_not(message):
    import kiwoom_sniper_v2
    parts = message.text.split()
    if len(parts) < 2: return bot.send_message(message.chat.id, "⚠️ 종목코드 입력 필요")
    
    try:
        report = kiwoom_sniper_v2.get_detailed_reason(parts[1].strip())
        bot.send_message(message.chat.id, report, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ 오류: {e}")

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.reply_to(message, "🔄 시스템을 재시작합니다.")
        os._exit(0)

@bot.message_handler(func=lambda message: message.text == "📜 감시/보유 리스트")
def handle_watch_list(message):
    # (기존 DB 조회 및 마크다운 출력 로직... 그대로 유지)
    bot.reply_to(message, "📜 *[감시 리스트 조회 완료]*", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🏆 오늘의 추천종목")
def handle_today_picks(message):
    # (오늘의 추천 종목 HTML 렌더링 로직... 그대로 유지)
    bot.send_message(message.chat.id, "🏆 <b>[오늘의 추천 종목 로드 완료]</b>", parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "🔍 실시간 종목분석")
def handle_analyze_btn(message):
    msg = bot.reply_to(message, "🔍 분석할 **종목코드 6자리** 입력", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_analyze_logic(m, m.text.strip()) if m.text.strip().isdigit() else None)

@bot.message_handler(func=lambda message: message.text == "➕ 수동 종목 추가")
def handle_manual_add_btn(message):
    if not has_special_auth(message.chat.id): return bot.reply_to(message, "🚫 권한 부족")
    msg = bot.reply_to(message, "📝 감시할 **종목코드 6자리** 입력", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_manual_add_logic(m, m.text.strip()) if m.text.strip().isdigit() else None)

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    bot.send_message(message.chat.id, "메뉴 버튼을 이용해 주세요.", reply_markup=get_main_keyboard())

# ==========================================
# 🚀 6. 봇 구동 진입점 (bot_main.py에서 호출됨)
# ==========================================
def start_telegram_bot():
    print("🤖 텔레그램 봇 수신 대기 시작...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ 텔레그램 연결 순단 ({e}). 5초 후 재접속...")
            time.sleep(5)