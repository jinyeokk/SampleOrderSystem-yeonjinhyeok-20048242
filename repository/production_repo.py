import sqlite3
from datetime import datetime
from typing import Optional

from model.production import ProductionQueue, QueueStatus


class ProductionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, queue: ProductionQueue) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO production_queue VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                queue.queue_id, queue.order_id, queue.sample_id,
                queue.required_qty, queue.produced_qty,
                queue.status.value, queue.queued_at.isoformat(),
            ),
        )
        self._conn.commit()

    def find_by_order(self, order_id: str) -> Optional[ProductionQueue]:
        row = self._conn.execute(
            "SELECT * FROM production_queue WHERE order_id = ?", (order_id,)
        ).fetchone()
        return _to_queue(row) if row else None

    def find_by_status(self, status: QueueStatus) -> list[ProductionQueue]:
        rows = self._conn.execute(
            "SELECT * FROM production_queue WHERE status = ? ORDER BY queued_at ASC",
            (status.value,),
        ).fetchall()
        return [_to_queue(r) for r in rows]

    def sum_active_qty_by_sample(self, sample_id: str) -> int:
        row = self._conn.execute(
            """SELECT COALESCE(SUM(required_qty), 0) AS total
               FROM production_queue
               WHERE sample_id = ? AND status != 'DONE'""",
            (sample_id,),
        ).fetchone()
        return row["total"] if row else 0


def _to_queue(row) -> ProductionQueue:
    return ProductionQueue(
        queue_id=row["queue_id"],
        order_id=row["order_id"],
        sample_id=row["sample_id"],
        required_qty=row["required_qty"],
        produced_qty=row["produced_qty"],
        status=QueueStatus(row["status"]),
        queued_at=datetime.fromisoformat(row["queued_at"]),
    )
