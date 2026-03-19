import requests
import json
import re

# 💡 Level 1 & 2 공통 모듈
from src.utils.logger import log_error
from src.core.event_bus import EventBus
from src.utils import kiwoom_utils

# ==========================================
# 1. 계좌 및 자산 조회 API
# ==========================================
def calc_buy_qty(current_price, total_deposit, ratio=0.1):
    """
    [v12.1] 예수금 대비 비중을 계산하여 정수 수량 산출
    """
    if current_price <= 0 or total_deposit <= 0:
        return 0

    target_budget = total_deposit * ratio
    safe_budget = target_budget * 0.95  # 슬리피지 대비 95% 사용

    qty = int(safe_budget // current_price)
    return qty

def get_deposit(token):
    """
    [kt00001] 예수금 조회 - return_code 대응 수정
    """
    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00001'
    }
    payload = {"qry_tp": "3"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()
        is_success = data.get('rt_cd') == '0' or data.get('return_code') == 0
        if res.status_code == 200 and is_success:
            return int(data.get('ord_alow_amt', 0))
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            log_error(f"❌ [예수금조회 실패] 사유: {err_msg}")
            return 0
    except:
        return 0

def get_my_inventory(token):
    """
    [kt00018] 계좌평가잔고내역을 조회합니다.
    SOR 주문을 고려하여 KRX(한국거래소)와 NXT(넥스트트레이드)의 잔고를 모두 합산합니다.
    """
    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00018',
    }

    # 💡 [핵심] 종목 코드를 키(Key)로 사용하여 양쪽 거래소의 수량을 합산할 딕셔너리
    aggregated_inventory = {}
    exchanges = ['KRX', 'NXT']
    
    for exchange in exchanges:
        params = {'qry_tp': '1', 'dmst_stex_tp': exchange}
        try:
            response = requests.post(url, headers=headers, json=params, timeout=5)
            data = response.json()
            
            if str(data.get('return_code', data.get('rt_cd', ''))) == '0':
                stock_list = data.get('acnt_evlt_remn_indv_tot', [])
                
                for item in stock_list:
                    raw_code = item.get('stk_cd', '')
                    code = raw_code[1:] if raw_code.startswith('A') else raw_code
                    qty = int(item.get('rmnd_qty', 0))
                    name = item.get('stk_nm', '')
                    
                    if qty > 0:
                        if code in aggregated_inventory:
                            aggregated_inventory[code]['qty'] += qty
                        else:
                            aggregated_inventory[code] = {'code': code, 'name': name, 'qty': qty}
            else:
                err_msg = data.get('return_msg', '알 수 없는 오류')
                log_error(f"⚠️ [API 경고] {exchange} 잔고 조회 실패: {err_msg}")

        except Exception as e:
            log_error(f"❌ [API 에러] {exchange} 잔고 통신 실패: {e}")

    return list(aggregated_inventory.values())

# ==========================================
# 2. 주문 실행 API
# ==========================================
def send_buy_order_market(code, qty, token, order_type="6", price=0):
    """
    [kt10000] 매수 주문 - return_code 대응 수정 및 지정가(00) 기능 추가
    - order_type: "00" (지정가 - 스캘핑 눌림목 그물망용)
                  "6"  (최유리지정가 - 기본값, 우량주 스윙용)
                  "3"  (시장가 - 강력한 추격 매수용)
    - price: 지정가 주문 시 입력할 1주당 단가 (시장가/최유리 지정가일 경우 0 또는 생략)
    """
    if qty <= 0: return None

    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10000'
    }

    # 💡 [핵심 개조] 지정가("00")일 때는 전달받은 price를 넣고, 아닐 때는 빈칸("")으로 둡니다.
    ord_price_str = str(int(price)) if str(order_type) == "00" and price > 0 else ""

    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": clean_code,
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,
        "trde_tp": str(order_type),
        "cond_uv": ""
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        is_success = str(data.get('rt_cd', '')) == '0' or str(data.get('return_code', '')) == '0'

        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code', data.get('rt_cd', ''))
            
            # 💡 [핵심] 에러 로깅 후 EventBus로 텔레그램 발송 (Decoupling)
            msg = f"❌ [매수거절] 종목:{clean_code}, 사유:{err_msg} (코드:{err_code})"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return data # 에러 데이터를 그대로 반환하여 상위에서 처리하게 함
            
    except Exception as e:
        msg = f"🔥 [매수주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None

def send_sell_order_market(code, qty, token, order_type="3", price=0):
    """
    [kt10001] 주식 매도 주문 (시장가/지정가/최유리지정가 통합 지원)
    """
    if qty <= 0: return None

    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10001'
    }

    # 💡 [핵심] 지정가("00") 매도일 경우에만 단가(price)를 세팅합니다.
    ord_price_str = str(int(price)) if str(order_type) == "00" and price > 0 else ""

    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": clean_code,
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,
        "trde_tp": str(order_type),
        "cond_uv": ""
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        is_success = str(data.get('rt_cd', '')) == '0' or str(data.get('return_code', '')) == '0'

        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code', data.get('rt_cd', ''))
            
            # 📢 EventBus를 통한 에러 브로드캐스트
            msg = f"❌ [매도거절] 종목:{clean_code}, 사유:{err_msg} (코드:{err_code})"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return data
            
    except Exception as e:
        msg = f"🔥 [매도주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None

