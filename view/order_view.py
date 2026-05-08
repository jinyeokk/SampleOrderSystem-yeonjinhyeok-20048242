from model.order import Order
from model.sample import Sample
from utils.display import TABLE_DIVIDER
from view.base_view import BaseView


class OrderView(BaseView):

    def show_header(self) -> None:
        self.section("시료 주문")

    def get_sample_id(self) -> str:
        return self.get_input("시료 ID  ")

    def get_customer_name(self) -> str:
        return self.get_input("고객명   ")

    def get_quantity(self) -> str:
        return self.get_input("주문 수량")

    def show_order_confirm(
        self, sample: Sample, customer: str, quantity: int
    ) -> None:
        self.divider()
        print("  입력 내용 확인")
        self.divider()
        print(f"  시료      : {sample.name} ({sample.sample_id})")
        print(f"  고객명    : {customer}")
        print(f"  주문 수량 : {quantity} ea")
        self.divider()

    def show_action_prompt(self) -> str:
        print("  Y. 예약 접수")
        print("  N. 취소")
        return self.get_input("선택")

    def show_order_success(self, order: Order) -> None:
        print(f"\n[완료] 예약 접수 완료.")
        print(TABLE_DIVIDER)
        print(f"  주문 번호 : {order.order_id}")
        print(f"  현재 상태 : {order.status.value}")
        print(TABLE_DIVIDER)
        self.info("재고 확인은 [3] 승인 메뉴에서 직접 진행하세요.")
