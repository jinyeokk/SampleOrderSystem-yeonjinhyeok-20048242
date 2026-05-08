from app import AppContext
from model.order import Order, OrderStatus
from model.sample import Sample
from utils.display import TABLE_DIVIDER, ljust_display, print_section

_YELLOW = "\033[33m"
_RESET  = "\033[0m"


def run(ctx: AppContext) -> None:
    while True:
        orders = ctx.order_service.get_all(OrderStatus.RESERVED)
        if not orders:
            print("[안내] 승인 대기 중인 주문이 없습니다.")
            return

        _print_list(orders, ctx)
        choice = input("승인할 번호 (0: 메인 메뉴) >> ").strip()

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
        action = _show_stock_check(order, sample)

        if action == "1":
            _process_approve(ctx, order, sample)
        elif action == "2":
            _process_reject(ctx, order)


# ── 목록 ──────────────────────────────────────────────────
# 컬럼: NO(4) + 주문번호(20) + 고객명(16) + 시료명(14) + 수량(6) = 60

def _print_list(orders: list[Order], ctx: AppContext) -> None:
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
        sample_name = ctx.sample_service.get(o.sample_id).name
        print(
            f" {i:>3}  {o.order_id:<20}"
            f"{ljust_display(o.customer_name, 16)}"
            f"{ljust_display(sample_name, 14)}"
            f"{o.quantity:>4} ea"
        )
    print(TABLE_DIVIDER)


# ── 재고 확인 + 액션 선택 ─────────────────────────────────

def _show_stock_check(order: Order, sample: Sample) -> str:
    shortage = order.quantity - sample.stock

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
        required_qty = sample.required_production(shortage)
        est_min      = int(required_qty * sample.avg_production_time)
        warn = (
            f"⚠ 재고 부족. 부족분 {shortage}ea 승인하시겠습니까?"
            f" (실 생산량 {required_qty}ea / {est_min:,}min)"
        )
        print(f"{_YELLOW}{warn}{_RESET}")

    print(TABLE_DIVIDER)
    print("  1. 승인")
    print("  2. 주문거절")
    print("  0. 취소")
    return input("선택 >> ").strip()


# ── 승인 처리 ─────────────────────────────────────────────

def _process_approve(ctx: AppContext, order: Order, sample: Sample) -> None:
    stock_before = sample.stock
    shortage     = order.quantity - stock_before
    approved     = ctx.order_service.approve(order.order_id)

    print("\n[완료] 주문 승인 완료.")
    print(TABLE_DIVIDER)
    print(f"  주문 번호 : {order.order_id}")

    if approved.status == OrderStatus.CONFIRMED:
        print(f"  변경 상태 : RESERVED → CONFIRMED")
        print(f"  재고 변동 : {stock_before} ea → {stock_before - order.quantity} ea")
    else:
        required_qty = sample.required_production(shortage)
        print(f"  변경 상태 : RESERVED → PRODUCING")
        print(f"  생산 등록 : {required_qty} ea  (ceil({shortage} / {sample.yield_rate}))")

    print(TABLE_DIVIDER)


# ── 거절 처리 ─────────────────────────────────────────────

def _process_reject(ctx: AppContext, order: Order) -> None:
    ctx.order_service.reject(order.order_id)

    print("\n[완료] 주문 거절 완료.")
    print(TABLE_DIVIDER)
    print(f"  주문 번호 : {order.order_id}")
    print(f"  변경 상태 : RESERVED → REJECTED")
    print(TABLE_DIVIDER)
