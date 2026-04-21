"""Legacy dashboard raw 테이블 제거 관리 스크립트.

PostgreSQL에서 튜닝 모니터링 아키텍처 전환 후 더 이상 사용하지 않는
raw payload 대량 저장 테이블을 drop/archive 합니다.

주의: 제거 전 필수 조건
- parquet backfill 전기간 완료
- DuckDB 집계/리포트 shadow diff 합격
- drop 대상 테이블 목록 + row_count 증적 문서화
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import DictCursor

from src.utils.constants import POSTGRES_URL

logger = logging.getLogger(__name__)

# 제거 대상 테이블 (기본)
LEGACY_TABLES = [
    "dashboard_pipeline_events",
    "dashboard_monitor_snapshots",
    # 필요시 추가: dashboard_* raw 적재 테이블
]

# 보존 테이블 (제거 금지)
PROTECTED_TABLES = [
    "tuning_dataset_runs",
    "tuning_dataset_quality",
]


def get_db_connection():
    """PostgreSQL 연결 반환."""
    return psycopg2.connect(POSTGRES_URL)


def table_exists(conn, table_name: str) -> bool:
    """테이블 존재 여부 확인."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
            (table_name,),
        )
        return cur.fetchone()[0]


def get_table_row_count(conn, table_name: str) -> Optional[int]:
    """테이블의 현재 행 수 조회."""
    if not table_exists(conn, table_name):
        return None
    with conn.cursor() as cur:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cur.fetchone()[0]
        except Exception as e:
            logger.warning("행 수 조회 실패 %s: %s", table_name, e)
            return None


def list_legacy_tables(conn) -> List[Dict[str, Any]]:
    """제거 대상 테이블 목록과 행 수를 반환."""
    results = []
    for table in LEGACY_TABLES:
        if table_exists(conn, table):
            row_count = get_table_row_count(conn, table)
            results.append(
                {
                    "table": table,
                    "exists": True,
                    "row_count": row_count,
                }
            )
        else:
            results.append(
                {
                    "table": table,
                    "exists": False,
                    "row_count": None,
                }
            )
    return results


def drop_table(conn, table_name: str) -> bool:
    """단일 테이블 삭제."""
    if not table_exists(conn, table_name):
        logger.info("테이블 %s 존재하지 않음, 삭제 건너뜀.", table_name)
        return True
    with conn.cursor() as cur:
        try:
            cur.execute(f"DROP TABLE {table_name} CASCADE")
            logger.info("테이블 %s 삭제 완료.", table_name)
            return True
        except Exception as e:
            logger.error("테이블 %s 삭제 실패: %s", table_name, e)
            return False


def dry_run_report(conn):
    """Dry-run 모드로 대상 테이블 현황 보고."""
    print("=== Legacy Dashboard Tables Dry-run ===")
    print(f"대상 테이블: {', '.join(LEGACY_TABLES)}")
    print(f"보호 테이블: {', '.join(PROTECTED_TABLES)}")
    print()
    tables = list_legacy_tables(conn)
    for tbl in tables:
        if tbl["exists"]:
            print(f"  {tbl['table']}: 존재, 행 수 = {tbl['row_count']}")
        else:
            print(f"  {tbl['table']}: 존재하지 않음")
    print()
    # 제거 예상 행 수 합계
    total_rows = sum(t["row_count"] or 0 for t in tables if t["exists"])
    print(f"총 제거 행 수: {total_rows}")
    print("⚠️  실제 삭제는 --execute 옵션 필요")
    return tables


def execute_drop(conn, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
    """실제 테이블 삭제 실행."""
    results = []
    total_dropped = 0
    for tbl in tables:
        if not tbl["exists"]:
            results.append(
                {"table": tbl["table"], "dropped": False, "reason": "not exist"}
            )
            continue
        success = drop_table(conn, tbl["table"])
        if success:
            total_dropped += 1
            results.append(
                {"table": tbl["table"], "dropped": True, "rows": tbl["row_count"]}
            )
        else:
            results.append(
                {"table": tbl["table"], "dropped": False, "reason": "drop failed"}
            )
    return {
        "total_tables": len(tables),
        "dropped_tables": total_dropped,
        "details": results,
    }


def log_execution_summary(
    action: str, results: Dict[str, Any], log_file: Optional[Path] = None
):
    """실행 요약을 로그 파일에 기록."""
    summary_lines = [
        f"# Legacy Dashboard Tables Decommission {action}",
        f"실행 시각: {datetime.now().isoformat()}",
        f"대상 테이블 수: {results['total_tables']}",
        f"삭제된 테이블 수: {results.get('dropped_tables', 'N/A')}",
        "상세:",
    ]
    for detail in results.get("details", []):
        summary_lines.append(f"  - {detail['table']}: {detail}")
    summary = "\n".join(summary_lines)
    print(summary)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(summary + "\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Legacy dashboard raw 테이블 제거 관리"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="삭제 대상 테이블 목록과 행 수만 출력 (실제 삭제 안 함)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제 테이블 삭제 실행 (주의: 데이터 손실)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="--execute 시 확인 프롬프트를 생략",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/legacy_table_decommission.log"),
        help="실행 이력 로그 파일 경로",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="상세 로그 출력"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if not args.dry_run and not args.execute:
        parser.error("--dry-run 또는 --execute 옵션 중 하나를 지정해야 합니다.")

    conn = None
    try:
        conn = get_db_connection()
        if args.dry_run:
            tables = dry_run_report(conn)
            log_execution_summary("dry-run", {"total_tables": len(tables)}, args.log_file)
        elif args.execute:
            # 확인
            if not args.yes:
                confirm = input("정말 legacy 테이블을 삭제하시겠습니까? (yes/no): ")
                if confirm.lower() != "yes":
                    print("취소됨.")
                    sys.exit(1)
            tables = list_legacy_tables(conn)
            results = execute_drop(conn, tables)
            conn.commit()
            log_execution_summary("execute", results, args.log_file)
            print("삭제 완료.")
    except Exception as e:
        logger.error("작업 중 오류: %s", e)
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
