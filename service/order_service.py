import uuid
from datetime import datetime
from typing import Optional

from model.order import Order, OrderStatus
from model.production import ProductionQueue
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from service.sample_service import SampleService, SampleNotFoundError


class OrderNotFoundError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        production_repo: ProductionRepository,
        sample_service: SampleService,
    ) -> None:
        self._order_repo = order_repo
        self._production_repo = production_repo
        self._sample_service = sample_service

    def place_order(self, customer_name: str, sample_id: str, quantity: int) -> Order:
        self._sample_service.get(sample_id)
        order = Order(
            order_id=self._generate_order_id(),
            customer_name=customer_name,
            sample_id=sample_id,
            quantity=quantity,
        )
        self._order_repo.save(order)
        self._order_repo.record_history(order.order_id, "주문 접수 (RESERVED)")
        return order

    def get(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    def get_all(self, status: Optional[OrderStatus] = None) -> list[Order]:
        if status is not None:
            return self._order_repo.find_by_status(status)
        return self._order_repo.find_all()

    def approve(self, order_id: str) -> Order:
        order = self.get(order_id)
        if order.status != OrderStatus.RESERVED:
            raise InvalidStatusTransitionError(
                f"승인 가능한 상태가 아닙니다. (현재: {order.status.value})"
            )
        sample = self._sample_service.get(order.sample_id)

        if sample.stock >= order.quantity:
            self._sample_service.update_stock(order.sample_id, -order.quantity)
            order.status = OrderStatus.CONFIRMED
            self._order_repo.record_history(order_id, "RESERVED → CONFIRMED")
        else:
            shortage = order.quantity - sample.stock
            required_qty = sample.required_production(shortage)
            queue = ProductionQueue(
                queue_id=uuid.uuid4().hex[:8],
                order_id=order_id,
                sample_id=order.sample_id,
                required_qty=required_qty,
            )
            self._production_repo.save(queue)
            order.status = OrderStatus.PRODUCING
            self._order_repo.record_history(order_id, "RESERVED → PRODUCING")

        order.updated_at = datetime.now()
        return order

    def reject(self, order_id: str, reason: str = "") -> Order:
        order = self.get(order_id)
        if order.status != OrderStatus.RESERVED:
            raise InvalidStatusTransitionError(
                f"거절 가능한 상태가 아닙니다. (현재: {order.status.value})"
            )
        order.status = OrderStatus.REJECTED
        order.reject_reason = reason
        order.updated_at = datetime.now()
        self._order_repo.record_history(order_id, "RESERVED → REJECTED")
        return order

    def _generate_order_id(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        count = sum(
            1 for o in self._order_repo.find_all()
            if o.order_id.startswith(f"ORD-{today}-")
        )
        return f"ORD-{today}-{count + 1:03d}"
