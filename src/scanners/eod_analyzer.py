import sys
import os
import json
import pandas as pd
from pathlib import Path

# 1. KORStockScan 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.utils.constants import CONFIG_PATH, DEV_PATH

def load_config():
    """환경에 맞는 설정 파일(JSON)을 로드합니다."""
    target_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else DEV_PATH
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 설정 파일 로드 실패: {e}")
        return {}

def extract_eod_candidates(db_manager):
    """최근 5일 데이터를 분석하여 내일의 주도주 후보 15종목을 추출합니다."""
    print("🔍 [데이터 추출] VCP 패턴 및 메이저 수급 매집 종목을 스캔합니다...")
    
    # 최근 5영업일 데이터 가져오기 (PostgreSQL 쿼리)
    query = """
    WITH RecentDates AS (
        SELECT DISTINCT quote_date FROM daily_stock_quotes ORDER BY quote_date DESC LIMIT 5
    )
    SELECT * FROM daily_stock_quotes 
    WHERE quote_date IN (SELECT quote_date FROM RecentDates)
    """
    df = pd.read_sql(query, db_manager.engine)
    if df.empty: return ""

    candidates = []
    grouped = df.groupby('stock_code')

    for code, group in grouped:
        group = group.sort_values('quote_date').reset_index(drop=True)
        if len(group) < 5: continue

        today_data = group.iloc[-1]
        
        # [조건 1] 잡주 배제: 종가 5,000원 이상, 시총 1,000억 이상
        if today_data['close_price'] < 5000 or today_data['marcap'] < 1000_000_000_00:
            continue
        
        # [조건 2] 추세 방어: 종가가 20일선 위 (정배열 초입)
        if today_data['close_price'] <= today_data['ma20']:
            continue
            
        # [조건 3] RSI 과열 방지 및 에너지 비축 (45 ~ 68 사이)
        if not (45 <= today_data['rsi'] <= 68):
            continue

        # [조건 4] 스마트머니(수급) 매집: 최근 3일 외인 or 기관 순매수 합산
        last_3_days = group.iloc[-3:]
        foreign_sum = last_3_days['foreign_net'].sum()
        inst_sum = last_3_days['inst_net'].sum()
        
        # 둘 다 팔고 나갔다면 세력 이탈로 간주
        if foreign_sum <= 0 and inst_sum <= 0:
            continue 

        # [조건 5] 에너지 응축 (거래량 급감): 오늘 거래량이 5일 평균 대비 120% 미만일 것
        avg_vol = group['volume'].mean()
        vol_ratio = today_data['volume'] / avg_vol if avg_vol > 0 else 1.0
        if vol_ratio > 1.2: 
            continue # 거래량이 터진 상태면 내일 쉬어갈 확률 높음

        # [조건 6] 볼린저밴드 스퀴즈 (폭이 좁을수록 폭발력이 큼)
        bbu = today_data.get('bbu', 0)
        bbl = today_data.get('bbl', 0)
        bb_width = (bbu - bbl) / today_data['close_price'] if bbu > 0 else 999
        
        candidates.append({
            'code': code,
            'name': today_data['stock_name'],
            'close_price': today_data['close_price'],
            'foreign_sum': foreign_sum,
            'inst_sum': inst_sum,
            'rsi': today_data['rsi'],
            'macd_hist': today_data.get('macd_hist', 0),
            'bb_width': bb_width,
            'vol_ratio': vol_ratio
        })

    # 후보군 정렬: 볼린저밴드 폭이 좁으면서(응축), 메이저 수급이 많은 순으로 Top 15 추출
    candidates_df = pd.DataFrame(candidates)
    if candidates_df.empty: return ""
    
    candidates_df = candidates_df.sort_values(by=['bb_width', 'foreign_sum'], ascending=[True, False]).head(15)
    
    # AI에게 먹여줄 텍스트 포맷팅
    report_text = ""
    for idx, row in candidates_df.iterrows():
        report_text += f"🔹 [{row['name']}] ({row['code']})\n"
        report_text += f" - 종가: {int(row['close_price']):,}원 (RSI: {row['rsi']:.1f}, BB폭: {row['bb_width']*100:.1f}%)\n"
        report_text += f" - 3일 누적수급: 외인 {int(row['foreign_sum']):,}주 / 기관 {int(row['inst_sum']):,}주\n"
        report_text += f" - 거래량 상태: 5일 평균대비 {row['vol_ratio']*100:.0f}% (에너지 응축중)\n"
        report_text += f" - MACD 히스토그램: {row['macd_hist']:.2f}\n\n"
    
    return report_text

if __name__ == "__main__":
    print("🌙 [종가베팅 분석기] 장 마감 후 데이터 기반 분석 시작...")
    
    # 1. 설정 및 DB 로드
    CONF = load_config()
    db = DBManager()
    
    # 2. 데이터 추출
    candidates_text = extract_eod_candidates(db)
    
    if not candidates_text:
        print("⚠️ 조건을 만족하는 주도주 후보군이 없습니다. (오늘 장이 매우 안 좋았거나 데이터 갱신 필요)")
        sys.exit(0)
        
    print("✅ 1차 필터링 완료! Gemini 3.0 Pro 수석 애널리스트에게 분석을 요청합니다...")
    
    # 3. AI 분석 엔진 호출을 위한 API Key 확보
    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]
    
    if not api_keys:
        print("🚨 설정 파일(json)에 GEMINI_API_KEY가 없습니다.")
        sys.exit(1)
        
    try:
        from src.engine.ai_engine import GeminiSniperEngine
        ai_engine = GeminiSniperEngine(api_keys=api_keys)
        
        # 💡 장 마감 분석 전용 프롬프트 및 gemini-3.0-pro 호출
        final_report = ai_engine.generate_eod_tomorrow_report(candidates_text)
        
        print("\n" + "="*50)
        print(final_report)
        print("="*50 + "\n")
        
        # 4. 텔레그램으로 전송
        event_bus = EventBus()
        import src.notify.telegram_manager # 텔레그램 리스너 연결 및 봇 초기화
        
        event_bus.publish('TELEGRAM_BROADCAST', {'message': final_report, 'audience': 'VIP_ALL'})
        print("🚀 텔레그램 VIP 채널로 마감 브리핑 전송 완료!")
        
    except Exception as e:
        print(f"🚨 AI 분석 또는 전송 중 에러 발생: {e}")