# ==========================================
# 🚀 코스닥 하이브리드 AI 스캐너 (v13 정비 버전)
# ==========================================

import os
import time
import json
from datetime import datetime
import requests

import kiwoom_utils
from signal_radar import SniperRadar  # 📡 레이더 모듈 추가
from db_manager import DBManager
import final_ensemble_scanner 
from constants import TRADING_RULES # constants.py에 정의된 상수를 가져옵니다.

# 1. 경로 및 설정 로드 (기존 동일)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def broadcast_kosdaq_picks(conf, picks):
    if not picks: return
    token = conf.get('TELEGRAM_TOKEN')
    db = DBManager()
    chat_ids = db.get_telegram_chat_ids()
    today = datetime.now().strftime('%Y-%m-%d')

    msg = f"🚀 <b>[KOSDAQ AI 스태킹 리포트]</b> {today}\n"
    msg += f"당일 수급 폭발 코스닥 종목 중 AI가 엄선한 타겟입니다.\n\n"

    for r in picks:
        msg += f"🥇 <b>{r['Name']}</b> ({r['Code']})\n"
        msg += f"   • 현재가: {r['Price']:,}원 (AI 확신: <b>{r['Prob']:.1%}</b>)\n"
        msg += f"   • 프로그램: {r['ProgramStatus']} | 체결강도: {r['CntrStr']}%\n"
        msg += f"   • 전략 태그: <code>KOSDAQ_ML</code>\n\n"

    for cid in chat_ids:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": cid, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except Exception as e: print(f"텔레그램 전송 에러: {e}")

# ==========================================
# 3. 메인 스캐너 엔진 (하이브리드 온디맨드 방식)
# ==========================================
def run_kosdaq_scanner():
    print("🚀 [KOSDAQ 스캐너] 코스닥 하이브리드 AI 감시 가동...")
    conf = load_config()
    db = DBManager()
    
    models = final_ensemble_scanner.load_models()
    if not models: return

    while True:
        now = datetime.now()
        # 장중(09:05 ~ 15:20) 동작 체크
        if not (datetime.strptime("09:05:00", "%H:%M:%S").time() <= now.time() <= datetime.strptime("15:20:00", "%H:%M:%S").time()):
            print("🌙 [KOSDAQ] 대기 중...")
            time.sleep(60)
            continue

        token = kiwoom_utils.get_kiwoom_token(conf)
        if not token:
            time.sleep(10)
            continue

        # 🚀 1. 레이더 가동 및 1차 필터링
        radar = SniperRadar(token)
        print(f"\n🔍 [{now.strftime('%H:%M:%S')}] KOSDAQ 수급 주도주 정밀 스캔 중...")

        # 트랙 A: 코스닥(101) 등락률 상위
        raw_targets = radar.get_top_fluctuation_ka10027(mrkt_tp="101", limit=40)
        
        # 트랙 B: 코스닥(101) 초신성 수급 폭발 종목만 추출
        supernova = radar.find_supernova_targets(mrkt_tp="101")
        
        # 두 리스트 합치기
        all_candidate_codes = {t['Code']: t for t in raw_targets}
        for s in supernova:
            if s['code'] not in all_candidate_codes:
                all_candidate_codes[s['code']] = {'Code': s['code'], 'Name': s['name'], 'Price': 0} # Price는 나중에 업데이트

        kosdaq_picks = []

        # 🚀 2. 개별 종목 정밀 분석 루프
        for code, item in all_candidate_codes.items():
            name = item.get('Name', 'Unknown')
            
            # 💡 [교정] 가격 정보 추출 최적화
            curr_p = float(item.get('Price', item.get('cur_prc', item.get('price', 0))))
            if not kiwoom_utils.is_valid_stock(code, name, current_price=curr_p):
                continue

            is_program_buying = radar.check_program_buying_ka90008(code)
            p_status = "🔥 매수중" if is_program_buying else "⚪ 관망"

            # 💡 [교정] 데이터 로드 로직 단순화
            df = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
            if df is None or len(df) < 60: continue
            
            curr_price = int(df['Close'].iloc[-1])
            if curr_price < TRADING_RULES.get('MIN_PRICE', 5000):
                continue
            
            # 수급/신용 데이터 병합
            df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code)
            df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code)
            
            if not df_investor.empty: df = df.join(df_investor, how='left')
            else: df[['Retail_Net', 'Foreign_Net', 'Inst_Net']] = 0.0
            
            if not df_margin.empty: df = df.join(df_margin, how='left')
            else: df['Margin_Rate'] = 0.0
            
            df.fillna(0.0, inplace=True)

            # 🚀 3. AI 앙상블 분석
            try:
                prob = final_ensemble_scanner.predict_prob_for_df(df, models)

                # 코스닥 스윙은 '확신도 80% 이상' + '프로그램 매수'일 때 최적의 승률을 보입니다.
                if prob >= 0.80:
                    print(f"   🎯 [KOSDAQ 포착] {name} (확신: {prob:.1%}, 프로그램: {p_status})")
                    kosdaq_picks.append({
                        'Code': code, 'Name': name, 'Price': curr_price,
                        'Prob': prob, 'CntrStr': 100, 'Position': 'MIDDLE',
                        'ProgramStatus': p_status
                    })
            except Exception as e:
                print(f"⚠️ {name} AI 분석 실패: {e}")

            time.sleep(0.3) # API 제한 방어

        # 🚀 4. DB 저장 및 브로드캐스트
        if kosdaq_picks:
            new_picks = []
            today_str = datetime.now().strftime('%Y-%m-%d')
            for r in kosdaq_picks:
                try:
                    with db._get_connection() as conn:
                        cur = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND code=?", (today_str, r['Code']))
                        if cur.fetchone()[0] == 0:
                            conn.execute('''
                                INSERT INTO recommendation_history (date, code, name, buy_price, type, position_tag, prob, strategy)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (today_str, r['Code'], r['Name'], r['Price'], 'MAIN', r['Position'], r['Prob'], 'KOSDAQ_ML'))
                            new_picks.append(r)
                except Exception as e: print(f"DB 저장 에러: {e}")
            
            if new_picks:
                broadcast_kosdaq_picks(conf, new_picks)

        print(f"✅ [{now.strftime('%H:%M:%S')}] KOSDAQ 스캔 완료. 15분 대기...")
        time.sleep(900)