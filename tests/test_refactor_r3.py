"""Refactor R3 테스트: 관리자 콘솔 쿼리 로직."""
from app import AppContext
from model.order import OrderStatus
from model.production import QueueStatus
from tests.db_helper import make_test_conn
from tests.harness import TestHarness, assert_eq, assert_true


def _make_ctx() -> AppContext:
    return AppContext(make_test_conn())


def run_tests() -> bool:
    h = TestHarness("Refactor R3 — 관리자 콘솔")

    h.run("빈 DB stats: 모든 값 0",           _test_stats_empty)
    h.run("시료 등록 후 samples 조회",         _test_samples_list)
    h.run("주문 후 orders 조회",               _test_orders_list)
    h.run("상태 필터 orders 조회",             _test_orders_filter)
    h.run("단건 order 조회",                   _test_order_detail)
    h.run("없는 주문 ID 조회 → None",         _test_order_not_found)
    h.run("생산 큐 queue 조회",                _test_queue)
    h.run("이력 history 조회",                 _test_history)

    return h.report()


def _test_stats_empty() -> None:
    ctx     = _make_ctx()
    samples = ctx.sample_repo.find_all()
    counts  = ctx.order_repo.count_by_status()
    waiting = ctx.production_repo.find_by_status(QueueStatus.WAITING)

    assert_eq(len(samples), 0)
    assert_eq(sum(counts.values()), 0)
    assert_eq(len(waiting), 0)


def _test_samples_list() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)

    samples = ctx.sample_repo.find_all()
    assert_eq(len(samples), 2)
    assert_eq(samples[0].sample_id, "A-001")


def _test_orders_list() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.order_service.place_order("고객1", "A-001", 10)
    ctx.order_service.place_order("고객2", "A-001", 20)

    orders = ctx.order_repo.find_all()
    assert_eq(len(orders), 2)


def _test_orders_filter() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)
    o1 = ctx.order_service.place_order("고객1", "A-001", 10)
    o2 = ctx.order_service.place_order("고객2", "A-001", 10)
    ctx.order_service.approve(o2.order_id)   # → CONFIRMED

    reserved  = ctx.order_repo.find_by_status(OrderStatus.RESERVED)
    confirmed = ctx.order_repo.find_by_status(OrderStatus.CONFIRMED)
    assert_eq(len(reserved),  1)
    assert_eq(len(confirmed), 1)


def _test_order_detail() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    order = ctx.order_service.place_order("(주)반도체코리아", "A-001", 30)

    found = ctx.order_repo.find_by_id(order.order_id)
    assert_true(found is not None)
    assert_eq(found.customer_name, "(주)반도체코리아")
    assert_eq(found.quantity, 30)
    assert_eq(found.status, OrderStatus.RESERVED)


def _test_order_not_found() -> None:
    ctx   = _make_ctx()
    found = ctx.order_repo.find_by_id("ORD-00000000-000")
    assert_true(found is None)


def _test_queue() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)
    order = ctx.order_service.place_order("고객", "B-001", 20)
    ctx.order_service.approve(order.order_id)   # 재고 0 → PRODUCING

    waiting = ctx.production_repo.find_by_status(QueueStatus.WAITING)
    assert_eq(len(waiting), 1)
    assert_eq(waiting[0].order_id, order.order_id)


def _test_history() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)
    order = ctx.order_service.place_order("고객", "A-001", 10)
    ctx.order_service.approve(order.order_id)

    history = ctx.order_repo.get_recent_history(10)
    assert_true(len(history) >= 2, "주문 접수 + 승인 이력 2건 이상")
    descriptions = [h["description"] for h in history]
    assert_true(any("CONFIRMED" in d for d in descriptions))


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
