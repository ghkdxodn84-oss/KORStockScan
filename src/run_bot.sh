#!/bin/bash

# 무한 루프 시작
while true; do
    echo "🚀 KORStockScan 스나이퍼 엔진을 시작합니다..."

    # 2026-05-06 intraday cash withdrawal override:
    # orderable cash is expected to be about 3,000,000 KRW today.
    # Keep the 1-share initial entry cap; only re-anchor scalping budget math.
    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN=1.0
    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX=1.0
    export KORSTOCKSCAN_SCALPING_MAX_BUY_BUDGET_KRW=3000000

    THRESHOLD_RUNTIME_ENV="../data/threshold_cycle/runtime_env/threshold_runtime_env_$(TZ=Asia/Seoul date +%F).env"
    if [ -f "$THRESHOLD_RUNTIME_ENV" ]; then
        echo "📌 threshold runtime env 적용: $THRESHOLD_RUNTIME_ENV"
        set -a
        # shellcheck source=/dev/null
        . "$THRESHOLD_RUNTIME_ENV"
        set +a
    fi

    # 봇 실행 (경로나 파일명은 환경에 맞게 수정)
    python bot_main.py

    echo "🛑 봇 프로세스가 종료되었습니다."
    echo "⏳ 5초 후 엔진을 재가동합니다. (완전 종료를 원하면 지금 Ctrl+C를 누르세요)"
    sleep 5
done

# 깃허브 연동 테스트
