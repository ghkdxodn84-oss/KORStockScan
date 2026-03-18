# src/database/db_manager.py
import pandas as pd
import src.utils.constants as const
from datetime import datetime
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.constants import POSTGRES_URL 
from sqlalchemy import func
from sqlalchemy import text
from contextlib import contextmanager
from src.utils.constants import TRADING_RULES

# 💡 MacroAlert 등 새로 추가된 모델들도 모두 임포트합니다.
from src.database.models import Base, User, RecommendationHistory, DailyStockQuote, MacroAlert
from src.utils.logger import log_error

class DBManager:
    """
    KORStockScan 시스템의 데이터베이스 접근 및 세션 관리를 전담하는 ORM 매니저
    """
    def __init__(self, db_url=POSTGRES_URL):
        self.engine = create_engine(
            db_url,
            pool_size=20,          
            max_overflow=10,       
            pool_timeout=30,       
            pool_pre_ping=True     
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def init_db(self):
        """프로그램 기동 시 테이블이 없으면 생성합니다."""
        Base.metadata.create_all(bind=self.engine)
        print("✅ 데이터베이스 초기화 및 테이블 검증 완료")
    
    @contextmanager
    def get_session(self):
        """DB 세션을 안전하게 열고 닫는 제너레이터 (에러 발생 시 롤백 보장)"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log_error(f"DB Transaction Error: {str(e)}")
            print(f"⚠️ DB Transaction Error: {e}")
            raise
        finally:
            session.close()

    # --------------------------------------------------------
    # 1. Pandas DataFrame 연동
    # --------------------------------------------------------
    def get_stock_data(self, code: str, limit: int = 60) -> pd.DataFrame:
        """Pandas는 SQLAlchemy engine을 직접 지원하므로 안전하게 연동 가능"""
        # 💡 [변경] code -> stock_code, date -> quote_date 반영
        query = f"SELECT * FROM daily_stock_quotes WHERE stock_code='{code}' ORDER BY quote_date DESC LIMIT {limit}"
        df = pd.read_sql(query, self.engine)
        if not df.empty:
            df = df.sort_values('quote_date').reset_index(drop=True)
        return df

    # --------------------------------------------------------
    # 2. 매매 이력 및 종목 관리
    # --------------------------------------------------------
    def save_recommendation(self, date: str, code: str, name: str, price: int, pick_type: str, position: str, prob: float = 0.7):
        """종목 추천 이력 저장 (존재하면 업데이트, 없으면 인서트)"""
        with self.get_session() as session:
            # 💡 [변경] rec_date, stock_code 필터링 적용
            record = session.query(RecommendationHistory).filter_by(rec_date=date, stock_code=code).first()
            
            if record: # Update
                record.buy_price = price
                record.trade_type = pick_type # 💡 type -> trade_type
                record.position_tag = position
                record.prob = prob
                if record.status == 'EXPIRED':
                    record.status = 'WATCHING'
            else:      # Insert
                new_record = RecommendationHistory(
                    rec_date=date,           # 💡 date -> rec_date
                    stock_code=code,         # 💡 code -> stock_code
                    stock_name=name,         # 💡 name -> stock_name
                    buy_price=price, 
                    trade_type=pick_type,    # 💡 type -> trade_type
                    position_tag=position, 
                    prob=prob
                )
                session.add(new_record)

    def update_sell_record(self, code: str, sell_price: int, profit_rate: float, status: str = 'COMPLETED'):
        """매도 완료 기록 업데이트"""
        # 💡 [변경] 모델이 진정한 DateTime으로 바뀌었으므로 문자열이 아닌 datetime 객체를 넘깁니다.
        sell_time_obj = datetime.now()
        
        with self.get_session() as session:
            # 💡 [변경] code -> stock_code
            records = session.query(RecommendationHistory).filter(
                RecommendationHistory.stock_code == code,
                RecommendationHistory.status.in_(['HOLDING', 'SELL_ORDERED'])
            ).all()
            
            for record in records:
                record.status = status
                record.sell_price = sell_price
                record.sell_time = sell_time_obj # 💡 파이썬 객체 그대로 투입
                record.profit_rate = profit_rate
    
    def register_manual_stock(self, code: str, name: str) -> bool:
        """수동 감시 종목을 DB에 등록합니다."""
        # 💡 ORM 단에서 Date 컬럼과 매핑될 수 있도록 date() 객체로 넘기는 것이 가장 안전합니다.
        today_date = datetime.now().date()
        target_code = str(code).zfill(6)

        try:
            with self.get_session() as session:
                # 💡 [변경] rec_date, stock_code 매핑
                record = session.query(RecommendationHistory).filter_by(
                    rec_date=today_date,
                    stock_code=target_code
                ).first()

                if record:
                    record.status = 'WATCHING'
                    record.trade_type = 'SCALPING' # 💡 type -> trade_type
                else:
                    new_record = RecommendationHistory(
                        rec_date=today_date,     # 💡 date -> rec_date
                        stock_code=target_code,  # 💡 code -> stock_code
                        stock_name=name,         # 💡 name -> stock_name
                        buy_price=0,
                        trade_type='SCALPING',     # 💡 type -> trade_type
                        status='WATCHING',
                        position_tag='MIDDLE'
                    )
                    session.add(new_record)
                
            return True

        except Exception as e:
            log_error(f"수동 타겟 DB 등록 오류 (ORM): {e}")
            return False
    
    def get_latest_history_date(self) -> str:
        """가장 최근 AI 스캐너 추천 기록의 날짜를 반환합니다."""
        try:
            with self.get_session() as session:
                # 💡 [변경] RecommendationHistory.date -> RecommendationHistory.rec_date
                latest_date = session.query(func.max(RecommendationHistory.rec_date)).scalar()
                
                # DB가 비어있을 경우 None 처리, 날짜 객체일 경우 문자열로 변환하여 리턴
                if latest_date:
                    return latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date)
                return None
                
        except Exception as e:
            log_error(f"최근 추천 기록 날짜 조회 실패: {e}")
            return None
    
    def get_history_by_date(self, date: str) -> pd.DataFrame:
        """특정 일자의 추천 종목 기록을 가져옵니다."""
        try:
            with self.get_session() as session:
                # 💡 [변경] date -> rec_date
                query = session.query(RecommendationHistory).filter_by(rec_date=date)
                df = pd.read_sql(query.statement, session.bind)
                return df

        except Exception as e:
            log_error(f"추천 기록 조회 실패 (날짜: {date}): {e}")
            return pd.DataFrame()
    
    def save_macro_alert(self, alert_data):
        """💡 [핵심] 글로벌 위기 알림을 DB에 저장 (중복 방어 포함)"""
        query = text("""
            INSERT INTO macro_alerts (alert_time, category, source, title, link, severity_score)
            VALUES (:alert_time, :category, :source, :title, :link, :severity_score)
            ON CONFLICT (link) DO NOTHING
        """)
        try:
            with self.get_session() as session:
                session.execute(query, alert_data)
                session.commit()
                return True
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"❌ 위기 경보 저장 실패: {e}")
            return False

    def get_recent_risk_count(self, hours=12, min_severity=2):
        """💡 [핵심] 최근 N시간 동안 발생한 심각한 위기 건수를 반환"""
        threshold = datetime.now() - timedelta(hours=hours)
        query = text("""
            SELECT COUNT(*) FROM macro_alerts 
            WHERE alert_time >= :threshold AND severity_score >= :min_severity
        """)
        try:
            with self.get_session() as session:
                return session.execute(query, {'threshold': threshold, 'min_severity': min_severity}).scalar()
        except Exception:
            return 0
    
    def get_active_targets(self) -> list:
        """
        💡 [핵심] 당일 감시 대상(WATCHING) 및 기존 보유 종목(HOLDING) 리스트를 
        엔진 규격에 맞는 딕셔너리 리스트로 반환합니다.
        고유 PK인 `id`를 포함하여 다중 스캘핑 시 데이터 덮어쓰기를 방지합니다.
        """
        import pandas as pd
        from datetime import datetime
        from src.utils.constants import TRADING_RULES
        
        try:
            today = datetime.now().date()
            
            with self.get_session() as session:
                # 💡 [핵심 교정 2] 이미 매매가 끝났거나(COMPLETED) 버려진(EXPIRED) 종목은 
                # 아예 DB에서 가져오지 않도록 쿼리단에서 컷오프! (메모리 낭비 완벽 차단)
                query = f"""
                    SELECT 
                        id, rec_date as date, stock_code as code, stock_name as name, 
                        trade_type as type, status, strategy, position_tag, prob, nxt, 
                        buy_price, buy_qty, buy_time, sell_price, sell_time, profit_rate 
                    FROM recommendation_history 
                    WHERE (rec_date='{today}' AND status NOT IN ('COMPLETED', 'EXPIRED')) 
                       OR status='HOLDING'
                """
                df = pd.read_sql(query, session.bind)

            if df.empty:
                return []

            # 💡 [핵심 교정 2] 상태값(status) 우선순위 강제 지정 (알파벳 정렬 버그 차단)
            # 가장 중요한 상태(HOLDING)부터 먼저 오도록 랭킹을 매깁니다.
            status_priority = {
                'HOLDING': 1, 
                'SELL_ORDERED': 2, 
                'BUY_ORDERED': 3, 
                'WATCHING': 4, 
                'COMPLETED': 5
            }
            df['priority'] = df['status'].map(status_priority).fillna(99)
            
            # 우선순위가 높은 순(오름차순), 그리고 id가 최신인 순(내림차순)으로 정렬 후 중복 제거
            df = df.sort_values(by=['priority', 'id'], ascending=[True, False])
            df = df.drop_duplicates(subset=['code'], keep='first')
            
            # 엔진에 넘기기 전에 임시 컬럼 삭제
            df = df.drop(columns=['priority'])
            
            targets = df.to_dict('records')

            # 기본값 보정 (스나이퍼 엔진의 부담을 DB 매니저가 덜어줍니다)
            default_prob = getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.8)
            
            for t in targets:
                t['prob'] = t.get('prob', default_prob)
                t['buy_qty'] = t.get('buy_qty', 0)
                t['strategy'] = t.get('strategy', 'KOSPI_ML')

            return targets
            
        except Exception as e:
            from src.utils.logger import log_error
            print(f"감시 대상 로드 에러: {e}")
            log_error(f"감시 대상 로드 에러: {e}")
            return []

    # --------------------------------------------------------
    # 3. 텔레그램 유저 관리
    # --------------------------------------------------------
    
    def get_telegram_chat_ids(self) -> list:
        with self.get_session() as session:
            users = session.query(User.chat_id).all()
            return [user.chat_id for user in users]
        
    def check_special_auth(self, chat_id: int) -> bool:
        with self.get_session() as session:
            user = session.query(User).filter_by(chat_id=chat_id).first()
            return bool(user and user.auth_group in ['A', 'V'])

    def add_new_user(self, chat_id: int):
        with self.get_session() as session:
            exists = session.query(User).filter_by(chat_id=chat_id).first()
            if not exists:
                new_user = User(chat_id=chat_id)
                session.add(new_user)
    
    def get_user_level(self, chat_id):
        """
        💡 [핵심] 특정 사용자의 등급(Admin/VIP/User)을 조회합니다.
        - 'A': 관리자 (Admin)
        - 'V': VIP 후원자 (VIP)
        - 'U': 일반 사용자 (User) - 기본값
        """
        chat_id_str = str(chat_id)
        
        try:
            from src.database.models import User # 💡 순환 참조 방지를 위한 지역 임포트
            
            with self.get_session() as session:
                # 1. DB에서 해당 chat_id를 가진 사용자 검색
                user = session.query(User).filter_by(chat_id=chat_id_str).first()
                
                # 2. 사용자가 존재하면 해당 레벨 반환, 없으면 기본값 'U' 반환
                if user and user.auth_group:
                    return user.auth_group
                
                # 💡 사용자가 없거나 레벨이 비어있다면 일반 유저('U')로 간주
                return 'U'
                
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"❌ 사용자 레벨 조회 중 에러 ({chat_id_str}): {e}")
            return 'U' # 에러 발생 시 보안을 위해 가장 낮은 등급 반환
    
    def upgrade_user_level(self, chat_id: int, level: str = 'V') -> bool:
        """
        사용자의 등급을 업데이트합니다. (기본값: 'V')
        """
        # 💡 [아키텍처 포인트] 파일 최상단에 User 모델이 임포트되어 있지 않다면
        # 순환 참조 방지를 위해 함수 내부에서 임포트합니다.
        from src.database.models import User 

        try:
            # 💡 [핵심 교정] sqlite3 원시 쿼리 대신 SQLAlchemy 세션 사용
            with self.get_session() as session:
                # 1. 대상 유저 조회 (chat_id를 문자열로 캐스팅하여 안전하게 비교)
                user = session.query(User).filter_by(chat_id=str(chat_id)).first()
                
                if user:
                    # 2. 유저가 존재하면 등급 업데이트 (숫자 1 대신 'VIP' 같은 문자열 사용)
                    user.auth_group = level
                    # session.commit()은 get_session()의 Context Manager(with문)가 
                    # 정상 종료될 때 자동으로 수행되지만, 명시적으로 적어주어도 좋습니다.
                    session.commit()
                    print(f"✅ [DBManager] 유저({chat_id}) 등급이 '{level}'(으)로 승격되었습니다.")
                    return True
                else:
                    print(f"⚠️ [DBManager] 승격할 유저({chat_id})를 DB에서 찾을 수 없습니다.")
                    return False
                    
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"유저 등급 업데이트 DB 에러: {e}")
            return False