import json
import os
import signal
import sqlite3
import threading
import time
from datetime import datetime

import telebot
from telebot import types

# 💡 엔진 및 유틸리티 모듈 임포트
import kiwoom_sniper_v2
import kiwoom_utils

# ==========================================
# 1. 경로 및 환경 설정 (상대 참조 고정)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')
STOCK_DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')

def load_config():
    """안전한 설정 파일 로드"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 설정 파일을 찾을 수 없습니다: {CONFIG_PATH}")
        return {}

CONF = load_config()
TOKEN = CONF.get('TELEGRAM_TOKEN')

if not TOKEN:
    print("🚨 TELEGRAM_TOKEN이 없어 봇을 기동할 수 없습니다.")
    exit()

bot = telebot.TeleBot(TOKEN)
engine_thread = None

# ==========================================
# 2. 데이터베이스 유틸리티 (Thread-safe)
# ==========================================
def init_db():
    """사용자 관리 DB 초기화"""
    with sqlite3.connect(USERS_DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                user_level INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def get_db_connection(db_path):
    """함수 내에서 개별적으로 연결하여 스레드 충돌 방지"""
    return sqlite3.connect(db_path, timeout=10)

# ==========================================
# 3. 챗봇 핵심 로직 및 메뉴
# ==========================================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏆 오늘의 추천종목", "🔍 실시간 종목분석")
    markup.add("☕ 서버 운영 후원하기")
    return markup

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    chat_id = message.chat.id
    with get_db_connection(USERS_DB_PATH) as conn:
        conn.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))

    welcome_msg = (
        "🚀 **KORStockScan v12.1 관제 시스템 기동**\n\n"
        "백테스트 **승률 63.3%**의 AI 앙상블이 실시간 감시 중입니다.\n\n"
        "📈 **스나이퍼 매매 원칙**\n"
        "• 장중 가변 익절 / 손절 시스템 적용\n"
        "• FDR-Kiwoom API 2중 지수 판독 적용\n"
        "• AI 확신도 기반 정예 종목 선별"
    )
    bot.send_message(chat_id, welcome_msg, parse_mode='Markdown', reply_markup=get_main_keyboard())

# --- [FDR 방어 로직이 적용된 상태 보고] ---
@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    chat_id = message.chat.id
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 🚀 [FDR 방어 핵심] 엔진이 판독한 최신 시장 상태 가져오기
    regime = kiwoom_sniper_v2.get_market_regime()
    regime_icon = "🐂 (상승장)" if regime == 'BULL' else "🐻 (조정장)"

    msg = f"🟢 *[KORStockScan 시스템 보고]*\n"
    msg += f"⏱ 현재시간: `{now_str}`\n"
    msg += f"📊 시장판독: **{regime_icon}**\n\n"

    # 엔진 스레드 생존 확인
    if engine_thread and engine_thread.is_alive():
        msg += "✅ **매매 엔진:** `정상 가동 중` 💓\n"
    else:
        msg += "❌ **매매 엔진:** `중단됨 (재시작 필요)` ⚠️\n"

    # 실시간 모니터링 현황
    try:
        with get_db_connection(STOCK_DB_PATH) as conn:
            today = datetime.now().strftime('%Y-%m-%d')
            watch_cnt = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='WATCHING'",
                                     (today,)).fetchone()[0]
            hold_cnt = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='HOLDING'",
                                    (today,)).fetchone()[0]
            msg += f"👀 **감시 대상:** `{watch_cnt} 종목`\n"
            msg += f"💼 **보유 종목:** `{hold_cnt} 종목`"
    except Exception as e:
        msg += f"⚠️ DB 조회 불가: {e}"

    bot.send_message(chat_id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['분석'])
def handle_analyze(message):
    badge = get_user_badge(message.chat.id)
    chat_id = message.chat.id
    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(chat_id, "⚠️ 종목코드를 함께 입력해주세요. (예: `/분석 005930`)", parse_mode='Markdown')
        return

    code = parts[1].strip()
    bot.send_message(chat_id, f"🔄 `{code}` 분석을 시작합니다...", parse_mode='Markdown')

    try:
        report = kiwoom_sniper_v2.analyze_stock_now(code)
        final_msg = f"{badge}님을 위한 분석 결과입니다!\n\n{report}"
        bot.send_message(message.chat.id, final_msg, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 오류 발생: {e}")


@bot.message_handler(commands=['오늘의추천', '추천'])
def handle_today_picks(message):
    chat_id = message.chat.id
    try:
        conn_temp = sqlite3.connect(STOCK_DB_PATH)
        today = datetime.now().strftime('%Y-%m-%d')
        picks = conn_temp.execute("SELECT name, buy_price, type FROM recommendation_history WHERE date=?",
                                  (today,)).fetchall()
        conn_temp.close()

        if not picks:
            bot.send_message(chat_id, "🧐 오늘은 아직 추천 종목이 없습니다.")
            return

        msg = "🏆 **[오늘의 AI 추천 종목]**\n\n"
        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']

        if main_picks:
            msg += "🔥 **[강력 추천]**\n"
            for name, price, _ in main_picks:
                msg += f"• **{name}** (`{price:,}원`)\n"
            msg += "\n"

        if runner_picks:
            msg += "🥈 **[관심 종목 상위 10개]**\n"
            for name, price, _ in runner_picks[:10]:
                msg += f"• **{name}** (`{price:,}원`)\n"

        bot.send_message(chat_id, msg, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ 추천 종목 로드 실패")

@bot.message_handler(commands=['사유', 'why'])
def handle_why_not(message):
    chat_id = message.chat.id
    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(chat_id, "⚠️ 종목코드를 입력해주세요. (예: `/사유 005930`)")
        return

    code = parts[1].strip()
    bot.send_message(chat_id, f"🔍 `{code}` 종목의 실시간 진입 요건을 정밀 분석합니다...")

    try:
        # 스나이퍼 엔진의 상세 사유 함수 호출
        reason_report = kiwoom_sniper_v2.get_detailed_reason(code)
        bot.send_message(chat_id, reason_report, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 분석 중 오류 발생: {e}")


# ==========================================
# 🚀 [관제탑] 수동 종목 등록 로직 시작
# ==========================================
@bot.message_handler(commands=['수동등록', 'admin'])
def handle_manual_add(message):
    chat_id = message.chat.id
    # 1. 관리자 권한 철저히 확인
    if str(chat_id) != str(CONF.get('ADMIN_ID')):
        bot.send_message(chat_id, "⛔ 관리자만 사용 가능한 명령어입니다.")
        return

    # 2. 인라인 버튼(채팅창 안에 뜨는 투명 버튼) 생성
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🎯 수동 감시 종목 추가", callback_data="add_manual_stock")
    markup.add(btn)

    bot.send_message(chat_id, "👨‍✈️ **[스나이퍼 관제탑]**\n수동으로 감시할 타겟을 지정하시겠습니까?", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "add_manual_stock")
def callback_add_stock(call):
    # 버튼을 누르면 기존 메시지의 버튼을 로딩 상태로 변경하거나 알림을 띄울 수 있음
    bot.answer_callback_query(call.id)

    msg = bot.send_message(call.message.chat.id, "✏️ 추가할 **종목코드**와 **종목명**을 띄어쓰기로 입력하세요.\n*(예: 005930 삼성전자)*",
                           parse_mode="Markdown")
    # 다음 사용자가 치는 채팅을 'process_manual_stock_input' 함수가 가로채서 처리하도록 예약
    bot.register_next_step_handler(msg, process_manual_stock_input)

def process_manual_stock_input(message):
    chat_id = message.chat.id
    try:
        inputs = message.text.split()
        if len(inputs) < 2:
            bot.send_message(chat_id, "❌ 형식이 잘못되었습니다. 다시 시도해주세요.\n*(예: 005930 삼성전자)*", parse_mode="Markdown")
            return

        code = inputs[0]
        name = " ".join(inputs[1:])

        # 🚀 [수정됨] kiwoom_utils의 전담 함수를 우아하게 호출합니다!
        is_success = kiwoom_utils.register_manual_stock(code, name, CONF)

        if is_success:
            bot.send_message(chat_id,
                             f"✅ **[{name}]({code})**\n스나이퍼 수동 타겟으로 DB 등록이 완료되었습니다!\n\n*(※ 실시간 감시 대상 등록 최대 30분 소요)*",
                             parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ DB 등록 실패. 서버 로그를 확인하세요.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ 명령어 처리 오류 발생: {e}")


# ==========================================
# 🚀 [관제탑] 수동 종목 등록 로직 끝
# ==========================================

# --- [4. 결제 및 등급 관리 로직] ---

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def handle_payment_success(message):
    chat_id = message.chat.id
    temp_conn = sqlite3.connect(USERS_DB_PATH)
    temp_conn.execute("UPDATE users SET user_level = 1 WHERE chat_id = ?", (chat_id,))
    temp_conn.commit()
    temp_conn.close()
    bot.send_message(chat_id, "🎊 **VIP 등급으로 승격되었습니다!**")


@bot.message_handler(commands=['reload'])
def handle_reload(message):
    global CONF
    chat_id = message.chat.id
    if str(chat_id) != str(CONF.get('ADMIN_ID')):
        bot.send_message(chat_id, "⛔ 관리 권한이 없습니다.")
        return

    try:
        CONF = load_config()
        if kiwoom_sniper_v2.reload_config():
            bot.send_message(chat_id, "✅ 설정이 성공적으로 새로고침 되었습니다!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ 새로고침 오류: {e}")


# --- [5. 텍스트 메시지 및 기타 유틸] ---

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🏆 오늘의 추천종목":
        handle_today_picks(message)
    elif text == "🔍 실시간 종목분석":
        bot.send_message(chat_id, "분석할 **종목코드 6자리**를 입력해주세요.", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_analyze_step)
    elif text == "☕ 서버 운영 후원하기":
        prices = [types.LabeledPrice(label="서버 후원", amount=50)]
        bot.send_invoice(chat_id, "✨ 서버 후원", "24시간 운영 지원", "donation_50", "", "XTR", prices)
    else:
        bot.send_message(chat_id, "아래 메뉴 버튼을 이용해 주세요.", reply_markup=get_main_keyboard())


def get_user_badge(chat_id):
    try:
        temp_conn = sqlite3.connect(USERS_DB_PATH)
        row = temp_conn.execute("SELECT user_level FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
        temp_conn.close()
        return "👑 [VIP 후원자] " if row and row[0] == 1 else "👤 [일반] "
    except:
        return ""


def process_analyze_step(message):
    chat_id = message.chat.id
    code = message.text.strip()

    if len(code) == 6 and code.isdigit():
        bot.send_message(chat_id, f"🔄 `{code}` 분석을 시작합니다...", parse_mode='Markdown')
        try:
            # 엔진의 분석 함수 호출
            report = kiwoom_sniper_v2.analyze_stock_now(code)
            bot.send_message(chat_id, report, parse_mode='Markdown')
        except Exception as e:
            # 🚀 [업데이트] 에러 내용을 사용자에게 직접 전달하여 원인 파악
            bot.send_message(chat_id, f"❌ 시스템 분석 오류 발생:\n`{str(e)}`", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "⚠️ 올바른 6자리 종목코드를 입력해 주세요.")

# ==========================================
# 4. 브로드캐스트 및 알림 시스템
# ==========================================
def broadcast_alert(message_text):
    temp_conn = sqlite3.connect(USERS_DB_PATH)
    rows = temp_conn.execute('SELECT chat_id FROM users').fetchall()
    for row in rows:
        try:
            bot.send_message(row[0], message_text, parse_mode='Markdown')
            time.sleep(0.05)
        except:
            pass
    temp_conn.close()

def broadcast_today_picks():
    """
    [v12.1 복구] 봇 시작 시, 오늘 날짜의 추천 종목을 모든 가입자에게 브로드캐스트합니다.
    """
    try:
        # 1. DB 연결 및 오늘자 추천 종목 조회
        conn = sqlite3.connect(STOCK_DB_PATH)
        today = datetime.now().strftime('%Y-%m-%d')

        # 종목코드 6자리를 보장하며 데이터 추출
        query = "SELECT name, buy_price, type, code FROM recommendation_history WHERE date=?"
        picks = conn.execute(query, (today,)).fetchall()
        conn.close()

        if not picks:
            print(f"🧐 [{today}] 추천 종목이 아직 생성되지 않아 알림을 대기합니다.")
            return

        # 2. 메시지 헤더 구성
        msg = f"🌅 **[{today}] AI 스태킹 앙상블 리포트**\n"
        msg += "🎯 **전략: 장중 +2.0% 익절(가변익절) / -2.5% 손절**\n"
        msg += "------------------------------------------\n"

        # 3. 등급별 종목 분류 (code[:6] 원칙 적용)
        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']

        # 강력 추천 종목 출력
        if main_picks:
            msg += "🔥 **[고확신 종목]**\n"
            for name, price, _, code in main_picks:
                clean_code = str(code)[:6]  # 🚀 무조건 6자리만 사용
                msg += f"• **{name}** ({clean_code}) : `{price:,}원`\n"
            msg += "\n"

        # 관심 종목 출력 (상위 10개로 제한하여 도배 방지)
        if runner_picks:
            msg += "🥈 **[관심 종목 TOP 10]**\n"
            for name, price, _, code in runner_picks[:10]:
                clean_code = str(code)[:6]
                msg += f"• **{name}** ({clean_code}) : `{price:,}원`\n"

            # 전체 개수 안내로 신뢰도 상승
            if len(runner_picks) > 10:
                msg += f"\n*(그 외 {len(runner_picks) - 10}개의 유망 종목 실시간 추적 중)*"

        msg += "\n------------------------------------------\n"
        msg += "💡 `/상태` 입력 시 엔진 가동 현황을 확인하실 수 있습니다."

        # 4. 전체 사용자에게 전송
        broadcast_alert(msg)
        print(f"📢 [{today}] 추천 종목 브로드캐스트 완료 (총 {len(picks)}종목)")

    except Exception as e:
        # 통합 에러 로깅 활용
        import kiwoom_utils
        kiwoom_utils.log_error(f"❌ 아침 브로드캐스트 실패: {e}", config=CONF)


# --- [6. 메인 시스템 가동] ---

def start_engine():
    kiwoom_sniper_v2.run_sniper(broadcast_alert)


def monitor_exit_time():
    while True:
        if datetime.now().time() >= datetime.strptime("22:00:00", "%H:%M:%S").time():
            print("🌙 시스템 안전 종료")
            os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(60)


if __name__ == '__main__':
    print("🤖 KORStockScan v12.1 관제 시스템 기동 중...")
    init_db()

    # 🚀 영업일 체크
    is_open, reason = kiwoom_utils.is_trading_day()

    if is_open:
        # 정상 영업일에만 리포트 발송 및 매매 엔진 스레드 시작
        broadcast_today_picks()

        engine_thread = threading.Thread(target=start_engine, daemon=True)
        engine_thread.start()
        print("✅ [시스템] 정상거래일 - 스나이퍼 엔진 스레드가 가동되었습니다.")
    else:
        # 휴장일 처리
        print(f"🛑 [시스템] 오늘은 {reason} 휴장일입니다. 매매 엔진과 리포트 발송을 생략합니다.")
        # engine_thread는 None 상태로 유지되어 /상태 명령어 시 '중단됨'으로 정상 표시됨

    # 야간 자동 종료 감시 시작 (휴장일이어도 봇 프로세스 자체는 꺼야 하므로 실행)
    threading.Thread(target=monitor_exit_time, daemon=True).start()

    print("📱 텔레그램 봇 폴링 시작 (명령어 대기 중)...")
    bot.infinity_polling()