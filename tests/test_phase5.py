"""Phase 5 테스트: 생산라인 (실 생산량 공식 / 생산 완료 / FIFO)."""
import math
import time

from app import AppContext
from view.production_view import _progress_bar
from model.order import OrderStatus
from model.production import QueueStatus
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository
from service.order_service import OrderService
from service.production_service import ProductionService
from service.sample_service import SampleService
from tests.harness import TestHarness, assert_eq, assert_true


def _make_ctx() -> AppContext:
    from tests.db_helper import make_test_conn
    return AppContext(make_test_conn())


def run_tests() -> bool:
    h = TestHarness("Phase 5 — 생산라인")

    h.run("실 생산량: ceil(부족분 / (수율 × 0.9))",   test_required_qty_formula)
    h.run("재고 0 → 전량 부족분 기준 실 생산량",       test_required_qty_zero_stock)
    h.run("생산 완료 후 CONFIRMED 전환",               test_complete_confirmed)
    h.run("생산 완료 후 재고 보정",                    test_complete_stock)
    h.run("PRODUCING 없으면 RUNNING 아님",             test_not_running)
    h.run("PRODUCING 존재 시 RUNNING",                 test_running)
    h.run("대기 큐 FIFO 순서 (queued_at 오름차순)",    test_fifo_order)
    h.run("진행률 바 — 0%",                           test_progress_bar_zero)
    h.run("진행률 바 — 50%",                          test_progress_bar_half)
    h.run("진행률 바 — 100%",                         test_progress_bar_full)

    return h.report()


# ── 실 생산량 공식 ────────────────────────────────────────

def test_required_qty_formula() -> None:
    """stock=10, order=30, shortage=20, yield=0.75 → ceil(20/(0.75×0.9)) = 30."""
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)
    ctx.sample_service.update_stock("B-001", 10)

    order = ctx.order_service.place_order("고객", "B-001", 30)
    ctx.order_service.approve(order.order_id)

    queue    = ctx.production_repo.find_by_order(order.order_id)
    expected = math.ceil(20 / (0.75 * 0.9))   # 30
    assert_eq(queue.required_qty, expected)


def test_required_qty_zero_stock() -> None:
    """stock=0, order=20, shortage=20, yield=0.75 → ceil(20/(0.75×0.9)) = 30."""
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)

    order = ctx.order_service.place_order("고객", "B-001", 20)
    ctx.order_service.approve(order.order_id)

    queue    = ctx.production_repo.find_by_order(order.order_id)
    expected = math.ceil(20 / (0.75 * 0.9))   # 30
    assert_eq(queue.required_qty, expected)


# ── 생산 완료 ─────────────────────────────────────────────

def test_complete_confirmed() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)

    order = ctx.order_service.place_order("고객", "B-001", 20)
    ctx.order_service.approve(order.order_id)
    result = ctx.production_service.complete_production(order.order_id)

    assert_eq(result.status, OrderStatus.CONFIRMED)


def test_complete_stock() -> None:
    """stock=0, required=30, order=20 → 완료 후 stock = 0 + 30 - 20 = 10."""
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)

    order = ctx.order_service.place_order("고객", "B-001", 20)
    ctx.order_service.approve(order.order_id)

    queue = ctx.production_repo.find_by_order(order.order_id)
    required = queue.required_qty  # 30

    ctx.production_service.complete_production(order.order_id)

    expected_stock = required - 20   # 30 - 20 = 10
    assert_eq(ctx.sample_service.get("B-001").stock, expected_stock)


# ── RUNNING / STOP ────────────────────────────────────────

def test_not_running() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)
    order = ctx.order_service.place_order("고객", "A-001", 10)
    ctx.order_service.approve(order.order_id)   # → CONFIRMED (재고 충분)

    items = ctx.production_service.get_in_progress()
    assert_eq(len(items), 0, "CONFIRMED 전환된 주문은 생산라인에 없음")


def test_running() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)
    order = ctx.order_service.place_order("고객", "B-001", 10)
    ctx.order_service.approve(order.order_id)   # → PRODUCING (재고 부족)

    items = ctx.production_service.get_in_progress()
    assert_eq(len(items), 1)


# ── FIFO ──────────────────────────────────────────────────

def test_fifo_order() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("B-001", "인화인듐", 120.0, 0.75)

    o1 = ctx.order_service.place_order("고객1", "B-001", 10)
    ctx.order_service.approve(o1.order_id)
    time.sleep(0.01)
    o2 = ctx.order_service.place_order("고객2", "B-001", 10)
    ctx.order_service.approve(o2.order_id)
    time.sleep(0.01)
    o3 = ctx.order_service.place_order("고객3", "B-001", 10)
    ctx.order_service.approve(o3.order_id)

    items = sorted(
        ctx.production_service.get_in_progress(),
        key=lambda x: x[1].queued_at,
    )
    assert_eq(items[0][0].order_id, o1.order_id, "FIFO 첫 번째")
    assert_eq(items[1][0].order_id, o2.order_id, "FIFO 두 번째")
    assert_eq(items[2][0].order_id, o3.order_id, "FIFO 세 번째")


# ── 진행률 바 ─────────────────────────────────────────────

def test_progress_bar_zero() -> None:
    bar = _progress_bar(0, 30)
    assert_eq(bar, "░" * 20)


def test_progress_bar_half() -> None:
    bar = _progress_bar(15, 30)
    assert_eq(bar, "▓" * 10 + "░" * 10)


def test_progress_bar_full() -> None:
    bar = _progress_bar(30, 30)
    assert_eq(bar, "▓" * 20)


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
