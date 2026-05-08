import math

from app import AppContext
from model.order import Order, OrderStatus
from model.sample import Sample
from view.approval_view import ApprovalView


class ApprovalController:

    def __init__(self, ctx: AppContext, view: ApprovalView) -> None:
        self._ctx  = ctx
        self._view = view

    def run(self) -> None:
        while True:
            orders = self._ctx.order_service.get_all(OrderStatus.RESERVED)
            if not orders:
                self._view.info("승인 대기 중인 주문이 없습니다.")
                return

            sample_map = {
                o.sample_id: self._ctx.sample_service.get(o.sample_id).name
                for o in orders
            }
            self._view.show_reserved_list(orders, sample_map)

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

            order  = orders[idx]
            sample = self._ctx.sample_service.get(order.sample_id)
            self._handle_action(order, sample)

    def _handle_action(self, order: Order, sample: Sample) -> None:
        shortage     = max(0, order.quantity - sample.stock)
        required_qty = math.ceil(shortage / (sample.yield_rate * 0.9)) if shortage > 0 else 0
        est_min      = int(required_qty * sample.avg_production_time)

        action = self._view.show_stock_check(
            order, sample, shortage, required_qty, est_min
        )

        if action == "1":
            stock_before = sample.stock
            approved = self._ctx.order_service.approve(order.order_id)
            if approved.status == OrderStatus.CONFIRMED:
                self._view.show_approve_confirmed(order, stock_before)
            else:
                self._view.show_approve_producing(
                    order, shortage, required_qty, sample.yield_rate
                )
        elif action == "2":
            self._ctx.order_service.reject(order.order_id)
            self._view.show_reject_result(order)
