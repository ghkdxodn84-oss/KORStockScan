import os
import time
import json
import requests
from datetime import datetime

import kiwoom_utils
from signal_radar import SniperRadar  # 🚀 신규 추가: 정보국 레이더
from db_manager import DBManager

# ==========================================
# 1. 경로 및 환경 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# ==========================================
# 2. 메인 감시 루프
# ==========================================
def run_scalper():
    print("⚡ [SCALPING 스캐너] 초단타 감시 엔진 가동 (1분 주기)...")
    conf = load_config()
    db = DBManager()
    today = datetime.now().strftime('%Y-%m-%d')

    already_picked = set()
    last_closed_msg_time = 0 # 💡 [교정 1] 장 마감 도배 방지용 타이머 추가

    while True:
        now = datetime.now()
        now_time = now.time()

        # 💡 [교정 1 적용] 장 마감 메시지 도배 방지 (1시간에 1번만 출력)
        market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
        market_close = datetime.strptime("15:20:00", "%H:%M:%S").time()
        
        if not (market_open <= now_time <= market_close):
            if time.time() - last_closed_msg_time > 3600:
                print("🌙 장 마감 혹은 개장 전입니다. 대기 중...")
                last_closed_msg_time = time.time()
            time.sleep(60)
            continue

        token = kiwoom_utils.get_kiwoom_token(conf)
        if not token:
            time.sleep(10)
            continue
            
        radar = SniperRadar(token)
        print(f"🔍 [{now.strftime('%H:%M:%S')}] 실시간 수급 쏠림 & 폭발 전조 종목 스캔 중...")
        
        soaring_targets = radar.get_top_fluctuation_ka10027(mrkt_tp="101", limit=30)
        supernova_targets = radar.find_supernova_targets(mrkt_tp="101")

        all_targets = {}
        for t in soaring_targets:
            all_targets[t['Code']] = t
            
        for t in supernova_targets:
            if t['code'] not in all_targets:
                all_targets[t['code']] = {
                    'Code': t['code'],
                    'Name': t['name'],
                    'ChangeRate': t.get('spike_rate', 0),
                    'CntrStr': 150.0,
                    'Price': t.get('cur_prc', 0) # 💡 초신성 트랙에 현재가 데이터가 있다면 보존
                }

        for code, t in all_targets.items():
            if code not in already_picked:
                
                # 💡 [교정 2] 가격 데이터를 먼저 추출하여 초고속 필터링에 넘겨줍니다!
                curr_p = float(t.get('Price', t.get('cur_prc', 0))) 

                if not kiwoom_utils.is_valid_stock(code, t['Name'], token=token, current_price=curr_p):
                    already_picked.add(code)
                    continue

                print(f"🎯 [타겟 포착] {t['Name']} (등락/급증률: +{t['ChangeRate']}%, 체결강도: {t['CntrStr']})")
                already_picked.add(code)

                try:
                    with db._get_connection() as conn:
                        conn.execute('''
                                     INSERT INTO recommendation_history 
                                     (date, code, name, buy_price, type, strategy, status)
                                     VALUES (?, ?, ?, ?, ?, ?, 'WATCHING')
                                     ON CONFLICT(date, code) DO UPDATE SET 
                                         strategy = excluded.strategy,
                                         buy_price = excluded.buy_price,
                                         status = 'WATCHING'
                                     WHERE status IN ('WATCHING', 'COMPLETED')
                                     ''', (today, code, t['Name'], 0, 'SCALP', 'SCALPING'))
                        conn.commit()
                except Exception as e:
                    print(f"⚠️ DB 저장 실패: {e}")

        time.sleep(60)

if __name__ == "__main__":
    run_scalper()