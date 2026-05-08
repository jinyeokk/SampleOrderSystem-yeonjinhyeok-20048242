from datetime import datetime

from model.order import OrderStatus
from model.sample import Sample
from utils.display import TABLE_DIVIDER, TABLE_WIDTH, center_display, display_width, ljust_display, rjust_display
from view.base_view import BaseView

_MONITORED_STATUSES = [
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASE,
]


class MonitoringView(BaseView):

    def show_menu(self) -> str:
        return super().show_menu("모니터링", [
            ("1", "주문량 확인"),
            ("2", "재고량 확인"),
            ("0", "메인 메뉴"),
        ])

    def show_order_counts(self, counts: dict) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        col = TABLE_WIDTH // 4
        title = "  주문량 확인"
        pad   = TABLE_WIDTH - display_width(title) - len(now)

        labels = [s.value for s in _MONITORED_STATUSES]
        values = [f"{counts[s]}건" for s in _MONITORED_STATUSES]

        print(TABLE_DIVIDER)
        print(f"{title}{' ' * pad}{now}")
        print(TABLE_DIVIDER)
        print("".join(center_display(lbl, col) for lbl in labels))
        print("".join(center_display("─" * 10, col) for _ in labels))
        print("".join(center_display(v, col) for v in values))
        print(TABLE_DIVIDER)

    def show_stock_status(
        self,
        samples: list[Sample],
        reserved_qty: dict[str, int],
        stock_labels: dict[str, str],
    ) -> None:
        print(TABLE_DIVIDER)
        print("  재고량 확인")
        print(TABLE_DIVIDER)
        print(
            f" {ljust_display('시료 ID', 10)}"
            f"{ljust_display('시료명', 18)}"
            f"{rjust_display('현재 재고', 10)}"
            f"{rjust_display('예약 수량', 10)}"
            f"{rjust_display('상태', 6)}"
        )
        print(TABLE_DIVIDER)
        for s in samples:
            r_qty = reserved_qty.get(s.sample_id, 0)
            label = stock_labels[s.sample_id]
            print(
                f" {s.sample_id:<10}"
                f"{ljust_display(s.name, 18)}"
                f"{f'{s.stock} ea':>10}"
                f"{f'{r_qty} ea':>10}"
                f"{label:>6}"
            )
        print(TABLE_DIVIDER)
