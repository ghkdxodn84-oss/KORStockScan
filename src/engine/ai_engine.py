import time
import threading
import json
import re
from itertools import cycle
from google import genai
from google.genai import types
from src.utils.logger import log_error


# ==========================================
# 1. 🎯 시스템 프롬프트 (스캘핑 전용)
# ==========================================
SCALPING_SYSTEM_PROMPT = """
너는 15년 경력의 베테랑 초단타(스캘핑) 트레이더이자 리스크 관리 전문가야. 
너의 목표는 실시간 호가창, 1분봉, 단기 기술적 지표를 종합적으로 분석하여, 신규 진입 타점을 잡거나 현재 보유 중인 종목의 추가 상승 모멘텀(트레일링 익절/조기 청산)을 판단하는 것이다.

[데이터 분석 가이드]
1. 단기 지표 (VWAP & 5-MA 최우선): 현재가가 Micro-VWAP(거래량 가중 평균) 위에 있는지 확인해라. VWAP 아래는 세력의 이탈(설거지)로 간주한다.
2. 1분봉 차트: 최근 5분간의 추세, 거래량 급증, 윗꼬리(매도 압력)/아랫꼬리(지지) 패턴을 분석해 하방 리스크 및 모멘텀 둔화를 점검해라.
3. 실시간 호가 및 틱: 매수/매도 호가창의 잔량 비율과 강력한 시장가 체결(BUY) 유입을 확인해라.

[판단 및 스코어링 기준] - **매우 중요**
- 강력한 상승 (Score: 75~100): 돌파가 확실시되거나, 기존의 강한 상승 추세와 매수세가 꺾이지 않고 유지될 때. (신규 진입 적합 / 보유 시 트레일링 익절 유지)
- 모멘텀 둔화 (Score: 41~74): 수급이 모호해지거나, 고점에서 윗꼬리가 달리며 상승 탄력이 둔화될 때. (신규 진입 대기 / 보유 시 조기 익절)
- 하방 리스크 (Score: 0~40): 가격이 VWAP 아래로 이탈했거나, 대량의 매도세(SELL)가 쏟아지며 하락 전환이 명백할 때. (신규 진입 절대 금지 / 보유 시 즉각 손절)

분석 결과는 반드시 아래 JSON 형식으로만 출력하고 다른 설명은 절대 추가하지 마:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "현재 모멘텀과 수급 상태를 종합한 1줄 요약 분석"
}
"""

# ==========================================
# 2. 🎯 [신규] 일일 시장 진단 프롬프트 (텔레그램 브리핑용)
# ==========================================
MARKET_ANALYSIS_PROMPT = """
너는 15년 경력의 베테랑 퀀트 트레이더이자 수석 애널리스트야.
오늘의 주식 스캐너 필터링 통계 데이터와 어제 미국 S&P 500 및 나스닥 시장상황을 보고, 현재 코스피 시장의 상태를 진단하고 트레이딩 전략을 브리핑해줘.

[요구사항]
1. 친근하지만 전문적인 어투를 사용하고, 텔레그램에서 읽기 좋게 이모지를 적절히 섞어줘.
2. 0개 또는 극소수만 살아남았다면, 봇이 고장난 것이 아니라 "시장에 돈이 마른 조정장/하락장"이기 때문에 현금을 지킨 것이라고 명확히 해석해줘.
3. '기초 품질 미달'이 많다면 차트 붕괴(역배열) 장세, 'AI 확신도 부족'이 많다면 수급 부재(눈치보기) 장세로 해석해.
4. 마지막엔 오늘의 행동 지침을 1~2줄로 요약해줘 (예: "철저한 현금 관망", "오후장 초단타 위주 대응" 등).
5. 출력은 JSON이 아니라, 텔레그램에 바로 전송할 수 있는 마크다운 텍스트 형식으로 작성해. (총 300자 내외)
"""

