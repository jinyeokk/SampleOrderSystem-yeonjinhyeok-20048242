from datetime import datetime

from model.order import Order, OrderStatus
from model.production import ProductionQueue, QueueStatus
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from service.order_service import OrderService, InvalidStatusTransitionError
from service.sample_service import SampleService


class ProductionService:
    def __init__(
        self,
        order_service: OrderService,
        order_repo: OrderRepository,
        production_repo: ProductionRepository,
        sample_service: SampleService,
    ) -> None:
        self._order_service = order_service
        self._order_repo = order_repo
        self._production_repo = production_repo
        self._sample_service = sample_service

    def get_in_progress(self) -> list[tuple[Order, ProductionQueue]]:
        producing = self._order_repo.find_by_status(OrderStatus.PRODUCING)
        result = []
        for order in producing:
            queue = self._production_repo.find_by_order(order.order_id)
            if queue:
                result.append((order, queue))
        return result

    def get_waiting_queue(self) -> list[ProductionQueue]:
        return self._production_repo.find_by_status(QueueStatus.WAITING)

    def complete_production(self, order_id: str) -> Order:
        order = self._order_service.get(order_id)
        if order.status != OrderStatus.PRODUCING:
            raise InvalidStatusTransitionError(
                f"생산 중 상태가 아닙니다. (현재: {order.status.value})"
            )
        queue = self._production_repo.find_by_order(order_id)

        # 생산 수량 추가 후 주문 수량 차감
        stock_delta = queue.required_qty - order.quantity
        self._sample_service.update_stock(order.sample_id, stock_delta)

        queue.status = QueueStatus.DONE
        queue.produced_qty = queue.required_qty

        order.status = OrderStatus.CONFIRMED
        order.updated_at = datetime.now()
        self._order_repo.record_history(order_id, "PRODUCING → CONFIRMED")
        return order
