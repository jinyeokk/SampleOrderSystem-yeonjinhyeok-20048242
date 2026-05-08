"""Phase 6 테스트: 출고처리 (ReleaseService)."""
from app import AppContext
from model.order import OrderStatus
from service.order_service import InvalidStatusTransitionError, OrderNotFoundError
from tests.harness import TestHarness, assert_eq, assert_raises, assert_true


def _make_ctx() -> AppContext:
    return AppContext()


def _setup_confirmed(ctx: AppContext, sample_id: str, qty: int) -> str:
    """시료 등록 → 주문 → 승인(CONFIRMED) 후 order_id 반환."""
    ctx.sample_service.register(sample_id, "테스트시료", 30.0, 0.90)
    ctx.sample_service.update_stock(sample_id, 100)
    order = ctx.order_service.place_order("테스트고객", sample_id, qty)
    ctx.order_service.approve(order.order_id)
    return order.order_id


def run_tests() -> bool:
    h = TestHarness("Phase 6 — 출고처리")

    h.run("출고 후 RELEASE 전환",                  _test_release_status)
    h.run("출고 일시(released_at) 기록",            _test_released_at)
    h.run("출고 대기 목록: CONFIRMED 주문만",       _test_pending_list)
    h.run("출고 대기 목록: 승인일시 오름차순 정렬", _test_pending_list_order)
    h.run("CONFIRMED 아닌 주문 출고 → 오류",       _test_wrong_status)
    h.run("없는 주문 ID → OrderNotFoundError",     _test_not_found)
    h.run("출고 후 목록에서 제거",                 _test_removed_from_list)

    return h.report()


# ── 출고 처리 ─────────────────────────────────────────────

def _test_release_status() -> None:
    ctx = _make_ctx()
    order_id = _setup_confirmed(ctx, "A-001", 10)
    released = ctx.release_service.release_one(order_id)
    assert_eq(released.status, OrderStatus.RELEASE)


def _test_released_at() -> None:
    ctx = _make_ctx()
    order_id = _setup_confirmed(ctx, "A-001", 10)
    released = ctx.release_service.release_one(order_id)
    assert_true(released.released_at is not None, "released_at 기록되어야 함")


# ── 목록 조회 ─────────────────────────────────────────────

def _test_pending_list() -> None:
    ctx = _make_ctx()
    _setup_confirmed(ctx, "A-001", 10)
    _setup_confirmed(ctx, "A-002", 20)

    pending = ctx.release_service.get_pending_list()
    assert_eq(len(pending), 2)
    assert_true(all(o.status == OrderStatus.CONFIRMED for o in pending))


def _test_pending_list_order() -> None:
    import time
    ctx = _make_ctx()
    id1 = _setup_confirmed(ctx, "A-001", 10)
    time.sleep(0.01)
    id2 = _setup_confirmed(ctx, "A-002", 10)

    pending = ctx.release_service.get_pending_list()
    assert_eq(pending[0].order_id, id1, "오래된 승인 건이 먼저")
    assert_eq(pending[1].order_id, id2)


# ── 오류 케이스 ───────────────────────────────────────────

def _test_wrong_status() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    order = ctx.order_service.place_order("고객", "A-001", 5)  # RESERVED
    assert_raises(InvalidStatusTransitionError, ctx.release_service.release_one, order.order_id)


def _test_not_found() -> None:
    ctx = _make_ctx()
    assert_raises(OrderNotFoundError, ctx.release_service.release_one, "ORD-00000000-000")


def _test_removed_from_list() -> None:
    ctx = _make_ctx()
    order_id = _setup_confirmed(ctx, "A-001", 10)

    ctx.release_service.release_one(order_id)
    pending = ctx.release_service.get_pending_list()
    assert_eq(len(pending), 0, "출고 완료 후 목록에서 제거")


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
