"""
[KORStockScan Final Ensemble Scanner (Batch Engine)]

이 모듈은 시스템의 최종 결정을 내리는 '장 마감(또는 장 전) 통합 스캐너' 및 '장중 지능형 재스캔' 엔진입니다.
시장 전체의 데이터를 분석하여 승률이 가장 높은 타겟을 찾아내고, 알림/감시 계층으로 데이터를 전달합니다.

💡 핵심 기능 명세 (Feature Spec):
1. run_integrated_scanner() - 장 마감/장전 배치 작업:
   - 코스피 시총/거래량 상위 150~200개 종목을 대상으로 AI 콰트로 앙상블(XGB/LGBM) 예측 수행.
   - 지수 상대강도(RS), 단기 정배열, 수급(스마트 머니) 필터를 거쳐 'MAIN', 'RUNNER' 추천 종목을 DB에 적재.
   - Gemini 및 OpenAI 등 LLM 합의체에 장전 브리핑 데이터(Context)를 제공.
2. run_intraday_scanner() - 장중 실시간 스캔:
   - 키움 API 실시간 주도주(급등주) 목록을 기반으로 가상 일봉을 생성하여 즉석 AI 판독 수행.
   - 포착 즉시 웹소켓 모듈에 감시(COMMAND_WS_REG)를 지시하여 실시간 체결을 준비.

💡 아키텍처 설계 사상 (Decoupling & Event-Driven):
- 이 파일은 오직 '계산(Compute)과 필터링(Filtering)'에만 집중합니다.
- 알림 전송: 텔레그램 서버와 직접 통신하지 않으며, 결과물은 EventBus를 통해 알림 계층으로 던집니다. (TELEGRAM_BROADCAST)
- AI 추론: 무거운 ML 예측 연산은 `ml_predictor.py` 모듈로 철저하게 위임(Delegate)하여 책임을 분리했습니다.
"""
import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 방어] 프로젝트 루트 경로를 sys.path에 동적으로 추가
# ==========================================
# 현재 파일(scanners) -> 부모(src) -> 부모(KORStockScan) 경로를 찾아냅니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import os
import json
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import FinanceDataReader as fdr

# 💡 Level 1 & 2 공통 모듈
from src.utils import kiwoom_utils
from src.utils.constants import TRADING_RULES, DATA_DIR, CONFIG_PATH, DEV_PATH
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.model.feature_engineer import calculate_all_features

# 💡 [교정] 커스텀 로거 적용
from src.utils.logger import log_error

# 💡 [수정] 순수 AI 추론 도구
import src.engine.ml_predictor as ml_predictor

# 💡 [신규] AI 합의체 (Gemini + OpenAI) 엔진 준비
from src.engine.ai_engine import GeminiSniperEngine
from src.engine.ai_engine_openai import GPTSniperEngine 

# 💡 [핵심 교정] 텔레그램 매니저를 초대해야 수신기가 EventBus에 정상 등록됩니다!
import src.notify.telegram_manager as telegram_manager

warnings.filterwarnings('ignore')

# --- [1. 성과 복기 엔진] ---
def get_performance_report(db: DBManager):
    """전일 추천 종목의 성과를 계산하여 반환합니다."""
    last_date = db.get_latest_history_date()
    if not last_date: return "📊 신규 가동을 시작합니다.\n"

    history = db.get_history_by_date(last_date)
    report_msg = f"📊 <b>[전일 성적표 ({last_date})]</b>\n"

    for r_type in ['MAIN', 'RUNNER']:
        subset = history[history['type'] == r_type]
        if subset.empty: continue

        profits = []
        for _, row in subset.iterrows():
            try:
                df = fdr.DataReader(row['code'], start=last_date)
                close_price = df.iloc[-1]['Close']
            except:
                db_last = db.get_stock_data(row['code'], limit=1)
                close_price = db_last.iloc[0]['Close'] if not db_last.empty else row['buy_price']

            p = (close_price / row['buy_price'] - 1) * 100
            profits.append(p)

        if profits:
            win_rate = (len([p for p in profits if p > 0]) / len(profits)) * 100
            avg_p = sum(profits) / len(profits)
            label = "✅ 강력추천" if r_type == 'MAIN' else "🥈 아차상"
            report_msg += f"{label}: 승률 {win_rate:.0f}% / 수익 {avg_p:+.2f}%\n"

    return report_msg + "-" * 20 + "\n"

