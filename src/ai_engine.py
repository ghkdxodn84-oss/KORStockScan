import json
import google.generativeai as genai

# ==========================================
# 1. 🎯 시스템 프롬프트 (스캘핑 전용)
# ==========================================
SCALPING_SYSTEM_PROMPT = """
너는 한국 주식시장의 초단타(스캘핑) 전문 AI 트레이더야. 
제공된 실시간 호가창 뎁스와 체결 흐름을 분석해서 1분 이내에 주가가 상승할지 판단해.

[판단 기준]
- BUY: 매도 호가창의 큰 물량(벽)을 강력한 매수 체결(BUY)로 돌파하기 시작할 때. (Score: 80~100)
- DROP: 매수 호가에만 물량이 많고(허매수), 실제 체결은 매도(SELL)가 압도적일 때. (Score: 0~40)
- WAIT: 수급이 모호하거나 거래량이 부족하여 방향성을 알 수 없을 때. (Score: 41~79)

분석 결과는 반드시 아래 JSON 형식으로만 출력하고 다른 설명은 절대 추가하지 마:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "결정에 대한 1줄 요약 분석"
}
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
            'gemini-2.5-flash',
            'gemini-3-flash-preview',        # 3.0 플래시
            'gemini-2.5-flash-lite',         # 2.5 라이트
            'gemini-3.1-flash-lite-preview',  # 3.1 라이트
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
    def _format_market_data(self, ws_data, recent_ticks):
        """키움 API의 딕셔너리 데이터를 AI가 읽을 수 있는 텍스트로 예쁘게 포장합니다."""
        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []})

        # 호가창 조립
        ask_str = "\n".join([f"매도 {5-i}호가: {a['price']}원 ({a['volume']}주)" for i, a in enumerate(orderbook['asks'])])
        bid_str = "\n".join([f"매수 {i+1}호가: {b['price']}원 ({b['volume']}주)" for i, b in enumerate(orderbook['bids'])])
        
        # 틱 흐름 조립 (최신순이 아래로 가도록 역순 배치)
        tick_str = "\n".join([f"[{t['time']}] {t['dir']} 체결: {t['price']}원 ({t['volume']}주)" for t in reversed(recent_ticks)])

        user_input = f"""
[현재 상태]
- 현재가: {curr_price}원
- 체결강도: {v_pw}%

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
    def analyze_target(self, target_name, ws_data, recent_ticks):
        formatted_data = self._format_market_data(ws_data, recent_ticks)
        
        # 💡 [핵심 2] 장전된 모델의 개수만큼 최대 재시도(Retry)를 허용합니다.
        max_retries = len(self.model_list)
        
        for attempt in range(max_retries):
            try:
                # 1. 현재 설정된 모델로 호출 시도
                response = self.model.generate_content([SCALPING_SYSTEM_PROMPT, formatted_data])
                cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
                
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