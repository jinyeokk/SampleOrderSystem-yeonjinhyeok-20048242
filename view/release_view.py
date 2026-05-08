from model.order import Order
from model.sample import Sample
from utils.display import TABLE_DIVIDER, ljust_display, rjust_display
from view.base_view import BaseView


class ReleaseView(BaseView):

    def show_pending_list(
        self, orders: list[Order], sample_map: dict[str, Sample]
    ) -> None:
        print(TABLE_DIVIDER)
        print(f"  출고 가능 주문 (총 {len(orders)}건) (CONFIRMED)")
        print(TABLE_DIVIDER)
        print(
            f" {rjust_display('NO', 4)}  "
            f"{ljust_display('주문 번호', 18)}"
            f"{ljust_display('고객명', 16)}"
            f"{ljust_display('시료명', 14)}"
            f"{rjust_display('수량', 5)}"
        )
        print(TABLE_DIVIDER)
        for i, o in enumerate(orders, 1):
            sample = sample_map.get(o.sample_id)
            sample_name = sample.name if sample else o.sample_id
            print(
                f" {i:>4}  "
                f"{o.order_id:<18}"
                f"{ljust_display(o.customer_name, 16)}"
                f"{ljust_display(sample_name, 14)}"
                f"{f'{o.quantity} ea':>5}"
            )
        print(TABLE_DIVIDER)

    def get_selection(self) -> str:
        return self.get_input("출고할 번호 (0: 메인 메뉴)")

    def show_release_result(self, order: Order, sample: Sample) -> None:
        released_at = order.released_at.strftime("%Y-%m-%d %H:%M:%S")
        print(TABLE_DIVIDER)
        print("  출고 처리 완료.")
        print(TABLE_DIVIDER)
        print(f"  주문 번호 : {order.order_id}")
        print(f"  고객명    : {order.customer_name}")
        print(f"  시료      : {sample.name} ({sample.sample_id})")
        print(f"  출고 수량 : {order.quantity} ea")
        print(f"  변경 상태 : CONFIRMED → RELEASE")
        print(f"  출고 일시 : {released_at}")
        print(TABLE_DIVIDER)
