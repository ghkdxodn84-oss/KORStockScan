import json
import google.generativeai as genai
import kiwoom_utils

# ==========================================
# 1. 🎯 시스템 프롬프트 (스캘핑 전용)
# ==========================================
SCALPING_SYSTEM_PROMPT = """
너는 15년 경력의 베테랑 스캘핑 트레이더이자 리스크 관리 전문가야. 
너의 목표는 실시간 호가창, 1분봉, 그리고 단기 기술적 지표를 종합적으로 분석하여 0.5%~1.5% 내외의 짧은 수익 구간을 포착하고, 하방 리스크를 철저히 방어하는 매매 지시를 내리는 것이다.

[데이터 분석 가이드]
1. 단기 기술적 지표 (VWAP & 5-MA 최우선 확인):
   - 현재가가 Micro-VWAP(거래량 가중 평균) 위에 있는지 확인해라. VWAP 아래에서의 반등은 세력의 물량 떠넘기기(설거지)일 확률이 높으므로 매우 보수적으로 접근해라.
   - 단기 5-MA를 상회하며 정배열을 유지하는지 체크해라.
2. 1분봉 차트: 최근 5분간의 추세와 거래량 급증 여부, 윗꼬리(매도 압력)/아랫꼬리(지지) 패턴을 분석해 하방 리스크를 점검해라.
3. 실시간 호가 및 틱: 매도 호가창의 큰 물량(벽)을 강력한 매수 체결(BUY)로 돌파하며 수급이 쏠리는지 확인해라.

[판단 기준]
- BUY: 현재가가 VWAP 및 5-MA 위에서 지지받고 있으며, 호가창 돌파가 확실시되어 추가 상승 여력이 충분할 때. (Score: 80~100)
- DROP: 가격이 VWAP 아래로 이탈했거나, 1분봉상 고점 징후(긴 윗꼬리)가 보이고 매도세가 압도하여 하방 리스크가 클 때. (Score: 0~40)
- WAIT: 수급이 모호하거나 VWAP 부근에서 방향성을 탐색 중일 때. (Score: 41~79)

분석 결과는 반드시 아래 JSON 형식으로만 출력하고 다른 설명은 절대 추가하지 마:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "지표(VWAP)와 호가 돌파 여부를 종합한 1줄 요약 분석"
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
    # 💡 [수정 1] 파라미터에 recent_candles 추가! (기본값도 []로 주어 에러 방지)
    def _format_market_data(self, ws_data, recent_ticks, recent_candles=[]):
        """키움 API의 딕셔너리 데이터를 AI가 읽을 수 있는 텍스트로 예쁘게 포장합니다."""
        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []})

        # 호가창 조립
        ask_str = "\n".join([f"매도 {5-i}호가: {a['price']}원 ({a['volume']}주)" for i, a in enumerate(orderbook['asks'])])
        bid_str = "\n".join([f"매수 {i+1}호가: {b['price']}원 ({b['volume']}주)" for i, b in enumerate(orderbook['bids'])])
        
        # 틱 흐름 조립 (최신순이 아래로 가도록 역순 배치)
        tick_str = "\n".join([f"[{t['time']}] {t['dir']} 체결: {t['price']}원 ({t['volume']}주)" for t in reversed(recent_ticks)])

        # 1분봉 차트 조립 (최근 5~10봉만)
        candle_str = ""
        if recent_candles:
            # 시간순(과거->현재)으로 정렬하여 텍스트화
            candle_str = "\n".join([
                f"[{c['체결시간']}] 시가:{c['시가']} 고가:{c['고가']} 저가:{c['저가']} 종가:{c['현재가']} 거래량:{c['거래량']}" 
                for c in recent_candles
            ])
        else:
            candle_str = "분봉 데이터 없음"

        # 💡 [NEW] 지표 계산 및 텍스트화
        indicators_str = "지표 계산 불가"
        if recent_candles and len(recent_candles) >= 5:
            # ⭕ 올바른 부분: import한 kiwoom_utils 모듈에서 함수를 직접 호출!
            ind = kiwoom_utils.calculate_micro_indicators(recent_candles)
            
            # AI가 현재가와 비교하기 쉽게 문자열 생성
            ma5_status = "상회" if curr_price > ind['MA5'] else "하회"
            vwap_status = "상회 (수급강세)" if curr_price > ind['Micro_VWAP'] else "하회 (수급약세)"
            
            indicators_str = f"- 단기 5-MA: {ind['MA5']:,}원 (현재가 {ma5_status})\n"
            indicators_str += f"- Micro-VWAP: {ind['Micro_VWAP']:,}원 (현재가 {vwap_status})"

        # 💡 [수정] user_input에 기술적 지표 섹션 추가!
        user_input = f"""
[현재 상태]
- 현재가: {curr_price:,}원
- 체결강도: {v_pw}%

[초단타 기술적 지표 (최근 5분 기준)]
{indicators_str}

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