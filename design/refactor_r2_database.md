# Refactor R2 : DB 연동 (SQLite)

## 1. 목적

현재 in-memory dict 기반의 Repository를 **SQLite** 영속성 계층으로 교체한다.  
Repository 인터페이스(메서드 시그니처)는 유지하여 Service 계층을 변경하지 않는다.

---

## 2. 현재 vs DB 구조

```
현재:  AppContext → Repository (dict) → 메모리 (앱 종료 시 데이터 소멸)
이후:  AppContext → Repository (SQLite) → data/semi.db (영속 저장)
```

---

## 3. 디렉토리 구조

```
semi/
├── data/
│   └── semi.db              # SQLite DB 파일 (자동 생성)
├── db/
│   ├── __init__.py
│   ├── connection.py        # DB 연결 관리 (싱글턴)
│   ├── schema.py            # 테이블 생성 DDL
│   └── migrations/
│       └── 001_initial.sql  # 초기 스키마
├── repository/
│   ├── sample_repo.py       # SQLite 구현으로 교체
│   ├── order_repo.py
│   └── production_repo.py
└── ...
```

---

## 4. 스키마 정의

```sql
-- samples
CREATE TABLE IF NOT EXISTS samples (
    sample_id            TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    avg_production_time  REAL NOT NULL,
    yield_rate           REAL NOT NULL,
    stock                INTEGER NOT NULL DEFAULT 0
);

-- orders
CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    sample_id       TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'RESERVED',
    reject_reason   TEXT DEFAULT '',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    released_at     TEXT,
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);

-- production_queue
CREATE TABLE IF NOT EXISTS production_queue (
    queue_id      TEXT PRIMARY KEY,
    order_id      TEXT NOT NULL,
    sample_id     TEXT NOT NULL,
    required_qty  INTEGER NOT NULL,
    produced_qty  INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'WAITING',
    queued_at     TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- order_history
CREATE TABLE IF NOT EXISTS order_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     TEXT NOT NULL,
    description  TEXT NOT NULL,
    changed_at   TEXT NOT NULL
);
```

---

## 5. DB 연결 관리

```python
# db/connection.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "semi.db"

class DBConnection:
    _instance: sqlite3.Connection | None = None

    @classmethod
    def get(cls) -> sqlite3.Connection:
        if cls._instance is None:
            DB_PATH.parent.mkdir(exist_ok=True)
            cls._instance = sqlite3.connect(DB_PATH, check_same_thread=False)
            cls._instance.row_factory = sqlite3.Row
            cls._instance.execute("PRAGMA foreign_keys = ON")
        return cls._instance

    @classmethod
    def close(cls) -> None:
        if cls._instance:
            cls._instance.close()
            cls._instance = None
```

---

## 6. Repository 구현 전환 예시

### SampleRepository (현재 → SQLite)

```python
# 현재 (in-memory)
class SampleRepository:
    def __init__(self):
        self._store: dict[str, Sample] = {}

    def save(self, sample: Sample) -> None:
        self._store[sample.sample_id] = sample

# SQLite 전환 후
class SampleRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def save(self, sample: Sample) -> None:
        self._conn.execute("""
            INSERT OR REPLACE INTO samples
            VALUES (?, ?, ?, ?, ?)
        """, (sample.sample_id, sample.name,
              sample.avg_production_time, sample.yield_rate, sample.stock))
        self._conn.commit()

    def find_by_id(self, sample_id: str) -> Sample | None:
        row = self._conn.execute(
            "SELECT * FROM samples WHERE sample_id = ?", (sample_id,)
        ).fetchone()
        return _row_to_sample(row) if row else None

    def update_stock(self, sample_id: str, delta: int) -> None:
        self._conn.execute(
            "UPDATE samples SET stock = stock + ? WHERE sample_id = ?",
            (delta, sample_id)
        )
        self._conn.commit()
```

---

## 7. CRUD 지원 범위

| 엔티티 | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Sample | ✅ 시료 등록 | ✅ 목록·단건 조회 | ✅ 재고 변경 | ❌ (범위 외) |
| Order | ✅ 주문 생성 | ✅ 전체·상태별·단건 | ✅ 상태 전이 | ❌ (범위 외) |
| ProductionQueue | ✅ 큐 등록 | ✅ 상태별 조회 | ✅ 상태·수량 변경 | ❌ (범위 외) |
| OrderHistory | ✅ 이력 기록 | ✅ 최근 N건 조회 | ❌ | ❌ |

---

## 8. AppContext 변경

```python
# app.py
from db.connection import DBConnection
from db.schema import initialize_schema

class AppContext:
    def __init__(self):
        conn = DBConnection.get()
        initialize_schema(conn)              # 테이블 없으면 생성

        self.sample_repo     = SampleRepository(conn)
        self.order_repo      = OrderRepository(conn)
        self.production_repo = ProductionRepository(conn)
        # ... 서비스는 동일
```

---

## 9. 구현 체크리스트

- [ ] `db/connection.py` — SQLite 싱글턴 연결
- [ ] `db/schema.py` — 테이블 초기화 함수
- [ ] `db/migrations/001_initial.sql` — 초기 스키마
- [ ] `repository/sample_repo.py` — SQLite 구현 교체
- [ ] `repository/order_repo.py` — SQLite 구현 교체
- [ ] `repository/production_repo.py` — SQLite 구현 교체
- [ ] `app.py` — DB 연결 주입
- [ ] 전체 테스트 60/60 통과 (Repository 인터페이스 동일 유지)
