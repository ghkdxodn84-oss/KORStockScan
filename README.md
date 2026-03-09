# 🚀 KORStockScan V13.0 - 완전 자동화 멀티 엔진 퀀트 스나이퍼

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)
![Kiwoom API](https://img.shields.io/badge/API-Kiwoom_REST-green?style=flat-square)
![Machine Learning](https://img.shields.io/badge/ML-XGBoost_%7C_LightGBM-orange?style=flat-square)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blueviolet?style=flat-square&logo=telegram)
![Security](https://img.shields.io/badge/Security-Fernet_Encrypted-red?style=flat-square)

**KORStockScan**은 키움증권 REST API와 머신러닝(Stacking Ensemble)을 활용하여 주식 시장을 스캐닝하고, 실시간 웹소켓을 통해 최적의 타점을 잡아내어 완전 자동매매를 수행하는 퀀트 트레이딩 봇입니다. 

V13.0 업데이트를 통해 기존 코스피 우량주 스윙 매매를 넘어, **코스닥 주도주(하이브리드 온디맨드 방식)**와 **초단타 스캘핑**까지 동시에 감시하고 매매하는 **'3-Way 멀티 스레드 아키텍처'**로 진화했습니다. 철저하게 분리된 정찰병(Scanner)과 격수(Sniper) 시스템을 통해 무호흡 무인 매매를 집행합니다.

---

## ✨ 핵심 기능 (Key Features)

* 🧠 **콰트로 앙상블 AI (Stacking Meta Model)**
  * XGBoost와 LightGBM을 기반으로 상승장(Bull) 전용 모델과 범용 하이브리드 모델을 혼합하여 단기 상승 확률(Prob)을 0.1초 만에 판독합니다.
* ⚡ **3-Way 정찰 시스템 (멀티 스캐너)**
  * **KOSPI 우량주 스윙 (`final_ensemble_scanner.py`):** 외인/기관의 매집 가속도를 분석해 안정적인 우량주를 타겟팅합니다.
  * **KOSDAQ 하이브리드 (`kosdaq_scanner.py`):** 당일 수급이 터진 코스닥 종목만 1차 선별(ka10027)한 뒤, 실시간 일봉 데이터를 수집(ka10081)해 AI로 분석하는 효율적인 온디맨드 방식을 채택했습니다.
  * **초단타 스캘핑 (`scalping_scanner.py`):** 실시간 등락률, 체결강도, 거래대금을 분석하여 1초 단위로 시장가 급등주를 낚아챕니다.
* 🔫 **통합 스나이퍼 매매 엔진 (`kiwoom_sniper_v2.py`)**
  * 스캐너가 물어온 타겟의 전략 태그(`KOSPI_ML`, `KOSDAQ_ML`, `SCALPING`)를 인식하여, 각기 다른 손절선과 트레일링 스탑, 타임아웃 룰(Time-Stop)을 다르게 적용해 스마트하게 청산합니다.
* 🛡️ **철통 보안 시스템 (Fernet 대칭키 암호화)**
  * API Key와 텔레그램 토큰이 담긴 설정 파일을 `config_prod.enc`로 암호화하여, 소스코드가 유출되어도 시스템 환경변수 마스터 키(`KORSTOCK_KEY`) 없이는 절대 접근할 수 없습니다.

---

## 🏗️ 시스템 아키텍처 (Architecture)

시스템은 `bot_main.py`의 지휘 아래 3개의 독립적인 모듈이 유기적으로 동작합니다.

1.  **관제탑 (`bot_main.py`):** 텔레그램 봇 폴링 및 멀티 스레드(매매 엔진, 스캐너 1/2)를 백그라운드 데몬으로 동시 가동하고 야간 자동 셧다운을 관리합니다.
2.  **정찰병 (Scanners):** 각자의 영역(코스피, 코스닥, 스캘핑)에서 타겟을 찾아 DB(`recommendation_history`)에 전략 태그와 함께 기록합니다.
3.  **격수 (Sniper):** DB를 15초 단위로 감시하다가 타겟이 들어오면 즉시 웹소켓 호가창에 연결, 체결강도(VPW) 폭발 시 **시장가 매수**를 집행하고 독립적인 룰에 따라 청산합니다.
4.  **중앙 통제소 (`constants.py`):** 모든 매매 기준(타겟 수익률, 손절선, 쿨타임 등)을 단일 진실 공급원에서 통제합니다.

---

## 📂 주요 디렉토리 구조 (Directory Structure)

```text
KORStockScan/
│
├── data/
│   ├── config_prod.enc           # 암호화된 API 설정 파일
│   ├── kospi_stock_data.db       # 종목 발굴 이력 및 상태 관리 DB
│   └── *.pkl                     # AI 앙상블 학습 모델 파일들
│
├── src/
│   ├── bot_main.py               # 🚀 메인 관제탑 (실행 파일)
│   ├── constants.py              # ⚙️ 중앙 통제소 (매매 룰, 변수 설정)
│   ├── encrypt_config.py         # 🛡️ 보안 키 암호화 스크립트
│   │
│   ├── final_ensemble_scanner.py # 🔍 KOSPI 스윙 스캐너 & AI 판독 모듈
│   ├── kosdaq_scanner.py         # 🔍 KOSDAQ 하이브리드 스캐너
│   ├── scalping_scanner.py       # 🔍 SCALPING 급등주 스캐너
│   │
│   ├── kiwoom_sniper_v2.py       # 🔫 실시간 매매 집행 엔진 (웹소켓 연동)
│   ├── kiwoom_orders.py          # 🛒 키움증권 매수/매도 API 통신
│   └── kiwoom_utils.py           # 🛠️ 각종 공통 유틸리티 (API 호출 등)
```

---

## ⚙️ 설치 및 설정 (Installation & Setup)

### 1. 환경 준비
* **Windows / Linux OS** (키움증권 REST API는 OS 제약이 비교적 적습니다.)
* **Python 3.13+**

### 2. 패키지 설치
```bash
git clone https://github.com/your-username/KORStockScan.git
cd KORStockScan
pip install -r requirements.txt
```

### 3. 보안 파일 암호화 셋업
보안을 위해 `config_prod.json` 원본 파일을 만들고 암호화 스크립트를 실행해야 합니다.

```bash
# 1. 암호화 스크립트 실행하여 config_prod.enc 생성 및 마스터 키 발급
python src/encrypt_config.py 

# 2. 발급받은 마스터 키를 환경변수에 등록 (Windows CMD 예시)
set KORSTOCK_KEY=발급받은_마스터_키_문자열
```
*(주의: 원본 json 파일은 암호화 완료 후 반드시 삭제하거나 안전한 오프라인 저장소에 백업하세요.)*

### 4. 전략 튜닝 (`constants.py`)
시장 상황에 맞게 `constants.py`의 수치들을 자유롭게 튜닝하세요.
* `SCALP_TARGET` / `SCALP_STOP`: 초단타 익절/손절선 (예: +2.0% / -2.5%)
* `SCALP_TIME_LIMIT_MIN`: 초단타 타임아웃 청산 시간 (예: 30분)
* `KOSDAQ_TARGET` / `KOSDAQ_STOP`: 코스닥 전용 타이트 룰 (예: 트레일링 +4.0% / 손절 -2.0%)
* `TRAILING_START_PCT`: 코스피 스윙 가변 익절 방어선 가동 시작점 (예: +3.5%)

### 5. 통합 시스템 기동
환경변수가 세팅된 터미널에서 아래 명령어 한 줄로 모든 시스템(텔레그램, 매매 엔진, 3대 스캐너)을 기동합니다.
```bash
python src/bot_main.py
```

---

## ⚠️ 면책 조항 (Disclaimer)
본 프로젝트는 알고리즘 트레이딩 및 AI 모델링 학습 목적으로 개발되었습니다. 본 시스템을 사용하여 발생하는 모든 금전적 손실과 법적 책임은 전적으로 사용자 본인에게 있습니다. 실전 투자 전 반드시 모의투자를 통해 충분히 검증하시기 바랍니다.