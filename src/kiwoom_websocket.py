import asyncio
import websockets
import json
import threading
from datetime import datetime

class KiwoomWSManager:
    # 💡 1. 초기화 함수에 체결 통보용 콜백(on_execution_callback) 추가
    def __init__(self, token, on_execution_callback=None):
        self.uri = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.token = token
        self.realtime_data = {}
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None
        self.on_execution_callback = on_execution_callback

    async def _run_ws(self):
        while True:
            try:
                print("🔌 [WS] 키움 서버에 연결을 시도합니다...")
                async with websockets.connect(self.uri) as ws:
                    self.websocket = ws
                    print("✅ [WS] 웹소켓 연결 성공!")

                    # 로그인 패킷 전송
                    login_packet = {'trnm': 'LOGIN', 'token': self.token}
                    await ws.send(json.dumps(login_packet))
                    print("🔑 [WS] 로그인 패킷 전송 완료")

                    # 🚀 2. [핵심] 계좌 전체 주문체결(00) 감시 등록 (빈 배열 전송)
                    exec_reg_packet = {
                        "trnm": "REG",
                        "grp_no": "2",  # 기존 호가/체결(1)과 분리하기 위해 2 사용
                        "refresh": "1",
                        "data": [
                            {
                                "item": [""],   # 종목코드 불필요
                                "type": ["00"]  # 주문체결 타입
                            }
                        ]
                    }
                    await ws.send(json.dumps(exec_reg_packet))
                    print("📝 [WS] 🚨 계좌 주문/체결통보(00) 감시망 등록 완료!")

                    # 기존 감시 종목 재등록
                    if self.subscribed_codes:
                        await self._send_reg(list(self.subscribed_codes))

                    # 메시지 수신 루프
                    while True:
                        message = await ws.recv()
                        await self._handle_message(message)

            except websockets.ConnectionClosed:
                print("⚠️ [WS] 연결 끊김! 3초 후 재접속 시도...")
                self.websocket = None
                await asyncio.sleep(3)
            except Exception as e:
                print(f"🚨 [WS] 예상치 못한 오류: {e}")
                self.websocket = None
                await asyncio.sleep(3)

    async def _handle_message(self, message):
        try:
            msg_dict = json.loads(message)
            
            # 💡 3. 데이터 파싱 로직
            if 'data' in msg_dict:
                for d in msg_dict['data']:
                    values = d.get('values', {})
                    if not values: continue

                    # ===================================================
                    # [트랙 A] 🚨 주문/체결 통보 가로채기 (type: 00)
                    # ===================================================
                    if '913' in values:  # 913은 키움증권 '주문상태' FID입니다.
                        status = values.get('913')
                        code = values.get('9001', '').replace('A', '') # 종목코드 정제
                        order_no = values.get('9203', '')              # 주문번호
                        order_type = values.get('905', '')             # '+매수' or '-매도'
                        
                        # 오직 '체결'이 발생했을 때만 영수증(콜백)을 보냅니다. (접수/취소는 무시)
                        if status == '체결':
                            raw_price = values.get('910', '0').replace('+', '').replace('-', '')
                            raw_qty = values.get('911', '0').replace('+', '').replace('-', '')
                            
                            exec_price = int(raw_price) if raw_price.isdigit() else 0
                            exec_qty = int(raw_qty) if raw_qty.isdigit() else 0
                            
                            print(f"🔔 [WS 실제체결] {code} {order_type} {exec_qty}주 @ {exec_price}원 (주문번호: {order_no})")
                            
                            # 스나이퍼 엔진으로 확실한 영수증 전송
                            if exec_price > 0 and self.on_execution_callback:
                                self.on_execution_callback({
                                    'code': code,
                                    'order_no': order_no,
                                    'type': 'BUY' if '매수' in order_type else 'SELL',
                                    'price': exec_price,
                                    'qty': exec_qty,
                                    'time': datetime.now().strftime('%H:%M:%S')
                                })
                        continue # 체결 통보 파싱이 끝났으므로 아래 가격 파싱은 건너뜀

                    # ===================================================
                    # [트랙 B] 기존 실시간 주가/호가 처리 (type: 0B, 0D)
                    # ===================================================
                    item_code = d.get('item', '')
                    if item_code and '10' in values: # 10은 '현재가' FID입니다.
                        raw_curr = values.get('10', '0').replace('+', '').replace('-', '')
                        curr_price = int(raw_curr) if raw_curr.isdigit() else 0
                        if curr_price > 0:
                            with self.lock:
                                self.realtime_data[item_code] = {
                                    'curr': curr_price,
                                    'time': datetime.now().strftime('%H:%M:%S')
                                }
        except Exception as e:
            pass # 불필요한 에러 로그 방지

    def start(self):
        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_ws())

        threading.Thread(target=thread_target, daemon=True).start()

    async def _send_reg(self, codes):
        try:
            for _ in range(50):
                if self.websocket:
                    break
                await asyncio.sleep(0.1)

            if self.websocket:
                print(f"📝 [WS] 종목 등록(REG) 전송 시도: {codes}")
                reg_packet = {
                    'trnm': 'REG',
                    'grp_no': '1',
                    'refresh': '1',
                    'data': [
                        {'item': codes, 'type': ['0B']},
                        {'item': codes, 'type': ['0D']}
                    ]
                }
                await self.websocket.send(json.dumps(reg_packet))
                self.subscribed_codes.update(codes)
                print(f"📡 [WS] 종목 등록 완료 및 데이터 수신 시작: {codes}")
            else:
                print(f"⚠️ [WS] 연결된 웹소켓이 없어 전송 실패: {codes}")

        except Exception as e:
            print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")

    def subscribe(self, codes):
        if not codes: return
        if isinstance(codes, str): codes = [codes]

        new_targets = [c for c in codes if c not in self.subscribed_codes]

        if new_targets and self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_reg(new_targets), self.loop)

            def on_complete(fut):
                try:
                    fut.result()
                except Exception as e:
                    print(f"🚨 [WS] 스레드 통신 간 에러 발생: {e}")

            future.add_done_callback(on_complete)

    def get_latest_data(self, code):
        with self.lock:
            return self.realtime_data.get(code, {})