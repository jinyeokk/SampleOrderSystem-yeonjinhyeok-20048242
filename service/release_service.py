from datetime import datetime

from model.order import Order, OrderStatus
from repository.order_repo import OrderRepository
from service.order_service import OrderService, InvalidStatusTransitionError


class ReleaseService:
    def __init__(self, order_service: OrderService, order_repo: OrderRepository) -> None:
        self._order_service = order_service
        self._order_repo = order_repo

    def get_pending_list(self) -> list[Order]:
        return sorted(
            self._order_repo.find_by_status(OrderStatus.CONFIRMED),
            key=lambda o: o.updated_at,
        )

    def release_one(self, order_id: str) -> Order:
        order = self._order_service.get(order_id)
        if order.status != OrderStatus.CONFIRMED:
            raise InvalidStatusTransitionError(
                f"출고 가능한 상태가 아닙니다. (현재: {order.status.value})"
            )
        order.status = OrderStatus.RELEASE
        order.released_at = datetime.now()
        order.updated_at = datetime.now()
        self._order_repo.record_history(order_id, "CONFIRMED → RELEASE")
        self._order_repo.save(order)
        return order

    def release_bulk(self, order_ids: list[str]) -> list[Order]:
        return [self.release_one(oid) for oid in order_ids]
