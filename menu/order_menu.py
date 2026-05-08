from app import AppContext
from service.order_service import OrderNotFoundError
from service.sample_service import SampleNotFoundError
from utils.display import TABLE_DIVIDER, print_section, prompt
from utils.validator import validate_max_length, validate_non_empty, validate_positive_int


def run(ctx: AppContext) -> None:
    print_section("시료 주문")
    try:
        sample_id   = _input_sample_id(ctx)
        customer    = _input_customer_name()
        quantity    = _input_quantity()
    except (ValueError, SampleNotFoundError) as e:
        print(f"[오류] {e}")
        return

    sample = ctx.sample_service.get(sample_id)
    _print_confirm(sample_id, sample.name, customer, quantity)

    if not _select_action():
        print("[안내] 주문이 취소되었습니다.")
        return

    order = ctx.order_service.place_order(customer, sample_id, quantity)

    print("\n[완료] 예약 접수 완료.")
    print(TABLE_DIVIDER)
    print(f"  주문 번호 : {order.order_id}")
    print(f"  현재 상태 : {order.status.value}")
    print(TABLE_DIVIDER)
    print("[안내] 재고 확인은 [3] 승인 메뉴에서 직접 진행하세요.")


# ── 입력 헬퍼 ─────────────────────────────────────────────

def _input_sample_id(ctx: AppContext) -> str:
    val = prompt("시료 ID  ")
    validate_non_empty(val, "시료 ID")
    ctx.sample_service.get(val)   # 존재 확인 — 없으면 SampleNotFoundError
    return val


def _input_customer_name() -> str:
    val = prompt("고객명   ")
    validate_non_empty(val, "고객명")
    validate_max_length(val, 50, "고객명")
    return val


def _input_quantity() -> int:
    return validate_positive_int(prompt("주문 수량"), "주문 수량")


# ── 확인 화면 ─────────────────────────────────────────────

def _print_confirm(
    sample_id: str, sample_name: str, customer: str, quantity: int
) -> None:
    print(TABLE_DIVIDER)
    print("  입력 내용 확인")
    print(TABLE_DIVIDER)
    print(f"  시료      : {sample_name} ({sample_id})")
    print(f"  고객명    : {customer}")
    print(f"  주문 수량 : {quantity} ea")
    print(TABLE_DIVIDER)


def _select_action() -> bool:
    print("  Y. 예약 접수")
    print("  N. 취소")
    return input("선택 >> ").strip().upper() == "Y"
