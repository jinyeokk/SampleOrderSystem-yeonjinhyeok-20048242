"""테스트용 in-memory SQLite 연결 생성 헬퍼."""
import sqlite3

from db.schema import initialize_schema


def make_test_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    initialize_schema(conn)
    return conn
