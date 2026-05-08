from app import AppContext
from model.order import Order
from model.sample import Sample
from utils.display import TABLE_DIVIDER, ljust_display, rjust_display


def run(ctx: AppContext) -> None:
    while True:
        orders = ctx.release_service.get_pending_list()
        if not orders:
            print("[안내] 출고 가능한 주문이 없습니다.")
            return

        _print_list(orders, ctx)
        choice = input("출고할 번호 (0: 메인 메뉴) >> ").strip()

        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(orders)):
                raise ValueError
        except ValueError:
            print("[오류] 유효하지 않은 번호입니다.")
            continue

        order  = orders[idx]
        sample = ctx.sample_service.get(order.sample_id)
        released = ctx.release_service.release_one(order.order_id)
        _print_result(released, sample)


# ── 목록 ──────────────────────────────────────────────────
# 컬럼: 공백(1) + NO(4) + gap(2) + 주문번호(18) + 고객명(16) + 시료명(14) + 수량(5) = 60

def _print_list(orders: list[Order], ctx: AppContext) -> None:
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
        sample_name = ctx.sample_service.get(o.sample_id).name
        print(
            f" {i:>4}  "
            f"{o.order_id:<18}"
            f"{ljust_display(o.customer_name, 16)}"
            f"{ljust_display(sample_name, 14)}"
            f"{f'{o.quantity} ea':>5}"
        )
    print(TABLE_DIVIDER)


# ── 완료 화면 ─────────────────────────────────────────────

def _print_result(order: Order, sample: Sample) -> None:
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
