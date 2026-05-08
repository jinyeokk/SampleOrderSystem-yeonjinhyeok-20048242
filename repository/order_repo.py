from datetime import datetime
from typing import Optional

from model.order import Order, OrderStatus


class OrderRepository:
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}
        self._history: list[dict] = []

    def save(self, order: Order) -> None:
        self._store[order.order_id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._store.get(order_id)

    def find_all(self) -> list[Order]:
        return sorted(self._store.values(), key=lambda o: o.created_at, reverse=True)

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self.find_all() if o.status == status]

    def count_by_status(self) -> dict[OrderStatus, int]:
        counts = {s: 0 for s in OrderStatus}
        for order in self._store.values():
            counts[order.status] += 1
        return counts

    def count_reserved_by_sample(self, sample_id: str) -> int:
        return sum(
            1 for o in self._store.values()
            if o.sample_id == sample_id and o.status == OrderStatus.RESERVED
        )

    def record_history(self, order_id: str, description: str) -> None:
        self._history.append({
            "changed_at": datetime.now(),
            "order_id": order_id,
            "description": description,
        })

    def get_recent_history(self, limit: int = 10) -> list[dict]:
        return list(reversed(self._history[-limit:]))
