import requests
import kiwoom_utils
import json
import re
from datetime import datetime

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

def get_my_inventory(token, config):
    """
    [kt00018] 계좌평가잔고내역을 조회합니다.
    SOR 주문을 고려하여 KRX(한국거래소)와 NXT(넥스트트레이드)의 잔고를 모두 합산합니다.
    """
    host = 'https://api.kiwoom.com'  # 실전투자
    endpoint = '/api/dostk/acnt'
    url = host + endpoint

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00018',
    }

    # 💡 [핵심] 종목 코드를 키(Key)로 사용하여 양쪽 거래소의 수량을 합산할 딕셔너리
    aggregated_inventory = {}

    # KRX와 NXT를 순차적으로 조회합니다.
    exchanges = ['KRX', 'NXT']
    
    for exchange in exchanges:
        params = {
            'qry_tp': '1',             # 조회구분 1:합산
            'dmst_stex_tp': exchange   # 국내거래소구분
        }

        try:
            response = requests.post(url, headers=headers, json=params)
            data = response.json()
            
            if data.get('return_code') == 0:
                stock_list = data.get('acnt_evlt_remn_indv_tot', [])
                
                for item in stock_list:
                    # "A005930" -> "005930" 변환
                    raw_code = item.get('stk_cd', '')
                    code = raw_code[1:] if raw_code.startswith('A') else raw_code
                    
                    qty = int(item.get('rmnd_qty', 0))
                    name = item.get('stk_nm', '')
                    
                    if qty > 0:
                        if code in aggregated_inventory:
                            # 이미 다른 거래소에서 조회된 수량이 있다면 누적해서 더합니다.
                            aggregated_inventory[code]['qty'] += qty
                        else:
                            # 처음 발견된 종목이면 딕셔너리에 신규 등록합니다.
                            aggregated_inventory[code] = {
                                'code': code,
                                'name': name,
                                'qty': qty
                            }
            else:
                err_msg = data.get('return_msg', '알 수 없는 오류')
                print(f"⚠️ [API 경고] {exchange} 잔고 조회 실패: {err_msg}")

        except Exception as e:
            print(f"❌ [API 에러] {exchange} 잔고 통신 실패: {e}")

    # 딕셔너리의 Value들만 뽑아서 리스트 형태로 반환합니다.
    return list(aggregated_inventory.values())

def send_buy_order_market(code, qty, token, config=None, order_type="6", price=0):
    """
    [kt10000] 매수 주문 - return_code 대응 수정 및 지정가(00) 기능 추가
    - order_type: "00" (지정가 - 스캘핑 눌림목 그물망용)
                  "6"  (최유리지정가 - 기본값, 우량주 스윙용)
                  "3"  (시장가 - 강력한 추격 매수용)
    - price: 지정가 주문 시 입력할 1주당 단가 (시장가/최유리 지정가일 경우 0 또는 생략)
    """
    if qty <= 0: return None

    code = code[0:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"
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
        "stk_cd": str(code),
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,     # 🚀 드디어 2호가 아래 가격이 이 자리로 꽂힙니다!
        "trde_tp": str(order_type),  # "00", "3", "6" 등 외부에서 받아온 타입
        "cond_uv": ""
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        # rt_cd 또는 return_code 둘 중 하나라도 0이면 성공으로 간주
        is_success = str(data.get('rt_cd', '')) == '0' or str(data.get('return_code', '')) == '0'

        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code') if data.get('return_code') is not None else data.get('rt_cd')
            import kiwoom_utils # 예외 처리 시 참조를 위해
            kiwoom_utils.log_error(f"❌ [매수거절] 종목:{code}, 사유:{err_msg} (코드:{err_code})", config=config,
                                   send_telegram=True)
            return None
    except Exception as e:
        import kiwoom_utils
        kiwoom_utils.log_error(f"🔥 [매수주문] 시스템 예외: {str(e)}", config=config, send_telegram=True)
        return None

def reserve_buy_order_ai(code, ai_target_price, deposit, token, config, ratio=0.05):
    """
    [v12.9] AI 권장 타점을 바탕으로 지정가 매수 예약 주문을 전송합니다.
    """
    try:
        # 1. AI 응답에서 숫자만 추출 (예: "50,500원" -> 50500)
        clean_price = int(re.sub(r'[^0-9]', '', str(ai_target_price)))
        
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
            config=config, 
            order_type="00", # 지정가
            price=final_target_price
        )
        
    except Exception as e:
        print(f"❌ [예약주문 실패] {code}: {str(e)}")
        return None

