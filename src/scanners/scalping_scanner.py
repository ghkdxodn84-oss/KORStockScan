import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import time
from datetime import datetime

# 💡 Level 1 & 2 공통 모듈 임포트
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.core.event_bus import EventBus
from src.engine.signal_radar import SniperRadar


def _resolve_scan_interval_sec(now_time):
    """장 초반/후반에는 더 자주 돌리고, 점심 구간은 약간 완화합니다."""
    hhmm = now_time.hour * 100 + now_time.minute
    if 905 <= hhmm < 1030:
        return 120
    if 1400 <= hhmm <= 1500:
        return 120
    return 180


def _source_priority(source):
    """장중 신선도는 시가대비 상위보다 최근 수급 급증 신호를 더 높게 봅니다."""
    return {
        "BOTH": 0,
        "SUPERNOVA": 1,
        "OPEN_TOP": 2,
    }.get(str(source or "OPEN_TOP"), 3)


def _freshness_score(target):
    """
    `OPEN_TOP`은 하루 종일 순위가 고착되기 쉬워 보조 신호로만 쓰고,
    최근 거래량 급증/체결강도/등락률이 함께 살아난 종목을 앞세웁니다.
    """
    source_bias = {
        "BOTH": 500.0,
        "SUPERNOVA": 300.0,
        "OPEN_TOP": 0.0,
    }.get(str(target.get("Source") or "OPEN_TOP"), 0.0)
    priority_score = float(target.get("PriorityScore", 0.0) or 0.0)
    spike_rate = float(target.get("SpikeRate", 0.0) or 0.0)
    flu_rate = float(target.get("FluRate", 0.0) or 0.0)
    cntr_str = float(target.get("CntrStr", 0.0) or 0.0)
    return source_bias + priority_score + min(spike_rate, 400.0) + (flu_rate * 8.0) + min(cntr_str, 200.0)


