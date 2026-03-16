import requests
import pandas as pd
import FinanceDataReader as fdr

# 기존 유틸리티에서 로깅 등 순수 도구만 빌려옵니다.
from src.utils import kiwoom_utils
from src.utils.logger import log_error
from src.core.event_bus import EventBus
from src.utils.constants import TRADING_RULES  # 필요에 따라 상수를 추가/수정해서 사용

class SniperRadar:
    """
    KORStockScan 통합 레이더 (정보국)
    """
    def __init__(self, token):
        self.access_token = token
        
        # 💡 [핵심] EventBus 인스턴스 획득 및 실시간 데이터 구독
        self.event_bus = EventBus()
        self.event_bus.subscribe("REALTIME_TICK_ARRIVED", self._on_realtime_tick)
    
    # ==========================================
    # ⚡ [핵심] 실시간 이벤트 처리기 (Event Handler)
    # ==========================================
    def _on_realtime_tick(self, payload):
        """웹소켓에서 'REALTIME_TICK_ARRIVED' 이벤트가 올 때마다 자동 실행됩니다."""
        code = payload.get('code')
        ws_data = payload.get('data')

        if not ws_data or ws_data.get('curr', 0) == 0:
            return

        # 1. 수급 점수 계산
        market_leader_score = self.calculate_market_leader_score(ws_data)

        # 2. 임시 AI 확신도 (나중에 Gemini/OpenAI 모듈 응답으로 교체될 부분)
        dummy_ai_prob = 0.85 

        # 3. 통합 신호 분석 (순수 데이터만 반환받음)
        score, prices, conclusion, checklist, metrics = SniperRadar.analyze_signal_integrated(ws_data, dummy_ai_prob)

        # 4. 🚀 [조건 충족 시 타점 계산 및 이벤트 발행]
        if score >= 70:  # 매수 기준 통과
            market_trend = self.get_market_regime(self.access_token)
            
            target_price, drop_pct = self.get_smart_target_price(
                curr_price=prices['curr'],
                v_pw=metrics['v_pw'],
                ai_score=dummy_ai_prob,
                market_trend=market_trend,
                ask_tot=metrics['ask_tot'],
                bid_tot=metrics['bid_tot']
            )

            # 💡 매매 엔진과 텔레그램이 받아볼 수 있도록 새로운 이벤트를 허공에 쏩니다!
            self.event_bus.publish("TRADE_SIGNAL_DETECTED", {
                "code": code,
                "target_price": target_price,
                "score": score,
                "conclusion": conclusion,
                "metrics": metrics,       # 텔레그램이 받아서 게이지바를 그릴 순수 데이터
                "checklist": checklist
            })
        
    # ==========================================
    # 🎯 [최종: 융합 및 지시] 메인 스캐너로 넘길 타겟 추출
    # ==========================================
    def find_supernova_targets(self, mrkt_tp="101"):
        """초신성 수급 폭발 타겟 추출 (현재가 포함 반환)"""
        final_targets = []
        
        # 💡 [핵심 수정 1] self.를 제거하고, kiwoom_utils의 함수를 호출하며 self.access_token을 넘깁니다.
        vol_spikes = kiwoom_utils.scan_volume_spike_ka10023(self.access_token, mrkt_tp=mrkt_tp)
        
        for stock in vol_spikes:
            # 💡 [핵심 수정 2] 각 검증 함수들에도 첫 번째 인자로 self.access_token을 정확히 주입합니다.
            is_program_buying = kiwoom_utils.check_program_buying_ka90008(self.access_token, stock['code'])
            is_strong_execution = kiwoom_utils.check_execution_strength_ka10046(self.access_token, stock['code'])
            
            if is_program_buying and is_strong_execution:
                # 🚀 'cur_prc'와 'Price'가 담긴 stock 객체 그대로 전달
                final_targets.append(stock)
                log_error(f"🚨 [Radar] 완벽한 수급 조짐 포착: {stock['name']} ({stock['code']})")
                
        return final_targets
    
    # ==========================================
    # 🧠 엔진 코어 (UI 로직 제거 및 순수 데이터 반환)
    # ==========================================
    @staticmethod
    def analyze_signal_integrated(ws_data, ai_prob, threshold=70):
        """[v13 정밀 진단] 문자열 UI 생성 로직을 걷어내고 순수 분석 지표 딕셔너리를 반환합니다."""
        score = ai_prob * 50
        prices = {}
        metrics = {} # 텔레그램 매니저에게 전달할 원시 데이터

        checklist = {
            "AI 확신도 (75%↑)": {"val": f"{ai_prob:.1%}", "pass": ai_prob >= 0.75},
            "유동성 (3억↑)": {"val": "대기", "pass": False},
            "체결강도 (100%↑)": {"val": "대기", "pass": False},
            "호가잔량비 (1.5~5배)": {"val": "대기", "pass": False}
        }

        try:
            curr_price = ws_data['curr']
            prices = {'curr': curr_price, 'buy': curr_price, 'sell': int(curr_price * 1.03), 'stop': int(curr_price * 0.97)}

            ask_tot = ws_data.get('ask_tot', 1)
            bid_tot = ws_data.get('bid_tot', 1)
            total = ask_tot + bid_tot

            # 유동성 검사
            liquidity_value = total * curr_price
            checklist["유동성 (3억↑)"] = {"val": f"{liquidity_value / 1e8:.1f}억", "pass": liquidity_value >= TRADING_RULES['MIN_LIQUIDITY']}

            # 호가잔량 검사
            imb_ratio = ask_tot / (bid_tot + 1e-9)
            pass_imb = 1.5 <= imb_ratio <= 5.0
            checklist["호가잔량비 (1.5~5배)"] = {"val": f"{imb_ratio:.2f}배", "pass": pass_imb}
            
            if pass_imb: score += 25

            # 체결강도 검사
            v_pw = ws_data.get('v_pw', 0.0)
            pass_v_pw = v_pw >= 100
            checklist["체결강도 (100%↑)"] = {"val": f"{v_pw:.1f}%", "pass": pass_v_pw}

            if v_pw >= 110: score += 25
            elif v_pw >= 100: score += 15

            # UI 문자열 대신 UI를 그릴 수 있는 뼈대 데이터 반환
            ratio_val = (ask_tot / total) * 100 if total > 0 else 0
            metrics = {
                "ratio_val": ratio_val,
                "ask_tot": ask_tot,
                "bid_tot": bid_tot,
                "v_pw": v_pw
            }

            if (v_pw < 100 and score < threshold) or (liquidity_value < TRADING_RULES['MIN_LIQUIDITY']):
                conclusion = "🚫 매수타이밍이 아닙니다"
            else:
                conclusion = "✅ 매수를 검토해보십시오"

        except Exception as e:
            conclusion = "결론: 분석 오류"

        return score, prices, conclusion, checklist, metrics

    def get_smart_target_price(self, curr_price, v_pw=100, ai_score=50, market_trend='NORMAL', ask_tot=0, bid_tot=0):
        """
        [스캘핑 4.0] 수급강도 + AI 확신도 + 호가잔량비율 + 라운드피겨 회피가 모두 적용된 궁극의 타점 계산기
        """
        if curr_price <= 0: return 0, 0.0
        
        final_ai_score = ai_score * 100 if ai_score <= 1.0 else ai_score
        
        # ==========================================
        # 💡 [아이디어 1] AI 초강세(90점 이상) -> 돌파 추격매수
        # ==========================================
        if final_ai_score >= 90:
            # 눌림목을 기다리지 않고 현재가(또는 바로 위 호가)로 직진하여 즉시 체결시킵니다.
            return curr_price, 0.0 
            
        # 1. 기본 설정 (수급강도 기준)
        if v_pw >= 200:
            drop_percent, tick_count = 0.2, 3
        elif v_pw >= 150:
            drop_percent, tick_count = 0.35, 4
        else:
            drop_percent, tick_count = 0.5, 5
            
        # 2. 🚀 가속 페달: AI 확신도 반영 (75~89점 구간)
        if final_ai_score >= 85:
            drop_percent = max(0.1, drop_percent - 0.15) 
            tick_count = max(1, tick_count - 1)
        elif final_ai_score <= 50: 
            drop_percent += 0.5   
            tick_count += 3

        # ==========================================
        # 💡 [아이디어 2] 호가창 잔량 비율(Orderbook Imbalance) 필터링
        # ==========================================
        if ask_tot > 0 and bid_tot > 0:
            if ask_tot >= bid_tot * 1.5:
                # 매도벽이 두터움 = 세력이 뚫고 올라갈 진짜 상승 신호
                # 너무 아래에 깔면 안 사지므로 타점을 위로 살짝 올림
                drop_percent = max(0.1, drop_percent - 0.2)
                tick_count = max(1, tick_count - 2)
            elif bid_tot >= ask_tot * 1.5:
                # 매수벽이 두터움 = 개미 꼬시기용 가짜 지지선일 확률 높음
                # 훅 빠질 수 있으므로 타점을 더 깊게(안전하게) 내림
                drop_percent += 0.4
                tick_count += 4

        # 3. 🛑 브레이크: 시장 지수 반영
        if market_trend == 'BAD':
            drop_percent += 0.5
            tick_count += 3

        # 4. 가격 계산 (퍼센트 방식 vs 틱 방식 중 더 안전한/낮은 가격)
        pct_price = kiwoom_utils.get_target_price_by_percent(curr_price, drop_percent)
        
        tick_price = curr_price
        for _ in range(int(tick_count)):
            tick = kiwoom_utils.get_tick_size(tick_price - 1) # 현재가보다 낮은 가격에서 시작하여 하나씩 호가 단위 내리기
            tick_price -= tick
            
        final_target = min(pct_price, tick_price)
        
        # ==========================================
        # 💡 [아이디어 3] 라운드 피겨(Round Figure) 회피 로직
        # ==========================================
        # 1만, 5만, 10만원 등 심리적 저항선 '바로 아래'는 악성 매물대이므로 피합니다.
        if 9800 <= final_target <= 9990:
            final_target = 9750   # 1만원 저항 회피 -> 아예 깊게 대기
        elif 49000 <= final_target <= 49950:
            final_target = 48800  # 5만원 저항 회피
        elif 98000 <= final_target <= 99900:
            final_target = 97500  # 10만원 저항 회피
            
        return int(final_target), round(drop_percent, 2)

    def calculate_micro_indicators(self, candles):
        """
        최근 1분봉 데이터를 바탕으로 스캘핑용 단기 지표를 계산합니다.
        
        # 📝 TODO [V14.0 업데이트 예정사항]
        # 향후 RSI(14) 및 MACD 지표를 추가하려면 아래 작업이 선행되어야 함:
        # 1. signal_radar.py의 get_minute_candles_ka10080 함수에서 limit=5 를 limit=30 이상으로 수정
        # 2. pandas-ta 또는 ta 라이브러리를 활용하여 EMA 기반 지표 계산 로직 추가
        """
        if not candles or len(candles) < 5:
            return {"MA5": 0, "Micro_VWAP": 0}

        # 1. 5분 이동평균선 (5-MA)
        # 캔들은 최신순(앞)부터 정렬되어 있다고 가정합니다.
        closes = [c['현재가'] for c in candles[:5]]
        ma5 = sum(closes) / 5

        # 2. Micro-VWAP (최근 5분간의 거래량 가중 평균 주가)
        # 공식: Sum(전형적 주가 * 거래량) / Sum(거래량)
        # *전형적 주가(Typical Price) = (고가 + 저가 + 종가) / 3
        total_vol = 0
        total_price_vol = 0
        
        for c in candles[:5]:
            typical_price = (c['고가'] + c['저가'] + c['현재가']) / 3
            total_price_vol += typical_price * c['거래량']
            total_vol += c['거래량']

        micro_vwap = total_price_vol / total_vol if total_vol > 0 else closes[0]

        return {
            "MA5": int(ma5), 
            "Micro_VWAP": int(micro_vwap)
        }

    def calculate_market_leader_score(self, ws_data):
        """
        [v12.4] 주도주 판별을 위한 수급 점수 계산기
        """
        if not ws_data:
            return 0
        
        # 1. 전일 대비 등락률 (변동성)
        fluctuation = float(ws_data.get('fluctuation', 0))
        
        # 2. 체결강도 (수급의 질)
        volume_power = float(ws_data.get('v_pw', 0))
        
        # 3. 호가 잔량 대금 (유동성 규모)
        # (매도잔량 + 매수잔량) * 현재가
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        curr_p = ws_data.get('curr', 0)
        liquidity = (ask_tot + bid_tot) * curr_p / 100_000_000 # 억 단위
        
        # 스캘핑용 가중치 공식: 
        # (등락률 * 10) + (체결강도 * 0.5) + (유동성 * 1.2)
        score = (fluctuation * 10) + (volume_power * 0.5) + (liquidity * 1.2)
        
        return round(score, 2)
    
    def get_market_regime(self, token=None):
        """
        코스피 지수를 분석하여 현재 시장 상태(BULL/BEAR)를 판별합니다.
        (1차: FinanceDataReader, 2차: 키움 ka20006 API 우회)
        기준: 코스피 현재가가 20일 이동평균선 위에 있으면 BULL, 아래면 BEAR
        """
        # 1차: FDR 사용 (코스피 지수 KS11)
        try:
            df = fdr.DataReader('KS11')
            if not df.empty and len(df) >= 20:
                current_close = float(df['Close'].iloc[-1])
                ma20 = float(df['Close'].tail(20).mean())
                return 'BULL' if current_close >= ma20 else 'BEAR'
        except Exception as e:
            print(f"⚠️ FDR 코스피 조회 실패. 키움 ka20006 API로 우회합니다: {e}")

        # 2차: 키움 ka20006 (업종일봉조회요청) 사용
        if token:
            try:
                url = kiwoom_utils.get_api_url("/api/dostk/mrkcond")
                headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'authorization': f'Bearer {token}',
                    'cont-yn': 'N',
                    'api-id': 'ka20006'
                }
                payload = {"upjong_cd": "001"} # 001: 코스피
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    res_json = res.json()
                    for key, val in res_json.items():
                        if isinstance(val, list) and len(val) >= 20 and 'cur_prc' in val[0]:
                            df_k = pd.DataFrame(val)
                            df_k['cur_prc'] = pd.to_numeric(df_k['cur_prc'].astype(str).str.replace(',', '', regex=False).str.replace('+', '', regex=False).str.replace('-', '', regex=False), errors='coerce')
                            current_close = df_k['cur_prc'].iloc[0]
                            ma20 = df_k['cur_prc'].head(20).mean()
                            return 'BULL' if current_close >= ma20 else 'BEAR'
            except Exception as e2:
                log_error(f"ka20006 처리 중 예외 발생: {e2}")
                print(f"🚨 키움 ka20006 우회 조회 실패: {e2}")
        # 둘 다 실패하면 보수적으로 BEAR(하락장) 모드 전환하여 리스크 관리
        return 'BEAR'