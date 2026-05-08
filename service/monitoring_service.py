from model.order import OrderStatus
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository

MONITORED_STATUSES = [
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASE,
]


class MonitoringService:
    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        production_repo: ProductionRepository,
    ) -> None:
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._production_repo = production_repo

    def get_dashboard(self) -> dict:
        all_counts = self._order_repo.count_by_status()
        order_counts = {s: all_counts[s] for s in MONITORED_STATUSES}

        stock_status = [
            {
                "sample": s,
                "producing_qty": self._production_repo.sum_active_qty_by_sample(s.sample_id),
                "waiting_orders": self._order_repo.count_reserved_by_sample(s.sample_id),
            }
            for s in self._sample_repo.find_all()
        ]

        return {
            "order_counts": order_counts,
            "stock_status": stock_status,
            "recent_history": self._order_repo.get_recent_history(10),
        }