# ==========================================
# 🦅 스캘핑 스캐너 (전방 탐색조)
# ==========================================
def run_scalper(is_test_mode=False):
    """
    [역할] 
    2~3분 주기로 시장을 스캔하여 당일 수급이 폭발하거나 급등 전조가 보이는
    '초단타(Scalping)' 타겟을 발굴합니다.
    
    [아키텍처 흐름]
    1. 데이터 수집: kiwoom_utils/signal_radar(REST API)를 호출하여 등락률 상위 및 거래량 급증 종목을 가져옵니다.
    2. 필터링: is_valid_stock을 통해 동전주, ETF, 스팩주 등의 불순물을 걸러냅니다.
    3. DB 저장: 발굴된 종목을 SQLAlchemy ORM을 사용하여 안전하게 Upsert(삽입/업데이트) 합니다.
    4. 이벤트 발행: 'COMMAND_WS_REG' 이벤트를 EventBus에 쏘아, 웹소켓 모듈이 해당 종목의 실시간 틱 데이터 감시를 즉각 시작하도록 지시합니다.
    """
    print("⚡ [SCALPING 스캐너] 초단타 감시 엔진 가동 (장초반/후반 2분, 그 외 3분 주기)...")
    db = DBManager()
    event_bus = EventBus() # 💡 전역 싱글톤 이벤트 버스
    
    today = datetime.now().strftime('%Y-%m-%d')
    # 같은 종목을 하루 종일 영구 제외하면 초반에 잡힌 이름만 오래 남게 됩니다.
    # 그래서 `already_picked` 대신 재등록 cooldown을 둬서, 한동안은 쉬게 하되
    # 다시 거래가 살아난 종목은 같은 날에도 재포착할 수 있게 만듭니다.
    recent_picks = {}
    last_closed_msg_time = 0 # 💡 장 마감 도배 방지용 타이머 추가
    reentry_cooldown_sec = 25 * 60
    max_new_codes = 12
    open_top_limit = 60
    supernova_limit = 30

    # 💡 무한 루프 밖에서 토큰과 레이더를 한 번만 초기화하여 부하 감소
    # (실제 운영 시에는 토큰 만료를 대비한 갱신 로직이 추가로 필요할 수 있음)
    
    token = kiwoom_utils.get_kiwoom_token()
    
    if not token:
        log_error("❌ 키움 토큰 발급 실패. 스캐너를 종료합니다.")
        return

    while True:
        now = datetime.now()
        now_time = now.time()

        # 장 운영 시간 체크 (09:05 ~ 15:00) - 장 초반 감시 5분 후부터 장 마감 1시간 전까지 가동
        market_open = datetime.strptime("09:05:00", "%H:%M:%S").time()
        market_close = datetime.strptime("15:00:00", "%H:%M:%S").time()
        
        if not is_test_mode and not (market_open <= now_time <= market_close):
            if time.time() - last_closed_msg_time > 3600:
                print("🌙 장 마감 혹은 개장 전입니다. 대기 중...")
                last_closed_msg_time = time.time()
            time.sleep(60)
            continue

        scan_interval_sec = _resolve_scan_interval_sec(now_time)

        # `ka10028`은 시가대비 상위라 장중에 얼굴이 잘 안 바뀔 수 있습니다.
        # 따라서 후보 수는 넓게 가져오되, 아래에서 `SUPERNOVA/BOTH`를 우선해
        # stale leader보다 최근에 살아난 종목이 먼저 뽑히게 합니다.
        soaring_targets = kiwoom_utils.get_top_open_fluctuation_ka10028(
            token,
            mrkt_tp="000",
            limit=open_top_limit,
        )
        
        radar = SniperRadar(token) 
        supernova_targets = radar.find_supernova_targets(
            mrkt_tp="000",
            candidate_limit=supernova_limit,
        )
        
        # 병합 단계에서 소스/점수를 같이 들고 가서, 최종 선별은
        # `BOTH -> SUPERNOVA -> OPEN_TOP` 우선순위와 freshness score로 정렬합니다.
        all_targets = {}
        for t in soaring_targets:
            all_targets[t['Code']] = {
                'Code': t['Code'],
                'Name': t['Name'],
                'FluRate': t.get('FluRate', 0.0), # 시가대비 등락률
                'CntrStr': t.get('CntrStr', 0.0),
                'Price': t.get('Price', 0),
                'Source': 'OPEN_TOP',
                'PriorityScore': 0.0,
                'SpikeRate': 0.0,
            }
            
        for t in supernova_targets:
            code = t.get('code', t.get('Code'))
            if code not in all_targets:
                all_targets[code] = {
                    'Code': code,
                    'Name': t.get('name', t.get('Name')),
                    'FluRate': t.get('flu_rate', t.get('FluRate', 0.0)),
                    'CntrStr': t.get('cntr_str', t.get('CntrStr', 150.0)),
                    'Price': t.get('Price', t.get('cur_prc', 0)),
                    'Source': 'SUPERNOVA',
                    'PriorityScore': float(t.get('priority_score', 0.0) or 0.0),
                    'SpikeRate': float(t.get('spike_rate', 0.0) or 0.0),
                }
            else:
                all_targets[code]['Source'] = 'BOTH' # 두 조건 모두 만족하는 초강력 타겟
                all_targets[code]['PriorityScore'] = max(
                    float(all_targets[code].get('PriorityScore', 0.0) or 0.0),
                    float(t.get('priority_score', 0.0) or 0.0),
                )
                all_targets[code]['SpikeRate'] = max(
                    float(all_targets[code].get('SpikeRate', 0.0) or 0.0),
                    float(t.get('spike_rate', 0.0) or 0.0),
                )
            
        new_codes_found = []
        now_ts = time.time()

        # 최근 25분 내 이미 밀어 넣은 종목은 잠시 쉬게 해서 감시 리스트의 회전율을 높입니다.
        # 대신 cooldown이 지나면 같은 날에도 재상승 종목을 다시 잡을 수 있습니다.
        recent_picks = {
            code: picked_at
            for code, picked_at in recent_picks.items()
            if (now_ts - picked_at) < reentry_cooldown_sec
        }

        ranked_targets = sorted(
            all_targets.values(),
            key=lambda item: (
                _source_priority(item.get('Source')),
                -_freshness_score(item),
                -float(item.get('FluRate', 0.0) or 0.0),
            ),
        )

        for t in ranked_targets:
            code = t['Code']
            if code in recent_picks:
                continue

            curr_p = float(t.get('Price', 0))

            if not kiwoom_utils.is_valid_stock(code, t['Name'], token=token, current_price=curr_p):
                recent_picks[code] = now_ts
                continue

            print(
                f"🎯 [타겟 포착] {t['Name']} "
                f"(등락률: +{t['FluRate']}%, 체결강도: {t['CntrStr']}, "
                f"신선도점수: {_freshness_score(t):.1f} | 출처: {t['Source']})"
            )
            recent_picks[code] = now_ts
            new_codes_found.append(code)

            try:
                with db.get_session() as session:
                    today_date = datetime.now().date()

                    record = db.find_reusable_watching_record(
                        session,
                        rec_date=today_date,
                        stock_code=code,
                        strategy='SCALPING',
                    )

                    if record:
                        record.stock_name = t['Name']
                        if record.status in ('WATCHING', 'COMPLETED', 'EXPIRED'):
                            record.strategy = 'SCALPING'
                            record.buy_price = 0
                            record.status = 'WATCHING'
                            record.position_tag = 'SCANNER'
                    else:
                        new_record = RecommendationHistory(
                            rec_date=today_date,
                            stock_code=code,
                            stock_name=t['Name'],
                            buy_price=0,
                            trade_type='SCALP',
                            strategy='SCALPING',
                            status='WATCHING',
                            position_tag='SCANNER'
                        )
                        session.add(new_record)
            except Exception as e:
                log_info(f"⚠️ DB 저장 실패 ({code}): {e}")
            
            if len(new_codes_found) >= max_new_codes:
                break
            
        if new_codes_found:
            event_bus.publish("COMMAND_WS_REG", {"codes": new_codes_found})
            print(f"📡 웹소켓 감시 등록 요청 완료: {len(new_codes_found)} 종목")

        time.sleep(scan_interval_sec)

if __name__ == "__main__":
    run_scalper(is_test_mode=True)
