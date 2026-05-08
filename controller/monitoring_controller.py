from app import AppContext
from model.order import OrderStatus
from view.monitoring_view import MonitoringView


class MonitoringController:

    def __init__(self, ctx: AppContext, view: MonitoringView) -> None:
        self._ctx  = ctx
        self._view = view

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "0":
                break
            elif choice == "1":
                self._show_order_counts()
                self._view.wait()
            elif choice == "2":
                self._show_stock_status()
                self._view.wait()
            else:
                self._view.error("유효하지 않은 선택입니다.")

    def _show_order_counts(self) -> None:
        counts = self._ctx.order_repo.count_by_status()
        self._view.show_order_counts(counts)

    def _show_stock_status(self) -> None:
        samples         = self._ctx.sample_service.get_all()
        reserved_orders = self._ctx.order_service.get_all(OrderStatus.RESERVED)

        reserved_qty: dict[str, int] = {}
        for o in reserved_orders:
            reserved_qty[o.sample_id] = reserved_qty.get(o.sample_id, 0) + o.quantity

        labels = {s.sample_id: _stock_label(s.stock, reserved_qty.get(s.sample_id, 0))
                  for s in samples}

        self._view.show_stock_status(samples, reserved_qty, labels)


def _stock_label(stock: int, reserved_qty: int) -> str:
    if stock == 0:
        return "고갈"
    if stock < reserved_qty:
        return "부족"
    return "여유"
