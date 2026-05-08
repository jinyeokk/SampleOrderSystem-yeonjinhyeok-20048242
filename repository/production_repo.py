from typing import Optional

from model.production import ProductionQueue, QueueStatus


class ProductionRepository:
    def __init__(self) -> None:
        self._store: dict[str, ProductionQueue] = {}

    def save(self, queue: ProductionQueue) -> None:
        self._store[queue.queue_id] = queue

    def find_by_order(self, order_id: str) -> Optional[ProductionQueue]:
        return next((q for q in self._store.values() if q.order_id == order_id), None)

    def find_by_status(self, status: QueueStatus) -> list[ProductionQueue]:
        return sorted(
            (q for q in self._store.values() if q.status == status),
            key=lambda q: q.queued_at,
        )

    def sum_active_qty_by_sample(self, sample_id: str) -> int:
        return sum(
            q.required_qty for q in self._store.values()
            if q.sample_id == sample_id and q.status != QueueStatus.DONE
        )
