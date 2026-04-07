import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import feedparser
from deep_translator import GoogleTranslator

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.utils.logger import log_error
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus

# 설정 상수 (수정 없음)
SOURCES = {
    "AlJazeera_War": "https://www.aljazeera.com/xml/rss/all.xml",
    "NYT_World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "ReliefWeb_Disaster": "https://reliefweb.int/updates/rss.xml",
    "WHO_Pandemic": "https://www.who.int/feeds/entity/csr/don/en/rss.xml"
}
WAR_KEYWORDS = ['war', 'missile', 'strike', 'invasion', 'military', 'conflict', 'nuclear', 'attack']
PANDEMIC_KEYWORDS = ['outbreak', 'virus', 'pandemic', 'epidemic', 'disease', 'quarantine', 'ebola', 'covid', 'h5n1']

db_manager = DBManager()
event_bus = EventBus()

def calculate_severity(title):
    title_lower = title.lower()
    is_war = any(kw in title_lower for kw in WAR_KEYWORDS)
    is_pandemic = any(kw in title_lower for kw in PANDEMIC_KEYWORDS)
    if not (is_war or is_pandemic): return None, 0
    category = "WAR" if is_war else "PANDEMIC"
    score = sum(1 for kw in WAR_KEYWORDS + PANDEMIC_KEYWORDS if kw in title_lower)
    return category, min(score, 5)

def is_telegram_send_allowed():
    """
    텔레그램 브로드캐스트가 허용된 시간인지 확인
    9PM(21:00) ~ 8AM(08:00) 사이는 텔레그램 전송 차단
    """
    current_hour = datetime.now().hour
    # 21시 이상 또는 8시 미만이면 전송 불가 (9PM ~ 8AM)
    if current_hour >= 21 or current_hour < 8:
        return False
    return True

def run_crisis_monitor():
    now = datetime.now()
    print(f"🌍 [{now.strftime('%Y-%m-%d %H:%M:%S')}] 글로벌 위기 감지 스캐너 가동...")

    new_severe_alerts = []

    # 1. RSS 스캔 및 DB 저장 (DBManager 위임)
    for source_name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                category, severity = calculate_severity(entry.title)
                if severity > 0:
                    alert_data = {
                        'alert_time': now, # 💡 PostgreSQL timestamp 형식 호환
                        'category': category,
                        'source': source_name,
                        'title': entry.title,
                        'link': entry.link,
                        'severity_score': severity
                    }
                    if db_manager.save_macro_alert(alert_data):
                        if severity >= 2:
                            new_severe_alerts.append({"category": category, "severity": severity, "en_title": entry.title})
        except Exception as e:
            log_error(f"RSS 스크래핑 에러 ({source_name}): {e}")
        time.sleep(1)

    # 2. 리스크 평가 및 알림 (DBManager 위임)
    if new_severe_alerts:
        risk_count = db_manager.get_recent_risk_count(hours=12, min_severity=2)
        
        if risk_count >= 4:
            # 💡 [우아한 개선] 번역 및 메시지 조립 로직
            translator = GoogleTranslator(source='auto', target='ko')
            msg = f"🚨 *[시스템 경보: 매매 리스크 감지]*\n최근 12시간 내 심각한 위기 경보가 **{risk_count}건** 누적되었습니다.\n\n"
            
            for alert in new_severe_alerts[:3]:
                try: ko_title = translator.translate(alert["en_title"])
                except: ko_title = alert["en_title"]
                msg += f"▪️ **[{alert['category']}]** {ko_title}\n"

            # ⏰ 텔레그램 전송 가능 시간 확인 (9PM ~ 8AM 제외)
            if is_telegram_send_allowed():
                event_bus.publish('TELEGRAM_BROADCAST', {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'})
                print(f"📢 위기 경보 브로드캐스트 완료 (누적: {risk_count}건)")
            else:
                current_hour = datetime.now().hour
                print(f"⏸️ 위기 경보 텔레그램 전송 차단 (현재: {current_hour}시 - 야간 조용한 시간 21시~8시)")

if __name__ == "__main__":
    run_crisis_monitor()