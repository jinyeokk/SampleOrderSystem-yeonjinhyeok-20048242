from app import AppContext
from view.release_view import ReleaseView


class ReleaseController:

    def __init__(self, ctx: AppContext, view: ReleaseView) -> None:
        self._ctx  = ctx
        self._view = view

    def run(self) -> None:
        while True:
            orders = self._ctx.release_service.get_pending_list()
            if not orders:
                self._view.info("출고 가능한 주문이 없습니다.")
                return

            sample_map = {
                o.sample_id: self._ctx.sample_service.get(o.sample_id)
                for o in orders
            }
            self._view.show_pending_list(orders, sample_map)
            choice = self._view.get_selection()

            if choice == "0":
                return

            try:
                idx = int(choice) - 1
                if not (0 <= idx < len(orders)):
                    raise ValueError
            except ValueError:
                self._view.error("유효하지 않은 번호입니다.")
                continue

            order    = orders[idx]
            sample   = sample_map[order.sample_id]
            released = self._ctx.release_service.release_one(order.order_id)
            self._view.show_release_result(released, sample)
