import json
import google.generativeai as genai
import kiwoom_utils

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
    # ==========================================
    # 2. ⚙️ 엔진 초기화
    # ==========================================
    def __init__(self, api_key):
        """설정 파일에서 읽어온 API 키로 Gemini 엔진을 가동합니다."""
        genai.configure(api_key=api_key)
        # 스캘핑은 스피드가 생명이므로 flash 모델 사용
        # 💡 [핵심 1] 사용할 모델들의 우선순위 리스트 (가장 좋은 모델부터 배치)
        self.model_list = [
            'gemini-3.1-flash-lite-preview',  # 3.1 라이트
            'gemini-3-flash-preview',        # 3.0 플래시
            'gemini-2.5-flash',
            'gemini-2.5-flash-lite',         # 2.5 라이트
            'gemini-2.5-flash-lite-preview-09-2025'
        ]
        
        # 현재 사용 중인 모델의 인덱스
        self.current_idx = 0 
        self._set_current_model()
        print(f"🧠 [AI 엔진] 멀티 모델 로테이션 가동! (선봉장: {self.model_list[0]})")
    
    def _set_current_model(self):
        """현재 인덱스에 맞는 모델로 교체합니다."""
        model_name = self.model_list[self.current_idx]
        self.model = genai.GenerativeModel(model_name)

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

[최근 1분봉 흐름 (opt10080)]
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
    # 💡 [핵심 2] 장전된 모델의 개수만큼 최대 재시도(Retry)를 허용합니다.
    def analyze_target(self, target_name, ws_data, recent_ticks, recent_candles):
        formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
        
        # 💡 [핵심 2] 장전된 모델의 개수만큼 최대 재시도(Retry)를 허용합니다.
        max_retries = len(self.model_list)
        
        for attempt in range(max_retries):
            try:
                # 1. 현재 설정된 모델로 호출 시도 (💡 generation_config 추가!)
                response = self.model.generate_content(
                    [SCALPING_SYSTEM_PROMPT, formatted_data],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # JSON 모드이므로 이제 replace("```json"...) 같은 지저분한 청소 코드가 필요 없습니다!
                cleaned_text = response.text.strip()
                result = json.loads(cleaned_text)
                
                if 'score' not in result:
                    result['score'] = 50
                else:
                    result['score'] = int(result['score'])
                    
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # 2. 쿼타 초과(429) 에러인지 확인
                if "429" in error_msg or "quota" in error_msg:
                    current_name = self.model_list[self.current_idx]
                    print(f"⚠️ [{target_name}] {current_name} 한도 초과! 바통 터치 준비...")
                    
                    # 3. 다음 모델로 인덱스 이동 (끝에 도달하면 다시 0번으로)
                    self.current_idx = (self.current_idx + 1) % len(self.model_list)
                    self._set_current_model()
                    
                    next_name = self.model_list[self.current_idx]
                    print(f"🔄 [AI 교체 완료] 이제부터 {next_name} 모델이 투입됩니다!")
                    
                    # continue를 통해 바뀐 모델로 for 문을 다시 돕니다(재시도).
                    continue 
                else:
                    # 쿼타 에러가 아닌 진짜 통신/파싱 에러면 그냥 대기(WAIT) 처리
                    print(f"🚨 [{target_name}] AI 통신/파싱 에러: {e}")
                    return {"action": "WAIT", "score": 50, "reason": "API 통신 또는 파싱 에러"}
        
        # 4. 모든 모델이 다 뻗어버린 최악의 경우
        print(f"🚨 [{target_name}] 준비된 모든 AI 모델의 총알(쿼타)이 소진되었습니다.")
        return {"action": "WAIT", "score": 50, "reason": "전체 AI 쿼타 소진"}
    
    # ==========================================
    # 5. 📢 [신규] 스캐너 결과 통계 분석 및 브리핑
    # ==========================================
    def analyze_scanner_results(self, total_count, survived_count, stats_text):
        """스캐너의 필터링 결과를 AI에게 던져주고 시장 진단 텍스트를 받아옵니다."""
        
        data_input = f"""
[오늘의 스캐너 필터링 통계]
- 총 스캔 대상: {total_count}개 종목
- 최종 생존(매수 감시 대상): {survived_count}개 종목
- 상세 탈락 사유:
{stats_text}
"""
        max_retries = len(self.model_list)
        
        for attempt in range(max_retries):
            try:
                # 💡 여기서는 JSON 강제 옵션(response_mime_type)을 쓰지 않습니다! (자연어 출력이므로)
                response = self.model.generate_content([MARKET_ANALYSIS_PROMPT, data_input])
                return response.text.strip()
                
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "quota" in error_msg:
                    self.current_idx = (self.current_idx + 1) % len(self.model_list)
                    self._set_current_model()
                    continue 
                else:
                    print(f"🚨 [AI 브리핑 에러] {e}")
                    return f"⚠️ AI 시장 진단 중 에러가 발생했습니다. (사유: {e})"
                    
        return "⚠️ 모든 AI 모델의 쿼타가 소진되어 시장 진단을 생성할 수 없습니다."