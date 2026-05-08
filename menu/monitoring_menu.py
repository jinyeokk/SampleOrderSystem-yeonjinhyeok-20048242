from datetime import datetime

from app import AppContext
from model.order import OrderStatus
from utils.display import (
    TABLE_DIVIDER,
    TABLE_WIDTH,
    center_display,
    display_width,
    input_menu,
    ljust_display,
    rjust_display,
)

_MONITORED_STATUSES = [
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASE,
]


def run(ctx: AppContext) -> None:
    while True:
        choice = input_menu("모니터링", [
            ("1", "주문량 확인"),
            ("2", "재고량 확인"),
            ("0", "메인 메뉴"),
        ])
        if choice == "0":
            break
        elif choice == "1":
            _show_order_counts(ctx)
            input("\nEnter를 눌러 계속...")
        elif choice == "2":
            _show_stock_status(ctx)
            input("\nEnter를 눌러 계속...")
        else:
            print("[오류] 유효하지 않은 선택입니다.")


# ── 주문량 확인 ───────────────────────────────────────────

def _show_order_counts(ctx: AppContext) -> None:
    counts = ctx.order_repo.count_by_status()
    now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    col    = TABLE_WIDTH // 4  # 15

    title   = "  주문량 확인"
    padding = TABLE_WIDTH - display_width(title) - len(now)

    labels = [s.value for s in _MONITORED_STATUSES]
    values = [f"{counts[s]}건" for s in _MONITORED_STATUSES]

    print(TABLE_DIVIDER)
    print(f"{title}{' ' * padding}{now}")
    print(TABLE_DIVIDER)
    print("".join(center_display(lbl, col) for lbl in labels))
    print("".join(center_display("─" * 10, col) for _ in labels))
    print("".join(center_display(v, col) for v in values))
    print(TABLE_DIVIDER)


# ── 재고량 확인 ───────────────────────────────────────────
# 컬럼: 시료ID(10) + 시료명(18) + 현재재고(10) + 예약수량(10) + 상태(6)

def _show_stock_status(ctx: AppContext) -> None:
    samples        = ctx.sample_service.get_all()
    reserved_orders = ctx.order_service.get_all(OrderStatus.RESERVED)

    reserved_qty: dict[str, int] = {}
    for o in reserved_orders:
        reserved_qty[o.sample_id] = reserved_qty.get(o.sample_id, 0) + o.quantity

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

    if not samples:
        print("[안내] 등록된 시료가 없습니다.")
    else:
        for s in samples:
            r_qty = reserved_qty.get(s.sample_id, 0)
            label = _stock_label(s.stock, r_qty)
            print(
                f" {s.sample_id:<10}"
                f"{ljust_display(s.name, 18)}"
                f"{f'{s.stock} ea':>10}"
                f"{f'{r_qty} ea':>10}"
                f"{label:>6}"
            )

    print(TABLE_DIVIDER)


def _stock_label(stock: int, reserved_qty: int) -> str:
    if stock == 0:
        return "고갈"
    if stock < reserved_qty:
        return "부족"
    return "여유"
