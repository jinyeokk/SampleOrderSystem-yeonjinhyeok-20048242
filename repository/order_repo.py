import sqlite3
from datetime import datetime
from typing import Optional

from model.order import Order, OrderStatus


class OrderRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, order: Order) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                order.order_id, order.customer_name, order.sample_id,
                order.quantity, order.status.value, order.reject_reason,
                order.created_at.isoformat(), order.updated_at.isoformat(),
                order.released_at.isoformat() if order.released_at else None,
            ),
        )
        self._conn.commit()

    def find_by_id(self, order_id: str) -> Optional[Order]:
        row = self._conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        return _to_order(row) if row else None

    def find_all(self) -> list[Order]:
        rows = self._conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC"
        ).fetchall()
        return [_to_order(r) for r in rows]

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        rows = self._conn.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC",
            (status.value,),
        ).fetchall()
        return [_to_order(r) for r in rows]

    def count_by_status(self) -> dict[OrderStatus, int]:
        counts = {s: 0 for s in OrderStatus}
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status"
        ).fetchall()
        for row in rows:
            try:
                counts[OrderStatus(row["status"])] = row["cnt"]
            except ValueError:
                pass
        return counts

    def count_reserved_by_sample(self, sample_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS cnt FROM orders WHERE sample_id = ? AND status = 'RESERVED'",
            (sample_id,),
        ).fetchone()
        return row["cnt"] if row else 0

    def record_history(self, order_id: str, description: str) -> None:
        self._conn.execute(
            "INSERT INTO order_history (order_id, description, changed_at) VALUES (?, ?, ?)",
            (order_id, description, datetime.now().isoformat()),
        )
        self._conn.commit()

    def get_recent_history(self, limit: int = 10) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM order_history ORDER BY changed_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "changed_at": datetime.fromisoformat(r["changed_at"]),
                "order_id": r["order_id"],
                "description": r["description"],
            }
            for r in rows
        ]


def _to_order(row) -> Order:
    return Order(
        order_id=row["order_id"],
        customer_name=row["customer_name"],
        sample_id=row["sample_id"],
        quantity=row["quantity"],
        status=OrderStatus(row["status"]),
        reject_reason=row["reject_reason"] or "",
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        released_at=datetime.fromisoformat(row["released_at"]) if row["released_at"] else None,
    )