def send_cancel_order(code, orig_ord_no, token, qty=0):
    """
    [kt10003] 주식 취소 주문 - 미체결 물량 취소
    :param qty: 취소 수량. 기본값 0 (0 입력 시 미체결 잔량 전부 취소)
    """
    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10003'  # 🚀 취소 전용 TR 명시
    }

    payload = {
        "dmst_stex_tp": "SOR",  # 국내거래소구분
        "orig_ord_no": str(orig_ord_no),  # 원주문번호
        "stk_cd": clean_code,  # 종목코드
        "cncl_qty": str(qty)  # 🚀 '0'이면 남은 물량 싹 다 취소!
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        if res.status_code == 200 and str(data.get('return_code', '')) == '0':
            cncl_qty_result = data.get('cncl_qty', '전량')
            new_ord_no = data.get('ord_no', '')
            print(f"✅ [취소접수] {clean_code} {cncl_qty_result}주 취소 성공 (새주문번호:{new_ord_no})")
            return data
        else:
            err_msg = data.get('return_msg', '상세 사유 없음')
            msg = f"❌ [취소거절] {clean_code}: {err_msg}"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return data

    except Exception as e:
        msg = f"🔥 [취소주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None

# ==========================================
# 3. 🚀 스마트 하이브리드 주문 (Sniper 엔진에서 호출)
# ==========================================
def send_smart_sell_order(code, qty, token, ws_data, reason_type):
    """
    [v13.1] 슬리피지 방어를 위한 스마트 매도 로직 (오리지널 정밀 로직 복원)
    """
    if qty <= 0: return None

    # 1. 매수 1호가 데이터 추출 (kiwoom_websocket '0D' 구조 반영)
    try:
        orderbook = ws_data.get('orderbook', {})
        bids = orderbook.get('bids', [])
        
        if not bids:
            print(f"⚠️ [{code}] 호가 데이터가 없어 시장가(3)로 전환합니다.")
            return send_sell_order_market(code, qty, token, order_type="3")

        # 매수 1호가 정보 (bids[0] 이 가장 높은 매수 호가)
        bid_1_p = bids[0].get('price', 0)
        bid_1_q = bids[0].get('volume', 0)
        
    except (IndexError, KeyError, TypeError) as e:
        log_error(f"❌ [{code}] 호가 데이터 파싱 실패: {e}")
        return send_sell_order_market(code, qty, token, order_type="3")

    # 2. 매매 성격에 따른 주문 분기
    # 🚨 손절(LOSS): 가격 불문, 시장가(3) 즉시 체결 (긴급 탈출)
    if reason_type == 'LOSS':
        print(f"🚨 [긴급손절] {code}: 시장가(3) 매도 (수량: {qty})")
        return send_sell_order_market(code, qty, token, order_type="3")

    # 💰 익절(PROFIT): 슬리피지 방어 가동
    else:
        # 매수 1호가 잔량이 내 물량보다 넉넉한지 확인 (2배 여유)
        if bid_1_p > 0 and bid_1_q >= qty * 2.0:
            print(f"💰 [스마트익절] {code}: 1호가({bid_1_p:,}원) 지정가 매도 (호가잔량: {bid_1_q}주)")
            return send_sell_order_market(code, qty, token, order_type="00", price=bid_1_p)
        
        else:
            # 1호가 잔량이 부족하면 '최유리지정가(6)'로 던져서 슬리피지 최소화
            print(f"⚠️ [슬리피지방어] {code}: 1호가 잔량 부족. 최유리지정가(6) 매도")
            return send_sell_order_market(code, qty, token, order_type="6")

def reserve_buy_order_ai(code, ai_target_price, deposit, token, ratio=0.05):
    """
    [v12.9] AI 권장 타점을 바탕으로 지정가 매수 예약 주문을 전송합니다.
    """
    try:
        # 💡 [보완] 입력값이 비어있거나 'None'인 경우 즉시 탈출
        if not ai_target_price or str(ai_target_price).strip() == "":
            print(f"⚠️ [{code}] AI 예약가 데이터가 비어있습니다.")
            return None

        clean_price_str = re.sub(r'[^0-9]', '', str(ai_target_price))
        if not clean_price_str: # 숫자가 하나도 없는 경우 방어
            return None
            
        clean_price = int(clean_price_str)
        
        # 2. 유틸리티를 사용하여 호가 규격에 맞게 내림 정규화
        # AI가 준 가격이 19,950원인데 호가 단위가 100원이면 19,900원으로 맞춥니다.
        final_target_price = kiwoom_utils.get_target_price_by_percent(clean_price, drop_percent=0)
        
        if final_target_price <= 0:
            print(f"⚠️ [{code}] 유효하지 않은 예약가입니다.")
            return None

        # 3. 매수 수량 계산
        buy_qty = calc_buy_qty(final_target_price, deposit, ratio)
        
        if buy_qty <= 0:
            print(f"⚠️ [{code}] 예수금 부족으로 예약 주문을 생성할 수 없습니다.")
            return None

        # 4. 지정가(00) 주문 전송
        print(f"🎯 [AI 예약] {code}: {final_target_price:,}원에 {buy_qty}주 낚싯바늘 투척")
        return send_buy_order_market(
            code=code, 
            qty=buy_qty, 
            token=token, 
            order_type="00", # 지정가
            price=final_target_price
        )
        
    except Exception as e:
        print(f"❌ [예약주문 실패] {code}: {str(e)}")
        return None

