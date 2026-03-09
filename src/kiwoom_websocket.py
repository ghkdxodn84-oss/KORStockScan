import asyncio
import websockets
import json
import threading


class KiwoomWSManager:
    def __init__(self, token):
        self.uri = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.token = token
        self.realtime_data = {}
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None

    async def _run_ws(self):
        # 🚀 [핵심 1] 무한 루프(while True)로 감싸서, 끊어지더라도 코루틴이 죽지 않고 다시 시작하게 만듭니다.
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

                    # 🚀 [핵심 2] 재접속 시, 기존에 감시 중이던 종목이 있다면 즉시 다시 구독(REG)을 요청합니다.
                    if self.subscribed_codes:
                        print(f"🔄 [WS] 재접속 감지! 기존 감시 종목({len(self.subscribed_codes)}개) 데이터를 서버에 다시 요청합니다.")
                        # 내부 통신이므로 await를 붙여 확실하게 전송을 보장합니다.
                        await self._send_reg(list(self.subscribed_codes))

                    # 데이터 수신 무한 루프
                    while True:
                        msg = await ws.recv()
                        res = json.loads(msg)

                        trnm = res.get('trnm')
                        if trnm not in ['PING', 'REAL']:
                            # 데이터가 너무 많아 터미널이 지저분해지는 것을 방지 (필요시 주석 해제)
                            # print(f"📥 [WS 서버 응답] {res}")
                            pass

                        if trnm == 'PING':
                            await ws.send(json.dumps(res))
                        elif trnm == 'REAL':
                            for entry in res.get('data', []):
                                dtype = entry.get('type')
                                code = entry.get('item')
                                vals = entry.get('values', {})

                                with self.lock:
                                    if code not in self.realtime_data:
                                        self.realtime_data[code] = {'curr': 0, 'v_pw': 0.0, 'ask_tot': 1, 'bid_tot': 1}

                                    # [0B] 체결데이터 (현재가, 체결강도)
                                    if dtype == '0B':
                                        if '10' in vals: self.realtime_data[code]['curr'] = abs(int(vals['10']))
                                        if '228' in vals: self.realtime_data[code]['v_pw'] = float(vals['228'])
                                    # [0D] 호가데이터 (총매도, 총매수 잔량)
                                    elif dtype == '0D':
                                        if '121' in vals: self.realtime_data[code]['ask_tot'] = int(vals['121'])
                                        if '125' in vals: self.realtime_data[code]['bid_tot'] = int(vals['125'])

            except Exception as e:
                # 🚀 [핵심 3] 10054 에러 등으로 연결이 끊기면 예외를 잡고, 3초 대기 후 루프의 처음으로 돌아가 재접속합니다.
                self.websocket = None
                print(f"❌ [WS] 네트워크 순단 발생 ({e}). 3초 후 불사조 재접속을 시도합니다...")
                await asyncio.sleep(3)

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