# --- [2. 메인 스캐너 엔진 (장 마감(또는 장 전) 배치 작업)] ---
def run_integrated_scanner():
    print(f"=== KORStockScan v14 (Stacking Ensemble + Event-Driven) ===")
    
    db = DBManager()
    event_bus = EventBus() # 💡 이벤트 버스 장착!

    try:
        # ==========================================
        # 1. 💡 가벼워진 ml_predictor를 통해 모델 로드
        # ==========================================
        models = ml_predictor.load_models()
        if not models:
            print("❌ AI 모델 로드 실패로 스캐너를 종료합니다.")
            return

        kiwoom_token = None
        target_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else DEV_PATH
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                CONF = json.load(f)
            kiwoom_token = kiwoom_utils.get_kiwoom_token(CONF)
        except Exception as e:
            print(f"⚠️ 키움 토큰 발급 생략 (FDR 단독 모드): {e}")

        # ==========================================
        # 2. 지수 상대강도(RS)용 지수 데이터 확보 (FDR 우선 -> Kiwoom ka20006 우회)
        # ==========================================
        kospi_5d_return = 0
        try:
            print("📈 FDR을 통해 최신 KOSPI 지수 데이터를 가져오는 중...")
            kospi_df = fdr.DataReader('KS11', start=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'))
            if not kospi_df.empty and len(kospi_df) >= 5:
                kospi_5d_return = (kospi_df['Close'].iloc[-1] / kospi_df['Close'].iloc[-5]) - 1
            else:
                raise ValueError("FDR 데이터 부족")
        except Exception as e:
            if kiwoom_token:
                latest_prc, before_prc = kiwoom_utils.get_index_daily_ka20006(kiwoom_token, "001")
                if latest_prc and before_prc:
                    kospi_5d_return = (latest_prc / before_prc) - 1

        # ==========================================
        # 3. 기초 유동성 필터 (FDR -> DB Fallback)
        # ==========================================
        print("🔍 [1/4] 분석 대상 종목 리스트 구성 중...")
        target_list = []
        try:
            df_krx = fdr.StockListing('KOSPI')
            top_m = df_krx.sort_values(by='Marcap', ascending=False).head(TRADING_RULES.TOP_N_MARCAP)
            target_df = top_m.sort_values(by='Volume', ascending=False).head(TRADING_RULES.TOP_N_VOLUME)
            target_list = [{'Code': r['Code'], 'Name': r['Name']} for _, r in target_df.iterrows()]
        except Exception as e:
            query = """
                SELECT stock_code AS "Code", stock_name AS "Name" 
                FROM daily_stock_quotes 
                WHERE quote_date = (SELECT MAX(quote_date) FROM daily_stock_quotes) 
                ORDER BY marcap DESC 
                LIMIT 200
                """
            with db.get_session() as session:
                # 💡 ORM/Core 방식으로 변경 필요 시 추후 대응, 현재는 pandas 연동 유지
                db_targets = pd.read_sql(query, session.bind)
            target_list = db_targets.head(150).to_dict('records')

        # ==========================================
        # 4. AI 앙상블 스캐닝 루프 (💡 except 블록 밖으로 완벽 탈출!)
        # ==========================================
        print(f"🚀 [2/4] AI 콰트로 앙상블 분석 시작 ({len(target_list)} 종목)...")
        all_results = []
        drop_stats = {'short_data': 0, 'invalid_type': 0, 'low_price': 0, 'quality': 0, 'ai_prob': 0, 'trend': 0, 'supply': 0, 'error': 0}

        # 💡 [핵심] DB의 스네이크 케이스를 AI가 아는 기존 대문자 포맷으로 원상복구하는 사전
        REVERSE_MAPPING = {
            'quote_date': 'Date', 'stock_code': 'Code', 'stock_name': 'Name',
            'open_price': 'Open', 'high_price': 'High', 'low_price': 'Low', 'close_price': 'Close', 'volume': 'Volume',
            'ma5': 'MA5', 'ma20': 'MA20', 'ma60': 'MA60', 'ma120': 'MA120', 'rsi': 'RSI', 
            'macd': 'MACD', 'macd_sig': 'MACD_Sig', 'macd_hist': 'MACD_Hist',
            'bbl': 'BBL', 'bbm': 'BBM', 'bbu': 'BBU', 'bbb': 'BBB', 'bbp': 'BBP', 
            'vwap': 'VWAP', 'obv': 'OBV', 'atr': 'ATR', 'daily_return': 'Return',
            'marcap': 'Marcap', 'retail_net': 'Retail_Net', 'foreign_net': 'Foreign_Net', 'inst_net': 'Inst_Net', 'margin_rate': 'Margin_Rate'
        }

        for stock in target_list:
            code = str(stock['Code']).strip().zfill(6)
            name = stock['Name']
            
            df = db.get_stock_data(code, limit=60)
            if len(df) < 30: 
                drop_stats['short_data'] += 1
                continue

            # 💡 [핵심 로직] 꺼내온 즉시 컬럼명을 AI용으로 갈아입힙니다.
            df = df.rename(columns=REVERSE_MAPPING)

            df = df.sort_values('Date')
            current_price = df.iloc[-1]['Close']

            if not kiwoom_utils.is_valid_stock(code, name, current_price=current_price):
                if current_price < TRADING_RULES.MIN_PRICE: drop_stats['low_price'] += 1
                else: drop_stats['invalid_type'] += 1
                continue

            # =================================================================
            # 🛡️ 기초품질(Quality) 필터: 하락 추세 및 소외주 1차 컷오프
            # 아래 3가지 모멘텀 조건 중 **단 1개도 만족하지 못하는(sum < 1)** 종목은 폐기
            #   1) 상대강도: 최근 5일 수익률이 코스피 지수 5일 수익률보다 높을 것
            #   2) 단기추세: 현재가 > 5일선 > 20일선 (단기 완전 정배열)
            #   3) 가격방어: 최근 20일(약 1달) 최고점 대비 하락폭이 -10% 이내일 것
            # =================================================================
            stock_5d_return = (current_price / df.iloc[-5]['Close']) - 1
            ma5, ma20 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(20).mean().iloc[-1]
            high_20d = df['High'].tail(20).max()

            if sum([stock_5d_return > kospi_5d_return, (current_price > ma5 > ma20), current_price >= (high_20d * 0.90)]) < 1:
                drop_stats['quality'] += 1  
                continue

            try:
                # 추론을 ml_predictor에게 위임!
                p_final = ml_predictor.predict_prob_for_df(df, models)

                if p_final < getattr(TRADING_RULES, 'PROB_RUNNER_PICK', 0.70):
                    drop_stats['ai_prob'] += 1  
                    continue

                # AI를 통과한 녀석들만 수급 필터를 위해 피처 계산
                df_feat = calculate_all_features(df)
                latest_row = df_feat.iloc[[-1]]

                f_roll5 = latest_row['Foreign_Net_Roll5'].values[0]
                i_roll5 = latest_row['Inst_Net_Roll5'].values[0]
                f_accel = latest_row['Foreign_Net_Accel'].values[0]
                i_accel = latest_row['Inst_Net_Accel'].values[0]

                if not ((f_roll5 > 0 and f_accel > 0) or (i_roll5 > 0 and i_accel > 0)):
                    drop_stats['supply'] += 1
                    continue

                h60, l60 = df_feat['High'].tail(60).max(), df_feat['Low'].tail(60).min()
                pos_pct = (current_price - l60) / (h60 - l60 + 1e-9)
                pos_tag = 'BREAKOUT' if pos_pct >= 0.8 else ('BOTTOM' if pos_pct <= 0.3 else 'MIDDLE')

                all_results.append({'Name': name, 'Prob': p_final, 'Price': int(current_price), 'Code': code, 'Position': pos_tag})

            except Exception as e:
                drop_stats['error'] += 1  
                continue

        # ==========================================
        # 5. 결과 기록 및 텔레그램 전송 (Event-Driven)
        # ==========================================
        print("📊 [3/4] 리포트 생성 및 전송 중...")
        
        debug_msg = (
            f"🛑 *[장 마감 스캐너 필터링 결과]*\n"
            f"총 {len(target_list)}개 중 *{len(all_results)}개 생존*\n\n"
            f"📉 *탈락 사유 통계*\n"
            f" • 데이터 부족: {drop_stats['short_data']}개\n"
            f" • ETF/동전주: {drop_stats['invalid_type'] + drop_stats['low_price']}개\n"
            f" • 기초 품질 미달: {drop_stats['quality']}개\n"
            f" • AI 확신도 부족: {drop_stats['ai_prob']}개\n"
            f" • 수급 부재(이탈): {drop_stats['supply']}개\n"
        )

        # 📢 [입의 분리 1] 관리자 텔레그램 발송을 EventBus로 위임!
        event_bus.publish("TELEGRAM_ADMIN_NOTIFY", {"text": debug_msg})

        # --- 추천 종목 분류 및 DB 저장 ---
        today = datetime.now().strftime('%Y-%m-%d')
        main_picks = sorted([r for r in all_results if r['Prob'] >= TRADING_RULES.PROB_MAIN_PICK], key=lambda x: x['Prob'], reverse=True)[:3]
        runner_ups = sorted([r for r in all_results if TRADING_RULES.PROB_RUNNER_PICK <= r['Prob'] < TRADING_RULES.PROB_MAIN_PICK], key=lambda x: x['Prob'], reverse=True)[:50]

        for r in main_picks:
            db.save_recommendation(today, r['Code'], r['Name'], r['Price'], 'MAIN', r['Position'], prob=r['Prob'])
        for r in runner_ups:
            db.save_recommendation(today, r['Code'], r['Name'], r['Price'], 'RUNNER', r['Position'], prob=r['Prob'])

        # --- Gemini AI 수석 트레이더 장전 브리핑 ---
        ai_briefing = "⚠️ GEMINI_API_KEY 미설정"
        api_key = CONF.get('GEMINI_API_KEY')
        if api_key:
            try:
                ai_engine = GeminiSniperEngine(api_keys=api_key)
                ai_briefing = ai_engine.analyze_scanner_results(len(target_list), len(all_results), debug_msg)
            except Exception as e:
                ai_briefing = f"⚠️ AI 브리핑 생성 실패: {e}"

        perf_report = get_performance_report(db)

        # 📢 [입의 분리 2] 최종 리포트를 포장해서 텔레그램 매니저에게 Event로 던짐!
        payload = {
            "type": "START_OF_DAY_REPORT",
            "date": today,
            "performance_report": perf_report,
            "ai_briefing": ai_briefing,
            "main_picks": main_picks,
            "runner_ups": runner_ups
        }
        event_bus.publish("TELEGRAM_BROADCAST", payload)

    except Exception as e:
        print(f"❌ 시스템 에러 발생: {e}")
    finally:
        print("🏁 [4/4] 스캐닝 프로세스가 종료되었습니다.")

def run_intraday_scanner(token):
    """
    오늘 실시간 시세를 반영한 가상 일봉을 생성하여 AI 앙상블을 재구동하는 장중 스캐너
    """
    print("🔍 [장중 스캔] 실시간 급등주(주도주) 탐색을 시작합니다...")

    db = DBManager()
    event_bus = EventBus() # 💡 이벤트 버스 연동

    # ==========================================
    # 1. 실시간 주도주 목록 수집 (Kiwoom -> FDR 방어)
    # ==========================================
    # 💡 [교정 1] SniperRadar 통신 대신 kiwoom_utils의 정제된 함수 사용
    raw_hot_stocks = kiwoom_utils.get_realtime_hot_stocks_ka00198(token, as_dict=True)
    hot_stocks = []

    # [1차 시도] 키움 API 결과 정제 (불순물 제거 및 🚀 가격 컷오프)
    if raw_hot_stocks:
        print("📈 키움 API를 통해 실시간 주도주 데이터를 확보했습니다.")
        for s in raw_hot_stocks:
            if kiwoom_utils.is_valid_stock(s['code'], s['name'], current_price=s['price']):
                hot_stocks.append(s)

    # [2차 시도 - Fallback] 키움 API 3회 모두 실패 시 FDR 실시간 거래량 상위 활용
    if not hot_stocks:
        print("⚠️ 키움 API 급등주 포착 실패. FDR 실시간 거래량 상위 종목으로 우회합니다...")
        try:
            df_krx = fdr.StockListing('KOSPI')
            top_vol = df_krx.sort_values(by='Volume', ascending=False).head(100)

            for _, row in top_vol.iterrows():
                current_price = int(row['Close'])
                if kiwoom_utils.is_valid_stock(row['Code'], row['Name'], current_price=current_price):
                    hot_stocks.append({
                        'code': row['Code'],
                        'name': row['Name'],
                        'price': current_price,
                        'vol': int(row['Volume'])
                    })
            print(f"✅ FDR 우회 성공: {len(hot_stocks)}개 종목 확보")
        except Exception as e:
            log_error(f"🚨 FDR 우회 수집 실패: {e}")

    if not hot_stocks:
        print("⚠️ 조건에 맞는 실시간 급등주가 없어 스캔을 보류합니다.")
        return []

    print(f"✅ 최종 포착된 핫-종목 {len(hot_stocks)}개에 대한 AI 판독을 시작합니다.")

    # ==========================================
    # 2. AI 앙상블 모델 로드 (순수 도구 사용)
    # ==========================================
    # 💡 [교정 2] 무거운 joblib 대신 가벼워진 ml_predictor 사용
    models = ml_predictor.load_models()
    if not models:
        log_error("❌ AI 모델 로드 실패. 장중 스캔을 취소합니다.")
        return []

    # ==========================================
    # 3. 실시간 가상 일봉 생성 및 AI 판독 루프
    # ==========================================
    new_targets = []
    new_codes_found = []
    today_str: str = datetime.now().strftime('%Y-%m-%d')
    drop_stats = {'ai_prob': 0, 'trend': 0, 'supply': 0, 'error': 0}

    for stock in hot_stocks:
        code, name, curr_price, curr_vol = stock['code'], stock['name'], stock['price'], stock['vol']

        df = db.get_stock_data(code, limit=60)
        if len(df) < 30: continue

        df = df.sort_values('Date').reset_index(drop=True)

        # 가상 일봉(오늘) 추가 또는 덮어쓰기
        if df.iloc[-1]['Date'] != today_str:
            new_row = df.iloc[-1].copy()
            new_row['Date'] = today_str
            new_row['Close'] = curr_price
            if curr_vol > 0: new_row['Volume'] = curr_vol
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df.at[df.index[-1], 'Close'] = curr_price
            if curr_vol > 0: df.at[df.index[-1], 'Volume'] = curr_vol

        try:
            # 💡 [교정 3] ml_predictor에게 순수 예측 요청
            p_final = ml_predictor.predict_prob_for_df(df, models)

            # ==========================================
            # 💡 황금 임계값 및 스마트 머니 필터 장착
            # ==========================================
            # 1. 확신도 필터 (constants.py 동기화)
            if p_final < TRADING_RULES.PROB_INTRADAY_PICK:
                drop_stats['ai_prob'] += 1
                continue

            # 수급 필터 검증을 위해 피처 별도 계산
            df_feat = calculate_all_features(df)
            latest_row = df_feat.iloc[[-1]]

            # ==========================================
            # 💡 2. [복구됨] 20일 이동평균선(MA20) 역배열 필터
            # 추세 추종 시: 주석 해제 (활성화)
            # 낙폭 과대(바닥 잡기) 시: 주석 처리 (비활성화)
            # ==========================================
            # latest_close = latest_row['Close'].values[0]
            # latest_ma20 = latest_row['MA20'].values[0]
            # if latest_close < latest_ma20:
            #     drop_stats['trend'] += 1
            #     continue

            # 3. [V3.1] 외국인/기관 매집 '가속도' 필터
            f_roll5 = latest_row['Foreign_Net_Roll5'].values[0]
            i_roll5 = latest_row['Inst_Net_Roll5'].values[0]
            f_accel = latest_row.get('Foreign_Net_Accel', pd.Series([0])).values[0]
            i_accel = latest_row.get('Inst_Net_Accel', pd.Series([0])).values[0]

            # 조건: 5일 누적이 양수이면서, 가속도(Accel)까지 플러스(+)로 전환된 곳이 한 곳이라도 있어야 통과!
            is_foreign_buying = (f_roll5 > 0 and f_accel > 0)
            is_inst_buying = (i_roll5 > 0 and i_accel > 0)

            if not (is_foreign_buying or is_inst_buying):
                drop_stats['supply'] += 1
                continue

            h60, l60 = df_feat['High'].tail(60).max(), df_feat['Low'].tail(60).min()
            pos_pct = (curr_price - l60) / (h60 - l60 + 1e-9)
            pos_tag = 'BREAKOUT' if pos_pct >= 0.8 else ('BOTTOM' if pos_pct <= 0.3 else 'MIDDLE')

            # 모든 필터를 뚫은 종목만 추가
            new_targets.append({
                'Name': name, 'Prob': p_final, 'Price': int(curr_price), 
                'Code': code, 'Position': pos_tag
            })
            new_codes_found.append(code)

        except Exception as e:
            drop_stats['error'] += 1
            log_error(f"⚠️ [{name}] 장중 스캔 연산 에러: {e}")
            continue

    # ==========================================
    # 4. 분석 결과 DB 기록 및 Event 브로드캐스트
    # ==========================================
    debug_msg = (
        f"🛑 *[장중 스캐너 필터링 결과]*\n"
        f"총 {len(hot_stocks)}개 중 *{len(new_targets)}개 생존*\n\n"
        f"📉 *탈락 사유 통계*\n"
        f" • AI 확신도 부족(<{int(getattr(TRADING_RULES, 'PROB_INTRADAY_PICK', 0.8)*100)}%): {drop_stats['ai_prob']}개\n"
        f" • 역배열(제외): {drop_stats['trend']}개\n"
        f" • 수급 부재(미달): {drop_stats['supply']}개\n"
        f" • 데이터 에러: {drop_stats['error']}개"
    )
    
    # 📢 [교정 4] 터미널 출력 대신 텔레그램 관리자에게 EventBus로 발송 지시
    event_bus.publish("TELEGRAM_ADMIN_NOTIFY", {"text": debug_msg})

    if new_targets:
        print(f"🎯 장중 AI 재스캔 완료! {len(new_targets)}개의 주도주 포착.")
        try:
            # 💡 ORM 기반 안전한 DB 저장
            with db.get_session() as session:
                for t in new_targets:
                    db.save_recommendation(today_str, t['Code'], t['Name'], t['Price'], 'MAIN', t['Position'], prob=t['Prob'])
        except Exception as e:
            log_error(f"장중 스캐너 DB 저장 에러: {e}")

        # 📢 [핵심] 스캐너가 직접 웹소켓에 실시간 감시 등록 요청!
        event_bus.publish("COMMAND_WS_REG", {"codes": new_codes_found})

        # 📢 텔레그램 매니저에게 장중 픽 전송 요청!
        event_bus.publish("TELEGRAM_BROADCAST", {
            "type": "INTRADAY_REPORT",
            "picks": new_targets
        })

    return new_targets

if __name__ == "__main__":
    run_integrated_scanner()