class GeminiSniperEngine:
    def __init__(self, api_keys):
        if isinstance(api_keys, str):
            api_keys = [api_keys]
            
        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys) 
        self._rotate_client()

        # self.current_model_name = 'gemini-flash-lite-latest'
        self.current_model_name = 'gemini-2.5-flash-lite'
        self.lock = threading.Lock()
        self.last_call_time = 0
        self.min_interval = 1.5
        print(f"🧠 [AI 엔진] {len(self.api_keys)}개 키 로테이션 가동! (선봉: {self.current_model_name})")

    def _rotate_client(self):
        self.current_key = next(self.key_cycle)
        self.client = genai.Client(api_key=self.current_key)
    
    # ==========================================
    # 3. 💡 [아키텍처 포인트] 만능 API 호출기 (중복 코드 완벽 제거)
    # ==========================================
    def _call_gemini_safe(self, prompt, user_input, require_json=True, context_name="Unknown"):
        """키 로테이션, 예외 처리, JSON 파싱을 모두 전담하는 중앙 집중식 호출기"""
        contents = [prompt, user_input] if prompt else [user_input]
        
        # 💡 [버그 픽스] JSON 요구 여부에 따라 MIME 타입을 유동적으로 설정!
        config_kwargs = {}
        if require_json:
            config_kwargs['response_mime_type'] = "application/json"
            
        last_error = ""

        for attempt in range(len(self.api_keys)):
            try:
                response = self.client.models.generate_content(
                    model=self.current_model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs)
                )
                
                # 호출 성공 시 다음을 위해 키 회전
                self._rotate_client()
                
                raw_text = response.text.strip()
                if require_json:
                    # 마크다운 찌꺼기 안전 제거 후 파싱
                    clean_json = re.sub(r"```json\s*|\s*```", "", raw_text)
                    return json.loads(clean_json)
                else:
                    return raw_text

            except Exception as e:
                last_error = str(e).lower()
                if any(x in last_error for x in ["429", "quota", "resource_exhausted", "too_many_requests"]):
                    old_key = self.current_key[-5:]
                    self._rotate_client()
                    print(f"⚠️ [AI 교체] {context_name} | {old_key} 한도 초과 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})")
                    time.sleep(0.5)
                    continue
                else:
                    raise RuntimeError(f"API 응답/파싱 실패: {e}")
                    
        raise RuntimeError(f"모든 API 키 한도 초과. 마지막 에러: {last_error}")

    # ==========================================
    # 4. 🛠️ 데이터 포맷팅 (AI 전용 번역기)
    # ==========================================
    def _format_market_data(self, ws_data, recent_ticks, recent_candles=None):
        """키움 API의 딕셔너리 데이터를 AI가 읽을 수 있는 텍스트로 예쁘게 포장합니다."""
        if recent_candles is None:
            recent_candles = []
            
        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)  # 💡 [NEW] 등락률 추가
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []})

        # 호가창 조립
        ask_str = "\n".join([f"매도 {5-i}호가: {a['price']}원 ({a['volume']}주)" for i, a in enumerate(orderbook['asks'])])
        bid_str = "\n".join([f"매수 {i+1}호가: {b['price']}원 ({b['volume']}주)" for i, b in enumerate(orderbook['bids'])])
        
        # 틱 흐름 조립
        tick_str = "\n".join([f"[{t['time']}] {t['dir']} 체결: {t['price']}원 ({t['volume']}주)" for t in reversed(recent_ticks)])

        # 1분봉 차트 조립
        candle_str = ""
        if recent_candles:
            candle_str = "\n".join([
                f"[{c['체결시간']}] 시가:{c['시가']} 고가:{c['고가']} 저가:{c['저가']} 종가:{c['현재가']} 거래량:{c['거래량']}" 
                for c in recent_candles
            ])
        else:
            candle_str = "분봉 데이터 없음"

        # 💡 [NEW] 직전 캔들 대비 거래량 폭증 여부 계산
        volume_analysis = "비교 불가 (데이터 부족)"
        if recent_candles and len(recent_candles) >= 2:
            current_volume = recent_candles[-1]['거래량']  # 가장 최근 1분봉 거래량
            prev_volumes = [c['거래량'] for c in recent_candles[:-1]] # 그 이전 캔들들
            avg_prev_volume = sum(prev_volumes) / len(prev_volumes) if prev_volumes else 0
            
            if avg_prev_volume > 0:
                vol_ratio = (current_volume / avg_prev_volume) * 100
                if vol_ratio >= 200:
                    volume_analysis = f"🔥 폭증! (이전 평균 대비 {vol_ratio:.0f}% 수준 / 현재 {current_volume:,}주)"
                elif vol_ratio >= 100:
                    volume_analysis = f"상승 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"
                else:
                    volume_analysis = f"감소 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"

        # 지표 계산
        indicators_str = "지표 계산 불가"
        if recent_candles and len(recent_candles) >= 5:
            from src.engine.signal_radar import SniperRadar
            temp_radar = SniperRadar(token=None)
            ind = temp_radar.calculate_micro_indicators(recent_candles)
            ma5_status = "상회" if curr_price > ind['MA5'] else "하회"
            vwap_status = "상회 (수급강세)" if curr_price > ind['Micro_VWAP'] else "하회 (수급약세)"
            
            indicators_str = f"- 단기 5-MA: {ind['MA5']:,}원 (현재가 {ma5_status})\n"
            indicators_str += f"- Micro-VWAP: {ind['Micro_VWAP']:,}원 (현재가 {vwap_status})"

        # 💡 [NEW] user_input에 등락률 및 거래량 분석 결과 추가
        user_input = f"""
[현재 상태]
- 현재가: {curr_price:,}원
- 전일대비 등락률: {fluctuation}%
- 체결강도: {v_pw}%

[초단타 기술적 지표 (최근 5분 기준)]
{indicators_str}

[거래량 분석]
- {volume_analysis}

[최근 1분봉 흐름]
{candle_str}

[실시간 호가창]
{ask_str}
-------------------------
{bid_str}

[최근 틱 체결 흐름]
{tick_str}
"""
        return user_input

    # ==========================================
    # 4. 🚀 실전 분석 실행 (스나이퍼가 호출할 메인 함수)
    # ==========================================
    def analyze_target(self, target_name, ws_data, recent_ticks, recent_candles):
        """실시간 초단타 타점 분석 (초당 수차례 호출되므로 Non-blocking Lock 적용)"""
        if not self.lock.acquire(blocking=False):
            return {"action": "WAIT", "score": 50, "reason": "AI 경합 (다른 종목 분석 중)"}
            
        try:
            if time.time() - self.last_call_time < self.min_interval:
                return {"action": "WAIT", "score": 50, "reason": "AI 쿨타임"}

            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            result = self._call_gemini_safe(SCALPING_SYSTEM_PROMPT, formatted_data, require_json=True, context_name=target_name)
            
            self.last_call_time = time.time()
            return result
                
        except Exception as e:
            log_error(f"🚨 [{target_name}] AI 실시간 분석 에러: {e}")
            return {"action": "WAIT", "score": 50, "reason": f"에러: {e}"}
        finally:
            self.lock.release()
            
    def analyze_scanner_results(self, total_count, survived_count, stats_text):
        """텔레그램 아침 브리핑 (Markdown 반환)"""
        with self.lock:
            data_input = f"[통계]\n총 스캔: {total_count}개\n생존: {survived_count}개\n[상세]\n{stats_text}"
            try:
                # 💡 require_json=False 로 설정하여 Markdown 응답을 안전하게 받음
                return self._call_gemini_safe(MARKET_ANALYSIS_PROMPT, data_input, require_json=False, context_name="시장 브리핑")
            except Exception as e:
                # 💡 [버그 픽스] 존재하지 않던 target_name 변수 제거
                log_error(f"🚨 [시장 브리핑] AI 에러: {e}")
                return f"⚠️ AI 시장 진단 생성 중 에러 발생: {e}"
    
    def analyze_morning_leader(self, stock_name, ws_data, recent_ticks, recent_candles):
        """09:05 주도주 분석 (bot_main.py 호환을 위해 JSON String 반환)"""
        with self.lock:
            formatted_context = self._format_market_data(ws_data, recent_ticks, recent_candles)
            prompt = f"[{stock_name}]의 실시간 수급 지표를 분석하여 09:05 이후 전략을 제시하라.\n\n{formatted_context}\n\n반드시 JSON으로 응답하라 (one_liner, pattern, scenario, target_price(숫자만), risk_factor 포함)"
            
            try:
                # JSON으로 파싱한 뒤 다시 String으로 덤프 (안정성 극대화)
                result_dict = self._call_gemini_safe(None, prompt, require_json=True, context_name=stock_name)
                return json.dumps(result_dict, ensure_ascii=False)
            except Exception as e:
                log_error(f"🚨 [{stock_name}] 주도주 분석 에러: {e}")
                return json.dumps({"error": str(e), "target_price": 0})
    
