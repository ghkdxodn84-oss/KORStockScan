import time
import threading
import json
import re # 💡 JSON 파싱 전 마크다운 찌꺼기 제거용
from itertools import cycle
from openai import OpenAI, RateLimitError  # 💡 신규 SDK (openai)
import src.utils.kiwoom_utils as kiwoom_utils
from src.database.db_manager import DBManager
from src.utils.constants import TRADING_RULES, DATA_DIR, CONFIG_PATH, NOTIFY_DIR

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

class GPTSniperEngine:
    # ==========================================
    # 2. ⚙️ 엔진 초기화
    # ==========================================
    def __init__(self, api_keys):
        """OpenAI API 키 리스트로 로테이션 시스템을 구축합니다."""
        if not isinstance(api_keys, list):
            api_keys = [api_keys]
        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys)

        self.current_model_name = 'gpt-4o-mini'
        self._rotate_client()

        self.lock = threading.Lock()
        self.last_call_time = 0
        self.min_interval = 0.5

        # 💡 adaptive cooldown 시스템을 위한 변수들 추가!
        self.rate_limit_history = []  # 최근 발생한 429 time기록 리스트
        self.dynamic_min_interval = 0.5  # 적응형 interval(초기값)
        print(f"🧠 [OpenAI 엔진] {len(self.api_keys)}개 키 로테이션 가동! (모델: {self.current_model_name})")
    
    def _rotate_client(self):
        """새로운 API 키를 꺼내 OpenAI 클라이언트를 교체합니다."""
        self.current_key = next(self.key_cycle)
        self.client = OpenAI(api_key=self.current_key)

    # ==========================================
    # 3. 🛠️ 데이터 포맷팅 (AI 전용 번역기)
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
            ind = kiwoom_utils.calculate_micro_indicators(recent_candles)
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
        if not self.lock.acquire(blocking=False):
            return {"action": "WAIT", "score": 50, "reason": "AI 분석 경합 중"}
            
        last_error_msg = "초기 상태"
            
        try:
            elapsed = time.time() - self.last_call_time
            if elapsed < self.min_interval:
                return {"action": "WAIT", "score": 50, "reason": f"AI 쿨타임 대기 ({self.min_interval}초)"}

            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)

            for attempt in range(len(self.api_keys)):
                try:
                    # 💡 OpenAI Chat API 호출 방식 적용
                    response = self.client.chat.completions.create(
                        model=self.current_model_name,
                        messages=[
                            {"role": "system", "content": SCALPING_SYSTEM_PROMPT},
                            {"role": "user", "content": formatted_data}
                        ],
                        # 💡 강력한 JSON 강제 옵션 (절대 마크다운이나 헛소리를 뱉지 않음)
                        response_format={"type": "json_object"},
                        temperature=0.1 # 스캘핑 봇의 일관된 판단을 위해 온도를 낮춤
                    )
                    
                    self.last_call_time = time.time()
                    
                    # 응답 텍스트 추출 및 JSON 파싱
                    content = response.choices[0].message.content
                    if content:
                        result = json.loads(content)
                        if 'score' not in result:
                            result['score'] = 50
                        else:
                            result['score'] = int(result['score'])
                        return result
                        
                    last_error_msg = "빈 응답 수신"
                    continue
            
                # 💡 OpenAI 전용 Rate Limit(429) 에러 처리
                except RateLimitError as e:
                    kiwoom_utils.log_error(f"⚠️ [{target_name}] API Rate Limit 초과: {e}")
                    last_error_msg = str(e)
                    self.rate_limit_history.append(time.time())
                    if len(self.rate_limit_history) > 20:
                        self.rate_limit_history = self.rate_limit_history[-20:]
                    old_key = self.current_key[-5:]
                    self._rotate_client()
                    print(f"⚠️ [{target_name}] {old_key} 한도 초과(429) -> {self.current_key[-5:]} 교체 ({attempt+1}/{len(self.api_keys)})")
                    continue
                    
                except Exception as e:
                    kiwoom_utils.log_error(f"🚨 [{target_name}] AI 분석 에러: {e}")
                    last_error_msg = str(e)
                    return {"action": "WAIT", "score": 50, "reason": f"API 에러: {last_error_msg}"}
            
            return {"action": "WAIT", "score": 50, "reason": f"모든 키 시도 실패. 에러: {last_error_msg}"}
            
        except Exception as e:
            kiwoom_utils.log_error(f"🚨 [{target_name}] AI 분석 치명적 에러: {e}")
            return {"action": "WAIT", "score": 50, "reason": f"엔진 치명적 에러: {e}"}
        finally:
            self.lock.release()
        
    # ==========================================
    # 5. 📢 [신규] 스캐너 결과 통계 분석 및 브리핑
    # ==========================================
    def analyze_scanner_results(self, total_count, survived_count, stats_text):
        data_input = f"""
[오늘의 스캐너 필터링 통계]
- 총 스캔 대상: {total_count}개 종목
- 최종 생존(매수 감시 대상): {survived_count}개 종목
- 상세 탈락 사유:
{stats_text}
"""
        for attempt in range(len(self.api_keys)):
            try:
                # 브리핑은 자연어로 받아야 하므로 response_format을 빼고 호출합니다.
                response = self.client.chat.completions.create(
                    model=self.current_model_name,
                    messages=[
                        {"role": "system", "content": MARKET_ANALYSIS_PROMPT},
                        {"role": "user", "content": data_input}
                    ],
                    temperature=0.7 # 텍스트 생성에는 약간의 창의성을 허용
                )
                return response.choices[0].message.content.strip()
                
            except RateLimitError:
                self.rate_limit_history.append(time.time())
                if len(self.rate_limit_history) > 20:
                    self.rate_limit_history = self.rate_limit_history[-20:]
                self._rotate_client()
                continue
            except Exception as e:
                kiwoom_utils.log_error(f"🚨 [AI 브리핑 에러] {e}")
                print(f"🚨 [AI 브리핑 에러] {e}")
                return f"⚠️ AI 시장 진단 중 에러가 발생했습니다. (사유: {e})"
                    
        return "⚠️ 모든 AI 모델의 쿼타가 소진되어 시장 진단을 생성할 수 없습니다."
    
    def analyze_morning_leader(self, stock_name, ws_data, recent_ticks, recent_candles):
        """
        [v12.8 -> GPT-4o-mini] 기존 고도화된 포맷을 활용한 09:05 주도주 분석
        """
        # 1. 기존 포맷 함수로 데이터 정제
        formatted_context = self._format_market_data(ws_data, recent_ticks, recent_candles)

        # 2. 시스템 프롬프트 구성 (역할 및 JSON 구조 강제)
        system_prompt = """
너는 대한민국 최고의 스캘핑 전문가이자 데이터 분석가야.
아래 제공된 실시간 수급 및 기술적 지표를 분석하여 09:05 이후의 전략을 제시하라.

반드시 다음 JSON 구조로만 응답하라:
{
    "one_liner": "종목에 대한 한 줄 평 (핵심 수급 요약)",
    "pattern": "현재 차트에서 발견된 기술적 패턴 명칭",
    "scenario": "향후 30분 내 예상 주가 흐름",
    "target_price": "최적의 눌림목 진입 단가 (숫자만)",
    "risk_factor": "진입 시 반드시 체크해야 할 리스크 요소"
}
"""
        # 3. 유저 프롬프트 구성 (실시간 데이터)
        user_prompt = f"[{stock_name}] 분석 데이터:\n{formatted_context}"

        last_error_msg = "초기 상태"

        # 4. 안전한 로테이션 및 API 호출 루프
        for attempt in range(len(self.api_keys)):
            try:
                response = self.client.chat.completions.create(
                    model=self.current_model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},  # 💡 강력한 JSON 강제
                    temperature=0.2 # 객관적이고 일관된 분석을 위해 낮은 온도 유지
                )
                
                content = response.choices[0].message.content
                if content:
                    # 💡 원본은 response.text(문자열)를 리턴했지만, 
                    # 파이썬 딕셔너리로 바로 파싱해서 리턴하는 것이 KORStockScan 로직 처리에 훨씬 안전합니다.
                    return json.loads(content)
                    
                last_error_msg = "빈 응답 수신"
                continue

            except RateLimitError as e:
                kiwoom_utils.log_error(f"⚠️ [{stock_name}] 주도주 분석 API Rate Limit 초과: {e}")
                last_error_msg = str(e)
                self.rate_limit_history.append(time.time())
                if len(self.rate_limit_history) > 20:
                    self.rate_limit_history = self.rate_limit_history[-20:]
                old_key = self.current_key[-5:]
                self._rotate_client()
                print(f"⚠️ [{stock_name} 주도주 분석] {old_key} 한도 초과(429) -> {self.current_key[-5:]} 교체 ({attempt+1}/{len(self.api_keys)})")
                continue

            except Exception as e:
                kiwoom_utils.log_error(f"🚨 [{stock_name}] 주도주 분석 에러: {e}")
                last_error_msg = str(e)
                # 다른 일반 에러 시 JSON 형태로 에러 사유 반환
                return {"error": f"API 에러: {last_error_msg}"}
        
        return {"error": f"모든 키 시도 실패. 마지막 에러: {last_error_msg}"}
    
    # ==========================================
    # 6. 🔍 [신규] 수동 종목 정밀 분석 (일봉 + 실시간 수급)
    # ==========================================
    def generate_manual_report(self, stock_code, stock_name, db_manager, ws_manager, radar_manager):
        """
        [GPT-4o-mini] 수동 종목 분석의 'A to Z'를 담당하는 컨트롤러
        직접 DB, WS, Radar에서 데이터를 수집하고 AI 분석 결과를 반환합니다.
        """
        # 1. 📂 데이터 레이어 호출: 로컬 DB 일봉 데이터 수집
        db_df = db_manager.get_daily_data(stock_code, limit=20) 
        if db_df is None or db_df.empty:
            return {"error": "로컬 DB에 일봉 데이터가 부족하여 분석할 수 없습니다."}

        # 2. 🔌 데이터 레이어 호출: 실시간 웹소켓 수집
        ws_data = ws_manager.get_latest_data(stock_code)
        if not ws_data or ws_data.get('curr', 0) == 0:
            # 장 시작 전이거나 감시 등록이 안된 경우 DB의 마지막 종가로 Fallback
            ws_data = {'curr': int(db_df.iloc[-1]['Close']), 'fluctuation': 0.0, 'volume': 0}

        # 3. 📡 데이터 레이어 호출: 레이더(수급) 수집
        program_buy = radar_manager.check_program_buying_ka90008(stock_code)
        v_pw_pass = radar_manager.check_execution_strength_ka10046(stock_code)

        # ==========================================
        # 4. 수집된 데이터 가공 (Formatting)
        # ==========================================
        recent_20 = db_df.tail(20)
        df_for_ai = recent_20[['Date', 'Close', 'Volume', 'MA5', 'MA20', 'MA60', 'RSI', 'MACD', 'BBU']].copy().round(1)
        history_str = df_for_ai.to_json(orient='records', force_ascii=False)
        avg_vol_20d = recent_20['Volume'].mean()
        
        curr_price = ws_data.get('curr', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)
        today_vol = ws_data.get('volume', 0)
        vol_ratio = (today_vol / avg_vol_20d * 100) if avg_vol_20d > 0 else 0
        
        program_str = "외인/기관 대량 순매수 유입 (강세)" if program_buy else "유의미한 대량 순매수 미확인"
        v_pw = ws_data.get('v_pw', 0.0)
        v_pw_str = f"{v_pw}% (강세 구간)" if v_pw_pass else f"{v_pw}% (보통/약세 구간)"

        # ==========================================
        # 5. AI 프롬프트 생성 및 호출
        # ==========================================
        system_prompt = """
너는 주식 시장의 최상위 기술적 분석가이자 트레이딩 코치야.
제공된 일봉 흐름과 장중 수급 데이터를 입체적으로 분석하여 진단하라.
"""
        user_input = f"""
[종목명: {stock_name}]
- 현재가: {curr_price:,}원 (전일비 {fluctuation}%)
- 누적 거래량: {today_vol:,}주 (20일 평균대비 {vol_ratio:.1f}%)
- 체결강도: {v_pw_str}
- 프로그램 순매수: {program_str}

[최근 20일 데이터]
{history_str}

아래 JSON으로만 응답해:
{{
    "trend": "추세 1줄 요약",
    "target": 목표가 숫자,
    "reason": "목표가 근거",
    "stop": 손절가 숫자,
    "action": "매매 지침"
}}
"""
        last_error = "초기화 전"
        for attempt in range(len(self.api_keys)):
            try:
                response = self.client.chat.completions.create(
                    model=self.current_model_name,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                    response_format={"type": "json_object"},
                    temperature=0.2 
                )
                return json.loads(response.choices[0].message.content)
            except RateLimitError as e:
                kiwoom_utils.log_error(f"⚠️ [{stock_name}] 주도주 분석 API Rate Limit 초과: {e}")
                last_error_msg = str(e)
                self.rate_limit_history.append(time.time())
                if len(self.rate_limit_history) > 20:
                    self.rate_limit_history = self.rate_limit_history[-20:]
                old_key = self.current_key[-5:]
                self._rotate_client()
                print(f"⚠️ [{stock_name} 주도주 분석] {old_key} 한도 초과(429) -> {self.current_key[-5:]} 교체 ({attempt+1}/{len(self.api_keys)})")
                continue
            except Exception as e:
                kiwoom_utils.log_error(f"🚨 [{stock_name}] 주도주 분석 에러: {e}")
                return {"error": str(e)}

        return {"error": f"API 호출 실패: {last_error}"}
    
    # ==========================================
    # 7. 🛠️ 최근 1분간 429 빈도 체크
    # ==========================================
    def _recalculate_cooldown(self):
        # 최근 1분간 429 빈도 체크
        window = 60
        now = time.time()
        recent_rls = [t for t in self.rate_limit_history if now - t < window]
        boost = 0.5 + 0.25 * min(len(recent_rls), 10)
        self.min_interval = max(boost, 0.5)  # 0.5~3.0초 가변