def send_smart_sell_order(code, qty, token, ws_data, reason_type='PROFIT', config=None):
    """
    [v12.3] 웹소켓 '0D' 데이터 구조 전용 스마트 매도 로직
    - reason_type: 'PROFIT' (익절) -> 지정가 위주
                   'LOSS'   (손절) -> 시장가 즉시 탈출
    """
    if qty <= 0: return None

    # 1. 매수 1호가 데이터 추출 (제공해주신 '0D' 구조 반영)
    try:
        orderbook = ws_data.get('orderbook', {})
        bids = orderbook.get('bids', [])
        
        if not bids:
            print(f"⚠️ [{code}] 매수 호가 데이터가 없어 시장가로 전환합니다.")
            return send_sell_order_market(code, qty, token, config=config, order_type="3")

        # 매수 1호가 정보 (bids[0] 이 가장 높은 매수 호가)
        bid_1_p = bids[0].get('price', 0)
        bid_1_q = bids[0].get('volume', 0)
        
    except (IndexError, KeyError, TypeError) as e:
        print(f"❌ [{code}] 호가 데이터 파싱 실패: {e}")
        return send_sell_order_market(code, qty, token, config=config, order_type="3")

    # 2. 매매 성격에 따른 주문 분기
    # 🚨 손절(LOSS): 가격 불문, 시장가(3) 즉시 체결
    if reason_type == 'LOSS':
        print(f"🚨 [긴급손절] {code}: 시장가 매도 (수량: {qty})")
        return send_sell_order_market(code, qty, token, config=config, order_type="3")

    # 💰 익절(PROFIT): 슬리피지 방어 가동
    else:
        # 매수 1호가 잔량이 내 물량보다 넉넉한지 확인
        if bid_1_p > 0 and bid_1_q >= qty * 1.2:
            print(f"💰 [스마트익절] {code}: 1호가({bid_1_p:,}원) 지정가 매도 (호가잔량: {bid_1_q}주)")
            return send_sell_order_market(code, qty, token, config=config, order_type="00", price=bid_1_p)
        
        else:
            # 1호가 잔량이 부족하면 '최유리지정가(6)'로 던져서 슬리피지 최소화
            print(f"⚠️ [슬리피지방어] {code}: 1호가 잔량 부족. 최유리지정가(6) 매도")
            return send_sell_order_market(code, qty, token, config=config, order_type="6")

def send_sell_order_market(code, qty, token, config=None, order_type="3", price=0):
    """
    [개조 버전] 매도 주문 - 지정가/시장가/최유리 선택 가능
    - order_type: "00"(지정가), "3"(시장가), "6"(최유리지정가)
    """
    if qty <= 0: return None

    code = code[0:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10001'
    }

    # 지정가일 때만 가격 입력
    ord_price_str = str(int(price)) if order_type == "00" and price > 0 else ""

    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": str(code),
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
            err_msg = data.get('return_msg') or '상세 사유 없음'
            kiwoom_utils.log_error(f"❌ [매도거절] {code}, 사유: {err_msg}", config=config, send_telegram=True)
            return data # 실패 시에도 응답값을 넘겨서 이유를 분석하게 함
    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [매도주문 예외] {str(e)}", config=config, send_telegram=True)
        return None

def get_deposit(token, config=None):
    """
    [kt00001] 예수금 조회 - return_code 대응 수정
    """
    url = "https://api.kiwoom.com/api/dostk/acnt"
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
            kiwoom_utils.log_error(f"❌ [예수금조회 실패] 사유: {err_msg}", config=config)
            return 0
    except:
        return 0


def send_cancel_order(code, orig_ord_no, token, qty=0, config=None):
    """
    [kt10003] 주식 취소 주문 - 미체결 물량 취소
    :param qty: 취소 수량. 기본값 0 (0 입력 시 미체결 잔량 전부 취소)
    """
    clean_code = str(code)[:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"

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

        # return_code 0이 성공
        if res.status_code == 200 and str(data.get('return_code', '')) == '0':
            cncl_qty_result = data.get('cncl_qty', '전량') # 빈 값이면 '전량'으로 표기
            new_ord_no = data.get('ord_no', '')
            # 메시지에 cncl_qty_result 활용!
            print(f"✅ [취소접수] {clean_code} {cncl_qty_result}주 취소 성공 (새주문번호:{new_ord_no})")
            return data
        else:
            err_msg = data.get('return_msg', '상세 사유 없음')
            kiwoom_utils.log_error(f"❌ [취소거절] {clean_code}: {err_msg}", config=config, send_telegram=True)
            return None

    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [취소주문] 시스템 예외: {str(e)}", config=config, send_telegram=True)
        return None