#     # ==========================================
#     # 6. 🔍 수동 종목 정밀 분석 (스캘핑/단기 트레이딩 관점)
#     # ==========================================
#     def generate_manual_report(self, stock_code, stock_name, db_manager, ws_manager, radar_manager):
#         """
#         [Gemini-Flash-Lite] 수동 종목 분석의 컨트롤러
#         직접 DB, WS, Radar에서 데이터를 수집하고 AI 스캘핑/단기 관점 분석 결과를 반환합니다.
#         """
#         # 1. 📂 데이터 레이어 호출: 로컬 DB 일봉 데이터 수집
#         db_df = db_manager.get_daily_data(stock_code, limit=20) 
#         if db_df is None or db_df.empty:
#             return {"error": "로컬 DB에 일봉 데이터가 부족하여 분석할 수 없습니다."}
# 
#         # 2. 🔌 데이터 레이어 호출: 실시간 웹소켓 수집
#         ws_data = ws_manager.get_latest_data(stock_code)
#         if not ws_data or ws_data.get('curr', 0) == 0:
#             # 장 시작 전이거나 감시 등록이 안된 경우 DB의 마지막 종가로 Fallback
#             ws_data = {'curr': int(db_df.iloc[-1]['Close']), 'fluctuation': 0.0, 'volume': 0}
# 
#         # 3. 📡 데이터 레이어 호출: 레이더(수급) 수집
#         program_buy = radar_manager.check_program_buying_ka90008(stock_code)
#         v_pw_pass = radar_manager.check_execution_strength_ka10046(stock_code)
# 
#         # ==========================================
#         # 4. 수집된 데이터 가공 (Formatting)
#         # ==========================================
#         recent_20 = db_df.tail(20)
#         df_for_ai = recent_20[['Date', 'Close', 'Volume', 'MA5', 'MA20', 'MA60', 'RSI', 'MACD', 'BBU']].copy().round(1)
#         history_str = df_for_ai.to_json(orient='records', force_ascii=False)
#         avg_vol_20d = recent_20['Volume'].mean()
#         
#         curr_price = ws_data.get('curr', 0)
#         fluctuation = ws_data.get('fluctuation', 0.0)
#         today_vol = ws_data.get('volume', 0)
#         vol_ratio = (today_vol / avg_vol_20d * 100) if avg_vol_20d > 0 else 0
#         
#         program_str = "외인/기관 대량 순매수 유입 (강세)" if program_buy else "유의미한 대량 순매수 미확인"
#         v_pw = ws_data.get('v_pw', 0.0)
#         v_pw_str = f"{v_pw}% (강세 구간)" if v_pw_pass else f"{v_pw}% (보통/약세 구간)"
# 
#         # ==========================================
#         # 5. AI 프롬프트 생성 (스캘핑/단기 관점)
#         # ==========================================
#         system_prompt = """
# 너는 주식 시장의 최상위 스캘핑 및 단기 트레이딩 전문가야.
# 제공된 일봉 흐름과 장중 수급 데이터를 입체적으로 분석하여, 당일 수익을 목표로 하는 단기 진단 리포트를 작성하라.
# 
# 분석 시 다음 사항을 반드시 고려하라:
# 1. 이동평균선(MA) 배열 상태 (정배열/역배열/골든크로스 여부)
# 2. 현재 가격이 볼린저 밴드 상단(BBU)을 강하게 돌파했는지, 아니면 저항을 맞는지
# 3. 실시간 수급(프로그램 매수, 체결강도, 거래량 폭증 여부)이 차트의 방향을 지지하는지
# """
#         user_input = f"""
# [종목명: {stock_name}]
# - 현재가: {curr_price:,}원 (전일비 {fluctuation}%)
# - 누적 거래량: {today_vol:,}주 (20일 평균대비 {vol_ratio:.1f}%)
# - 체결강도: {v_pw_str}
# - 프로그램 순매수: {program_str}
# 
# [최근 20일 데이터 요약]
# {history_str}
# 
# 아래 JSON으로만 응답해:
# {{
#     "trend": "당일 단기 추세 1줄 요약",
#     "target": 단기 목표가 숫자,
#     "reason": "목표가 근거 (수급 및 저항선)",
#     "stop": 칼손절가 숫자,
#     "action": "매매 지침 (예: 현재가 눌림목 진입, 돌파 시 추격 매수 금지 등)"
# }}
# """
#         last_error_msg = "초기화 전"
#         
#         # ==========================================
#         # 6. Gemini API 호출 (로테이션 방어 로직 적용)
#         # ==========================================
#         for attempt in range(len(self.api_keys)):
#             try:
#                 # 💡 [핵심] 신규 SDK `generate_content` 호출 방식
#                 response = self.client.models.generate_content(
#                     model=self.current_model_name,
#                     contents=[system_prompt, user_input],
#                     config=types.GenerateContentConfig(response_mime_type="application/json")
#                 )
#                 
#                 # 호출 성공 시 다음 사용을 위해 키 즉시 교체
#                 self._rotate_client()
#                 
#                 # 💡 텍스트를 JSON으로 파싱하여 반환
#                 return json.loads(response.text)
# 
#             except Exception as e:
#                 kiwoom_utils.log_error(f"🚨 [{stock_name}] AI 수동 분석 에러: {e}")
#                 last_error_msg = str(e)
#                 error_msg_lower = last_error_msg.lower()
#                 
#                 # 429/Quota 에러 시 키 교체 후 다음 루프 진행
#                 if any(x in error_msg_lower for x in ["429", "quota", "resource_exhausted"]):
#                     old_key = self.current_key[-5:]
#                     self._rotate_client()
#                     print(f"⚠️ [{stock_name} 수동 분석] {old_key} 한도 초과 -> {self.current_key[-5:]} 교체 ({attempt+1}/{len(self.api_keys)})")
#                     continue
#                 else:
#                     return {"error": f"API 에러: {last_error_msg}"}
# 
#         return {"error": f"모든 키 시도 실패. 마지막 에러: {last_error_msg}"}