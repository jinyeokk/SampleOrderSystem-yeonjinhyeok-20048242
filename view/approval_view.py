from model.order import Order, OrderStatus
from model.sample import Sample
from utils.display import TABLE_DIVIDER, ljust_display, rjust_display
from view.base_view import BaseView

_YELLOW = "\033[33m"
_RESET  = "\033[0m"


class ApprovalView(BaseView):

    def show_reserved_list(
        self, orders: list[Order], sample_map: dict[str, Sample]
    ) -> None:
        print(TABLE_DIVIDER)
        print(f"  승인 대기 중인 예약 목록 (총 {len(orders)}건) (RESERVED)")
        print(TABLE_DIVIDER)
        print(
            f" {'NO':>3}  {'주문 번호':<20}"
            f"{ljust_display('고객명', 16)}"
            f"{ljust_display('시료명', 14)}"
            f"{'수량':>6}"
        )
        print(TABLE_DIVIDER)
        for i, o in enumerate(orders, 1):
            sample_name = sample_map.get(o.sample_id, o.sample_id)
            print(
                f" {i:>3}  {o.order_id:<20}"
                f"{ljust_display(o.customer_name, 16)}"
                f"{ljust_display(sample_name, 14)}"
                f"{o.quantity:>4} ea"
            )
        print(TABLE_DIVIDER)

    def get_selection(self) -> str:
        return self.get_input("승인할 번호 (0: 메인 메뉴)")

    def show_stock_check(
        self, order: Order, sample: Sample, shortage: int,
        required_qty: int, est_min: int
    ) -> str:
        print(TABLE_DIVIDER)
        print("  재고 확인 중")
        print(TABLE_DIVIDER)
        print(f"  주문 번호 : {order.order_id}")
        print(f"  고객명    : {order.customer_name}")
        print(f"  시료      : {sample.name} ({sample.sample_id})")
        print(f"  주문 수량 : {order.quantity} ea")
        print(f"  현재 재고 : {sample.stock} ea")

        if shortage > 0:
            print(f"  부족분    : {shortage} ea  ← 이 수량만 생산")
            print(TABLE_DIVIDER)
            warn = (
                f"⚠ 재고 부족. 부족분 {shortage}ea 승인하시겠습니까?"
                f" (실 생산량 {required_qty}ea / {est_min:,}min)"
            )
            print(f"{_YELLOW}{warn}{_RESET}")

        print(TABLE_DIVIDER)
        print("  1. 승인")
        print("  2. 주문거절")
        print("  0. 취소")
        return self.get_input("선택")

    def show_approve_confirmed(
        self, order: Order, stock_before: int
    ) -> None:
        print(f"\n[완료] 주문 승인 완료.")
        print(TABLE_DIVIDER)
        print(f"  주문 번호 : {order.order_id}")
        print(f"  변경 상태 : RESERVED → CONFIRMED")
        print(f"  재고 변동 : {stock_before} ea → {stock_before - order.quantity} ea")
        print(TABLE_DIVIDER)

    def show_approve_producing(
        self, order: Order, shortage: int, required_qty: int, yield_rate: float
    ) -> None:
        print(f"\n[완료] 주문 승인 완료.")
        print(TABLE_DIVIDER)
        print(f"  주문 번호 : {order.order_id}")
        print(f"  변경 상태 : RESERVED → PRODUCING")
        print(f"  생산 등록 : {required_qty} ea  (ceil({shortage} / {yield_rate}))")
        print(TABLE_DIVIDER)

    def show_reject_result(self, order: Order) -> None:
        print(f"\n[완료] 주문 거절 완료.")
        print(TABLE_DIVIDER)
        print(f"  주문 번호 : {order.order_id}")
        print(f"  변경 상태 : RESERVED → REJECTED")
        print(TABLE_DIVIDER)
