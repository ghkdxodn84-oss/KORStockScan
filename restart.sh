#!/bin/bash

# ============================================================
# 🚀 KORStockScan V13.0 통합 재시작 스크립트
# ============================================================

PROJECT_DIR="/home/ubuntu/KORStockScan2"
VENV_PATH="$PROJECT_DIR/venv/bin/activate"
LOG_DIR="$PROJECT_DIR/logs"

# 1. 로그 디렉토리 생성 (없을 경우)
mkdir -p $LOG_DIR

echo "🔄 [1/4] 기존 봇 프로세스 종료 중..."

# 💡 방법 A: 파일명 기반 (가장 확실함)
pkill -9 -f "kiwoom_sniper_v2.py"
pkill -9 -f "telegram_manager.py"
pkill -9 -f "bot_main.py"
rm -f "$PROJECT_DIR/restart.flag" # 재시작 플래그 파일 삭제

sleep 2

echo "🐍 [2/4] 가상환경(venv) 활성화 중..."
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "🚨 에러: 가상환경을 찾을 수 없습니다 ($VENV_PATH)"
    exit 1
fi

echo "🔫 [3/4] 스나이퍼 엔진 및 텔레그램 매니저 가동..."
# 💡 nohup을 사용하여 터미널을 꺼도 백그라운드에서 계속 돌아가게 합니다.
# 💡 로그는 logs 디렉토리에 분리하여 저장합니다.
nohup python src/engine/kiwoom_sniper_v2.py >> "$LOG_DIR/sniper_$(date +%Y%m%d).log" 2>&1 &
nohup python src/notify/telegram_manager.py >> "$LOG_DIR/telegram_$(date +%Y%m%d).log" 2>&1 &

sleep 1

echo "✅ [4/4] 모든 시스템 재가동 완료!"
echo "------------------------------------------------------------"
echo "📡 실시간 로그 확인: tail -f logs/sniper_$(date +%Y%m%d).log"
echo "🤖 프로세스 확인: ps -ef | grep KORStockScan"
echo "------------------------------------------------------------"