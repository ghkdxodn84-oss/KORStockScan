import sqlite3
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. DB 경로 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')


def run_diagnostics():
    print("🕵️‍♂️ [KORStockScan] 스캘핑(SCALPING) 거래 이력 진단을 시작합니다...\n")

    try:
        conn = sqlite3.connect(DB_PATH)
        # 스캘핑 전략으로 들어간 모든 종목 조회
        query = """
                SELECT date, buy_time, name, code, buy_price, status
                FROM recommendation_history
                WHERE strategy = 'SCALPING' OR type = 'SCALP'
                ORDER BY date DESC, buy_time DESC \
                """
        df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        print(f"🚨 DB 로드 실패: {e}")
        return

    if df.empty:
        print("⚠️ 스캘핑 거래 이력이 없습니다. 아직 봇이 타겟을 잡지 못했거나, 오늘 처음 가동하셨을 수 있습니다.")
        return

    # 오늘 날짜 필터링
    today_str = datetime.now().strftime('%Y-%m-%d')
    df_today = df[df['date'] == today_str].copy()

    print("==========================================")
    print(f"📊 {today_str} (오늘) 스캘핑 스캐너 타겟 분석")
    print("==========================================")

    if df_today.empty:
        print("오늘 포착된 스캘핑 타겟이 없습니다.")
    else:
        total_targets = len(df_today)
        # buy_time이 있는 것만 실제 매수 시도(또는 성공)한 종목
        attempted = df_today[df_today['buy_time'].notnull() & (df_today['buy_time'] != '')]

        print(f"🎯 총 포착된 타겟: {total_targets}건")
        print(f"🔫 실제 매수 방아쇠를 당긴 횟수: {len(attempted)}건")

        status_counts = df_today['status'].value_counts()
        print("\n[현재 상태별 분포]")
        for status, count in status_counts.items():
            print(f" - {status}: {count}건")

        print("\n🕒 [시간대별 매수 진입 타임라인]")
        if attempted.empty:
            print(" -> 진입 이력이 없습니다.")
        else:
            # 시간순으로 정렬하여 출력 (오전 -> 오후)
            attempted_sorted = attempted.sort_values(by='buy_time')
            for _, row in attempted_sorted.iterrows():
                b_time = row['buy_time']
                name = row['name']
                price = row['buy_price']
                status = row['status']

                # 상태에 따라 아이콘 변경
                icon = "🟢" if status == 'COMPLETED' else "🟡" if status == 'HOLDING' else "⚪"
                print(f"{icon} [{b_time}] {name} (진입가: {int(price):,}원) -> 최종 상태: {status}")

    print("==========================================")
    print("💡 [퀀트의 진단 포인트]")
    print("1. 타겟은 많은데 '매수 방아쇠' 횟수가 적다면?")
    print("   -> 갭(Gap) 상승 1.5% 필터에 걸려 진입을 잘 참고 있다는 뜻입니다. (방어 성공)")
    print("2. 'COMPLETED(종료)' 종목들의 진입 시간대를 확인하세요.")
    print("   -> 텔레그램 로그와 비교했을 때, 특정 시간대(예: 09:00~09:30)에 들어간 종목이 유독 손절이 많다면, 아침장 변동성에 당한 것입니다.")
    print("==========================================")


if __name__ == "__main__":
    run_diagnostics()