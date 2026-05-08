"""Phase 3 테스트: 주문 승인 / 거절 (OrderService.approve / reject)."""
import math

from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository
from model.order import OrderStatus
from model.production import QueueStatus
from service.order_service import InvalidStatusTransitionError, OrderNotFoundError, OrderService
from service.sample_service import SampleService
from tests.harness import TestHarness, assert_eq, assert_raises, assert_true


def _make_services():
    from tests.db_helper import make_test_conn
    conn            = make_test_conn()
    sample_repo     = SampleRepository(conn)
    order_repo      = OrderRepository(conn)
    production_repo = ProductionRepository(conn)
    sample_svc      = SampleService(sample_repo)
    order_svc       = OrderService(order_repo, production_repo, sample_svc)
    return sample_svc, order_svc, production_repo


def run_tests() -> bool:
    h = TestHarness("Phase 3 — 주문 승인 / 거절")

    h.run("승인 — 재고 충분 → CONFIRMED",               test_approve_confirmed)
    h.run("승인 — 재고 충분 → 재고 차감",               test_approve_stock_deducted)
    h.run("승인 — 재고 부족 → PRODUCING",               test_approve_producing)
    h.run("승인 — 부족분 기준 생산 필요량 계산",         test_approve_shortage_based_qty)
    h.run("승인 — 재고 0 → 전체 수량 기준 생산",        test_approve_zero_stock)
    h.run("승인 — PRODUCING 시 기존 재고 유지",          test_approve_stock_unchanged)
    h.run("거절 → REJECTED",                             test_reject)
    h.run("RESERVED 아닌 주문 승인 → 오류",              test_approve_wrong_status)
    h.run("RESERVED 아닌 주문 거절 → 오류",              test_reject_wrong_status)
    h.run("없는 주문 ID 승인 → OrderNotFoundError",      test_approve_not_found)

    return h.report()


# ── 승인 ──────────────────────────────────────────────────

def test_approve_confirmed() -> None:
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)
    sample_svc.update_stock("A-001", 50)

    order   = order_svc.place_order("고객", "A-001", 30)
    approved = order_svc.approve(order.order_id)

    assert_eq(approved.status, OrderStatus.CONFIRMED)


def test_approve_stock_deducted() -> None:
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)
    sample_svc.update_stock("A-001", 50)

    order = order_svc.place_order("고객", "A-001", 30)
    order_svc.approve(order.order_id)

    assert_eq(sample_svc.get("A-001").stock, 20)


def test_approve_producing() -> None:
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("B-001", "인화인듐", 120.0, 0.75)
    sample_svc.update_stock("B-001", 10)

    order   = order_svc.place_order("고객", "B-001", 30)
    approved = order_svc.approve(order.order_id)

    assert_eq(approved.status, OrderStatus.PRODUCING)


def test_approve_shortage_based_qty() -> None:
    """부족분 기준 + 오차 10% 반영: ceil(shortage / (yield_rate × 0.9))."""
    sample_svc, order_svc, prod_repo = _make_services()
    sample_svc.register("B-001", "인화인듐", 120.0, 0.75)
    sample_svc.update_stock("B-001", 10)   # stock=10, order=30, shortage=20

    order = order_svc.place_order("고객", "B-001", 30)
    order_svc.approve(order.order_id)

    queue = prod_repo.find_by_order(order.order_id)
    expected = math.ceil(20 / (0.75 * 0.9))   # ceil(20 / 0.675) = 30
    assert_eq(queue.required_qty, expected)


def test_approve_zero_stock() -> None:
    """재고 0이면 전체 수량이 부족분: ceil(order_qty / (yield_rate × 0.9))."""
    sample_svc, order_svc, prod_repo = _make_services()
    sample_svc.register("B-001", "인화인듐", 120.0, 0.75)  # stock=0

    order = order_svc.place_order("고객", "B-001", 20)
    order_svc.approve(order.order_id)

    queue    = prod_repo.find_by_order(order.order_id)
    expected = math.ceil(20 / (0.75 * 0.9))   # ceil(20 / 0.675) = 30
    assert_eq(queue.required_qty, expected)


def test_approve_stock_unchanged() -> None:
    """PRODUCING 전환 시 기존 재고는 유지 (생산 완료 시점에 정산)."""
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("B-001", "인화인듐", 120.0, 0.75)
    sample_svc.update_stock("B-001", 10)

    order = order_svc.place_order("고객", "B-001", 30)
    order_svc.approve(order.order_id)

    assert_eq(sample_svc.get("B-001").stock, 10)   # 재고 변화 없음


# ── 거절 ──────────────────────────────────────────────────

def test_reject() -> None:
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)

    order    = order_svc.place_order("고객", "A-001", 10)
    rejected = order_svc.reject(order.order_id)

    assert_eq(rejected.status, OrderStatus.REJECTED)


# ── 오류 케이스 ───────────────────────────────────────────

def test_approve_wrong_status() -> None:
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)
    sample_svc.update_stock("A-001", 50)

    order = order_svc.place_order("고객", "A-001", 10)
    order_svc.approve(order.order_id)   # → CONFIRMED
    assert_raises(InvalidStatusTransitionError, order_svc.approve, order.order_id)


def test_reject_wrong_status() -> None:
    sample_svc, order_svc, _ = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)
    sample_svc.update_stock("A-001", 50)

    order = order_svc.place_order("고객", "A-001", 10)
    order_svc.approve(order.order_id)   # → CONFIRMED
    assert_raises(InvalidStatusTransitionError, order_svc.reject, order.order_id, "사유")


def test_approve_not_found() -> None:
    _, order_svc, _ = _make_services()
    assert_raises(OrderNotFoundError, order_svc.approve, "ORD-00000000-000")


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
