from app import AppContext
from service.sample_service import SampleNotFoundError
from utils.validator import validate_max_length, validate_non_empty, validate_positive_int
from view.order_view import OrderView


class OrderController:

    def __init__(self, ctx: AppContext, view: OrderView) -> None:
        self._ctx  = ctx
        self._view = view

    def run(self) -> None:
        self._view.show_header()
        try:
            sample_id = self._read_sample_id()
            customer  = self._read_customer()
            quantity  = self._read_quantity()
        except (ValueError, SampleNotFoundError) as e:
            self._view.error(str(e))
            return

        sample = self._ctx.sample_service.get(sample_id)
        self._view.show_order_confirm(sample, customer, quantity)

        if self._view.show_action_prompt().upper() != "Y":
            self._view.info("주문이 취소되었습니다.")
            return

        order = self._ctx.order_service.place_order(customer, sample_id, quantity)
        self._view.show_order_success(order)

    # ── 입력 + 검증 ───────────────────────────────────────

    def _read_sample_id(self) -> str:
        val = self._view.get_sample_id()
        validate_non_empty(val, "시료 ID")
        self._ctx.sample_service.get(val)   # 존재 확인
        return val

    def _read_customer(self) -> str:
        val = self._view.get_customer_name()
        validate_non_empty(val, "고객명")
        validate_max_length(val, 50, "고객명")
        return val

    def _read_quantity(self) -> int:
        return validate_positive_int(self._view.get_quantity(), "주문 수량")
