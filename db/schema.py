import sqlite3


def initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS samples (
            sample_id            TEXT PRIMARY KEY,
            name                 TEXT NOT NULL,
            avg_production_time  REAL NOT NULL,
            yield_rate           REAL NOT NULL,
            stock                INTEGER NOT NULL DEFAULT 0
        );

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

        CREATE TABLE IF NOT EXISTS order_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id     TEXT NOT NULL,
            description  TEXT NOT NULL,
            changed_at   TEXT NOT NULL
        );
    """)
    conn.commit()
