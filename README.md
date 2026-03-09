# 🚀 KORStockScan V13.0 - 완전 자동화 멀티 엔진 퀀트 스나이퍼

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)
![Kiwoom API](https://img.shields.io/badge/API-Kiwoom_REST-green?style=flat-square)
![Machine Learning](https://img.shields.io/badge/ML-XGBoost_%7C_LightGBM-orange?style=flat-square)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blueviolet?style=flat-square&logo=telegram)
![Security](https://img.shields.io/badge/Security-Fernet_Encrypted-red?style=flat-square)

**KORStockScan**은 키움증권 REST API와 머신러닝(Stacking Ensemble)을 활용하여 주식 시장을 스캐닝하고, 실시간 웹소켓을 통해 최적의 타점을 잡아내어 완전 자동매매를 수행하는 퀀트 트레이딩 봇입니다.

V13.0 업데이트를 통해 기존 코스피 우량주 스윙 매매를 넘어, **코스닥 주도주(하이브리드 방식)**와 **초단타 스캘핑**까지 동시에 감시하고 매매하는 **'3-Way 멀티 스레드 아키텍처'**로 진화했습니다. 철저하게 분리된 정찰병(Scanner)과 격수(Sniper) 시스템을 통해 무호흡 무인 매매를 집행합니다.

---

## 🛰️ 스캐너 엔진 비교 (Scanner Comparison)

시스템은 `SniperRadar` 모듈을 공유하지만, 전략적 목적에 따라 두 가지 상이한 스캐닝 방식을 운용합니다.

| 구분 | 초단타 스캘핑 스캐너 (Scalping) | 코스닥 AI 하이브리드 스캐너 (KOSDAQ) |
| :--- | :--- | :--- |
| **감시 대상** | 시장 전체 (`000`: 코스피 + 코스닥) | 코스닥 시장 전용 (`101`) |
| **스캔 주기** | **1분 주기** (초고속 탐색) | **15분 주기** (정밀 분석) |
| **분석 깊이** | 실시간 수급 및 가격 급증 (SniperRadar) | **AI 앙상블 모델** + 수급/신용 데이터 결합 |
| **진입 기준** | 등락률 상위 혹은 수급 폭발 (Supernova) | 1차 필터링 후 **AI 확신도 80% 이상** |
| **전략 태그** | `SCALPING` (초단타 전술) | `KOSDAQ_ML` (AI 기반 스윙 전술) |
| **매매 목표** | **+2.0% 익절 / -2.5% 칼손절** | 전략별 가변 익절 및 트레일링 스탑 적용 |

---

## ✨ 핵심 기능 (Key Features)

### 1. SniperRadar (통합 정보국)
* **7개 API 입체 분석**: 거래량 급증(`ka10023`), 프로그램 순매수(`ka90008`), 체결강도 추이(`ka10046`) 등 7개 API를 조합하여 세력의 진입 조짐을 포착합니다.
* **투망 & 현미경 전략**: 시장 전체를 넓게 훑는 '투망' 단계와 개별 종목의 수급을 정밀 검증하는 '현미경' 단계를 거쳐 고확신 타점만 추출합니다.

### 2. AI 앙상블 판독 (KOSPI/KOSDAQ 스윙)
* **Stacking Ensemble**: XGBoost, LightGBM 등 4개 모델의 예측치를 메타 모델이 최종 통합하여 당일 상승 확률을 산출합니다.
* **데이터 통합**: 실시간 일봉(OHLCV), 투자자별 순매수, 신용 잔고율 데이터를 결합하여 입체적인 차트 분석을 수행합니다.

### 3. 실시간 매매 엔진 (Sniper V2)
* **멀티 전략 대응**: DB에 기록된 `strategy` 태그에 따라 초단타, 코스피 스윙, 코스닥 스윙 등 각기 다른 매매 룰을 적용합니다.
* **눌림목 자동 진입**: 스캘핑 포착 시 현재가 대비 정확한 호가 단위를 계산하여 2호가 아래에 매수 대기 주문을 넣어 안전한 진입을 도모합니다.
* **성과 추적**: 매수/매도가, 매매 시간, 수익률을 DB에 영구 기록하여 전략별 승률과 성과를 관리합니다.

---

## 📂 프로젝트 구조 (Project Structure)

```text
/KORStockScan
├── src/
│   ├── bot_main.py               # 🤖 텔레그램 봇 및 전체 시스템 제어 센터
│   ├── signal_radar.py           # 📡 SniperRadar (통합 정보국 모듈)
│   │
│   ├── final_ensemble_scanner.py # 🧠 KOSPI 스윙 스캐너 & AI 판독 모듈
│   ├── kosdaq_scanner.py         # 🔍 KOSDAQ 하이브리드 AI 스캐너
│   ├── scalping_scanner.py       # 🔍 SCALPING 수급 급등주 스캐너
│   │
│   ├── kiwoom_sniper_v2.py       # 🔫 실시간 매매 집행 엔진 (멀티 전략 대응)
│   ├── kiwoom_orders.py          # 🛒 키움증권 REST API 주문 통신 모듈
│   ├── kiwoom_utils.py           # 🛠️ 공통 유틸리티 및 API 연동 라이브러리
│   └── db_manager.py             # 🗄️ SQLite 데이터베이스 통합 관리
└── data/
    ├── config_prod.json          # ⚙️ 시스템 설정 및 API 키 관리
    └── kospi_stock_data.db       # 📊 주가 데이터 및 추천 히스토리 저장
```

---

## ⚙️ 설치 및 설정 (Installation & Setup)

### 1. 환경 준비
* **OS**: Windows 또는 Linux (키움증권 REST API 기반으로 OS 제약이 적습니다.)
* **Python**: 3.13 버전 이상 권장
* **데이터베이스**: SQLite3 (기본 내장)

### 2. 패키지 설치
저장소를 복제하고 필요한 라이브러리를 설치합니다.
```bash
git clone [https://github.com/your-username/KORStockScan.git](https://github.com/your-username/KORStockScan.git)
cd KORStockScan
pip install -r requirements.txt
```

### 3. 시스템 가동
설정 파일(`config_prod.json`) 세팅 후, 전체 시스템 제어 센터인 `bot_main.py`를 실행하면 멀티 스캐너와 매매 엔진이 스레드 방식으로 동시에 가동됩니다.

1. **설정 파일 작성**: `data/config_prod.json` 파일에 키움 API 앱키, 시크릿키, 텔레그램 토큰 등을 올바르게 입력합니다.
2. **통합 엔진 실행**: 터미널에서 아래 명령어를 입력하여 시스템을 시작합니다.
   ```bash
   python src/bot_main.py
   ```
3. **가동 확인**: 터미널에 [시스템] 정상거래일 - 스나이퍼 매매 엔진 가동 완료 등의 메시지가 뜨는지 확인합니다.

---

## 📊 데이터베이스 및 성과 관리
시스템은 모든 추천 이력과 매매 성과를 투명하게 관리하며, 전략별 승률 분석이 가능하도록 설계되었습니다.

* **통합 DB 관리**: `data/kospi_stock_data.db`를 통해 모든 추천 이력, 매수/매도가, 수익률을 통합 관리합니다.
* **자동 스키마 최적화**: 시스템 가동 시 `strategy`(전략 태그), `sell_price`(매도가), `profit_rate`(수익률) 등 필수 컬럼을 자동으로 검사하고 생성하여 DB 에러를 원천 차단합니다.
* **실시간 성적표**: 매매 체결 시 수익률을 영구 기록하며, 텔레그램을 통해 성적표 리포트를 즉시 보고합니다.
* **중복 추천 방지**: 동일 종목이 당일 여러 번 포착되더라도 `already_picked` 로직을 통해 중복 알림과 뇌동매매를 방지합니다.

---

## ⚠️ 면책 조항 (Disclaimer)
본 소프트웨어는 개인적인 투자 참고 및 알고리즘 트레이딩 학습 목적으로 제작되었습니다. 

1. **투자 책임**: 모든 투자 결정에 대한 최종 책임은 사용자 본인에게 있습니다. 제작자는 이 프로그램을 사용하여 발생한 어떠한 경제적 손실에 대해서도 법적 책임을 지지 않습니다.
2. **시스템 리스크**: 주식 거래는 원금 손실의 위험이 매우 크며, 자동 매매 시스템의 예기치 못한 오류, 네트워크 장애, 또는 API 통신 지연으로 인해 손실이 발생할 수 있습니다.
3. **사전 테스트**: 실투자 전에는 반드시 모의투자 환경에서 충분한 테스트를 거친 후 운용하시기 바랍니다.

