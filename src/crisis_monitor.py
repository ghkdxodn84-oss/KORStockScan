import os
import sqlite3
import feedparser
import json
import requests
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 경로 및 환경 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CRISIS_DB_PATH = os.path.join(DATA_DIR, 'crisis_alerts.db')
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')

SOURCES = {
    # 1. 중동/아시아 지정학적 리스크 (가장 빠름)
    "AlJazeera_War": "https://www.aljazeera.com/xml/rss/all.xml",

    # 2. 글로벌 메이저 언론사 속보 (친숙함, 교차 검증용)
    "NYT_World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",

    # 3. 공식 기관 리포트 (가짜 뉴스 필터링)
    "ReliefWeb_Disaster": "https://reliefweb.int/updates/rss.xml",
    "WHO_Pandemic": "https://www.who.int/feeds/entity/csr/don/en/rss.xml"
}

WAR_KEYWORDS = ['war', 'missile', 'strike', 'invasion', 'military', 'conflict', 'nuclear', 'attack']
PANDEMIC_KEYWORDS = ['outbreak', 'virus', 'pandemic', 'epidemic', 'disease', 'quarantine', 'ebola', 'covid', 'h5n1']


# ==========================================
# 2. 텔레그램 브로드캐스트 유틸리티
# ==========================================
def send_telegram_alert(message_text):
    """설정 파일과 유저 DB를 읽어 모든 사용자에게 알림을 전송합니다."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            conf = json.load(f)
        token = conf.get('TELEGRAM_TOKEN')
        if not token: return

        with sqlite3.connect(USERS_DB_PATH) as conn:
            users = conn.execute('SELECT chat_id FROM users').fetchall()

        for (chat_id,) in users:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message_text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            requests.post(url, json=payload, timeout=5)
            time.sleep(0.05)  # 스팸 방지
    except Exception as e:
        print(f"🚨 텔레그램 알림 전송 실패: {e}")


# ==========================================
# 3. 위기 데이터 분석 및 DB 관리
# ==========================================
def init_crisis_db():
    with sqlite3.connect(CRISIS_DB_PATH) as conn:
        conn.execute('''
                     CREATE TABLE IF NOT EXISTS macro_alerts
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         timestamp
                         TEXT,
                         category
                         TEXT,
                         source
                         TEXT,
                         title
                         TEXT,
                         link
                         TEXT
                         UNIQUE,
                         severity_score
                         INTEGER
                     )
                     ''')


def calculate_severity(title):
    title_lower = title.lower()
    is_war = any(kw in title_lower for kw in WAR_KEYWORDS)
    is_pandemic = any(kw in title_lower for kw in PANDEMIC_KEYWORDS)

    if not (is_war or is_pandemic): return None, 0
    category = "WAR" if is_war else "PANDEMIC"
    if is_war and is_pandemic: category = "COMPLEX_CRISIS"

    score = sum(1 for kw in WAR_KEYWORDS + PANDEMIC_KEYWORDS if kw in title_lower)
    return category, min(score, 5)


# ==========================================
# 4. 메인 실행 루프 (수집 -> 판독 -> 알림)
# ==========================================
def run_crisis_monitor():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🌍 [{now_str}] 글로벌 위기 감지 스캐너 가동...")
    init_crisis_db()

    # 💡 [수정] 모든 뉴스가 아닌, '위험도 2점 이상'의 심각한 신규 뉴스만 담는 리스트
    new_severe_alerts = []

    # 1. RSS 피드 스크래핑 및 DB 저장
    with sqlite3.connect(CRISIS_DB_PATH) as conn:
        for source_name, url in SOURCES.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:15]:
                    title = entry.title
                    link = entry.link
                    category, severity = calculate_severity(title)

                    if severity > 0:
                        try:
                            # 일단 위험도 1 이상이면 DB에 모두 기록 (데이터 축적용)
                            conn.execute('''
                                         INSERT INTO macro_alerts (timestamp, category, source, title, link, severity_score)
                                         VALUES (?, ?, ?, ?, ?, ?)
                                         ''', (now_str, category, source_name, title, link, severity))

                            # 🚀 [핵심] 방금 저장된 뉴스의 위험도가 2 이상일 때만 알림 후보로 등록
                            if severity >= 2:
                                new_severe_alerts.append(f"[{category}] {title} (위험도: {severity})")

                        except sqlite3.IntegrityError:
                            # 이미 기록된 뉴스면 패스
                            pass
            except Exception:
                pass
            time.sleep(1)
        conn.commit()

    print(f"✅ 스캔 완료: 텔레그램 트리거 대상 신규 심각 경보 {len(new_severe_alerts)}건 포착.")

    # 2. '심각한 신규 위기'가 방금 포착되었을 때만 누적 리스크를 평가하여 알림 전송
    if new_severe_alerts:
        try:
            time_threshold = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
            with sqlite3.connect(CRISIS_DB_PATH) as conn:
                # 12시간 내 심각한 경보(위험도 2 이상)가 몇 건인지 카운트
                query = "SELECT COUNT(*) FROM macro_alerts WHERE timestamp >= ? AND severity_score >= 2"
                risk_count = conn.execute(query, (time_threshold,)).fetchone()[0]

            # 🚀 [최종 트리거] 누적된 심각 경보가 2건 이상일 때만 (즉, 장중 대응이 필요할 때만) 브로드캐스트
            now_time = datetime.now().time()
            if risk_count >= 2:
                msg = f"🚨 *[시스템 경보: 장중 대응 리스크 감지]*\n"
                msg += f"최근 12시간 내 심각한 글로벌 위기 경보가 **{risk_count}건** 누적되었습니다.\n\n"
                msg += "💡 *권장 대응 시나리오*\n"
                msg += "• **신규 매수 중단 권고:** 거시 경제 변동성 확대 대비\n"

                # 오후 2시 30분 이후라면 오버나잇 회피 강력 권고
                if now_time >= datetime.strptime("14:30:00", "%H:%M:%S").time():
                    msg += "• **⚠️ 보유 자산 청산 권고:** 장 마감 전 오버나잇 리스크 회피를 위한 전량 현금화 고려\n"

                msg += "\n*🚨 방금 발생한 심각한 위기 속보:*\n"
                for alert in new_severe_alerts[:3]:  # 최신 3개만 요약해서 보여줌
                    msg += f"- `{alert}`\n"

                send_telegram_alert(msg)
                print("📢 텔레그램 위기 경보 브로드캐스트 완료.")
            else:
                print(f"ℹ️ 신규 심각 경보가 있으나, 아직 장중 대응 임계치(누적 {risk_count}건)에 도달하지 않아 알림을 보류합니다.")

        except Exception as e:
            print(f"⚠️ 리스크 평가 중 에러 발생: {e}")


if __name__ == "__main__":
    run_crisis_monitor()