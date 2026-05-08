from datetime import datetime

from model.order import Order
from model.production import ProductionQueue
from model.sample import Sample
from utils.display import TABLE_DIVIDER, TABLE_WIDTH, display_width, ljust_display, rjust_display
from view.base_view import BaseView


class ProductionView(BaseView):

    def show_dashboard(
        self,
        items: list[tuple[Order, ProductionQueue]],
        sample_map: dict[str, Sample],
    ) -> str:
        now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        running  = bool(items)
        status   = "■ RUNNING" if running else "□ STOP"
        title    = "  생산라인 현황"
        pad      = TABLE_WIDTH - display_width(title) - len(now)

        print(TABLE_DIVIDER)
        print(f"{title}{' ' * pad}{now}")
        print(TABLE_DIVIDER)
        print(f"  생산라인 상태 : {status}")
        print(TABLE_DIVIDER)

        if running:
            self._show_current(items[0], sample_map)
        else:
            print("  현재 처리 중 — 없음")
            print(TABLE_DIVIDER)

        self._show_waiting(items[1:], sample_map)
        print("  0. 메인 메뉴")
        return self.get_input("선택")

    def _show_current(
        self, item: tuple[Order, ProductionQueue], sample_map: dict[str, Sample]
    ) -> None:
        order, queue = item
        sample  = sample_map[order.sample_id]
        est_min = int(queue.required_qty * sample.avg_production_time)
        bar     = _progress_bar(queue.produced_qty, queue.required_qty)

        print("  현재 처리 중")
        print(TABLE_DIVIDER)
        print(f"  주문 번호   : {order.order_id}")
        print(f"  고객명      : {order.customer_name}")
        print(f"  시료        : {sample.name} ({sample.sample_id})")
        print(f"  주문 수량   : {order.quantity} ea")
        print(f"  실 생산량   : {queue.required_qty} ea")
        print(f"  총 생산시간 : {est_min:,} min")
        print(f"  진행률      : [{bar}]  {queue.produced_qty} / {queue.required_qty} ea")
        print(TABLE_DIVIDER)

    def _show_waiting(
        self, items: list[tuple[Order, ProductionQueue]], sample_map: dict[str, Sample]
    ) -> None:
        print(f"  대기 주문 (총 {len(items)}건) — FIFO")
        print(TABLE_DIVIDER)
        if not items:
            print("  [안내] 대기 중인 주문이 없습니다.")
            print(TABLE_DIVIDER)
            return

        print(
            f" {rjust_display('순번', 4)}  "
            f"{ljust_display('주문 번호', 18)}"
            f"{ljust_display('시료명', 14)}"
            f"{rjust_display('실생산량', 8)}"
            f"  등록일시"
        )
        print(TABLE_DIVIDER)
        for i, (order, queue) in enumerate(items, 1):
            sample_name = sample_map[order.sample_id].name
            dt_str      = queue.queued_at.strftime("%m-%d %H:%M")
            print(
                f" {i:>4}  "
                f"{order.order_id:<18}"
                f"{ljust_display(sample_name, 14)}"
                f"{f'{queue.required_qty} ea':>8}"
                f"  {dt_str}"
            )
        print(TABLE_DIVIDER)


def _progress_bar(produced: int, required: int, width: int = 20) -> str:
    filled = int(produced / required * width) if required > 0 else 0
    return "▓" * filled + "░" * (width - filled)
