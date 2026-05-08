"""Phase 4 테스트: 모니터링 (주문량 확인 / 재고량 확인)."""
from app import AppContext
from controller.monitoring_controller import _stock_label
from model.order import OrderStatus
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository
from service.order_service import OrderService
from service.sample_service import SampleService
from tests.harness import TestHarness, assert_eq, assert_true


def _make_ctx() -> AppContext:
    from tests.db_helper import make_test_conn
    return AppContext(make_test_conn())


def run_tests() -> bool:
    h = TestHarness("Phase 4 — 모니터링")

    h.run("재고 0 → 고갈",                          _test_stock_label_고갈)
    h.run("재고 > 0, 재고 < 예약 수량 → 부족",      _test_stock_label_부족)
    h.run("재고 >= 예약 수량 → 여유",               _test_stock_label_여유)
    h.run("예약 수량 0이면 재고 > 0 → 여유",        _test_stock_label_no_reserved)
    h.run("REJECTED 주문은 건수에서 제외",           _test_order_count_excludes_rejected)
    h.run("예약 수량은 RESERVED 상태 합계만",        _test_reserved_qty_reserved_only)
    h.run("시료별 예약 수량 집계",                   _test_reserved_qty_per_sample)

    return h.report()


# ── _stock_label ──────────────────────────────────────────

def _test_stock_label_고갈() -> None:
    assert_eq(_stock_label(0, 0),  "고갈")
    assert_eq(_stock_label(0, 10), "고갈")


def _test_stock_label_부족() -> None:
    assert_eq(_stock_label(5,  10), "부족")
    assert_eq(_stock_label(1, 100), "부족")


def _test_stock_label_여유() -> None:
    assert_eq(_stock_label(10, 10), "여유")
    assert_eq(_stock_label(20, 10), "여유")
    assert_eq(_stock_label(100, 0), "여유")


def _test_stock_label_no_reserved() -> None:
    assert_eq(_stock_label(5, 0), "여유")


# ── 주문 건수 집계 ────────────────────────────────────────

def _test_order_count_excludes_rejected() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)

    o1 = ctx.order_service.place_order("고객1", "A-001", 5)
    o2 = ctx.order_service.place_order("고객2", "A-001", 5)
    ctx.order_service.reject(o2.order_id)

    counts = ctx.order_repo.count_by_status()
    assert_eq(counts[OrderStatus.RESERVED], 1)
    assert_eq(counts[OrderStatus.REJECTED], 1)

    monitored_total = sum(
        counts[s] for s in [
            OrderStatus.RESERVED, OrderStatus.PRODUCING,
            OrderStatus.CONFIRMED, OrderStatus.RELEASE,
        ]
    )
    assert_eq(monitored_total, 1, "REJECTED 제외한 집계는 1건")


# ── 예약 수량 집계 ────────────────────────────────────────

def _test_reserved_qty_reserved_only() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)

    o1 = ctx.order_service.place_order("고객1", "A-001", 10)  # RESERVED
    o2 = ctx.order_service.place_order("고객2", "A-001", 20)  # RESERVED → CONFIRMED
    ctx.order_service.approve(o2.order_id)

    reserved_orders = ctx.order_service.get_all(OrderStatus.RESERVED)
    reserved_qty = sum(o.quantity for o in reserved_orders if o.sample_id == "A-001")

    assert_eq(reserved_qty, 10, "CONFIRMED 전환된 주문은 예약 수량에서 제외")


def _test_reserved_qty_per_sample() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)

    ctx.order_service.place_order("고객1", "A-001", 10)
    ctx.order_service.place_order("고객2", "A-001", 20)
    ctx.order_service.place_order("고객3", "B-001", 15)

    reserved = ctx.order_service.get_all(OrderStatus.RESERVED)
    qty_map: dict[str, int] = {}
    for o in reserved:
        qty_map[o.sample_id] = qty_map.get(o.sample_id, 0) + o.quantity

    assert_eq(qty_map.get("A-001", 0), 30)
    assert_eq(qty_map.get("B-001", 0), 15)


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
