"""Refactor R4 테스트: 더미 데이터 생성 도구."""
import random

from app import AppContext
from model.order import OrderStatus
from model.production import QueueStatus
from tests.db_helper import make_test_conn
from tests.harness import TestHarness, assert_eq, assert_true
from tools.dummy_data import (
    _apply_transitions,
    _build_status_list,
    _drain_stock,
    _ensure_stock,
    _generate_orders,
    _generate_samples,
    _reset,
)


def _make_ctx() -> AppContext:
    return AppContext(make_test_conn())


def run_tests() -> bool:
    h = TestHarness("Refactor R4 — 더미 데이터 생성")

    h.run("상태 분포 목록 — 총 건수 일치",          test_status_list_count)
    h.run("상태 분포 목록 — 모든 상태 포함",         test_status_list_coverage)
    h.run("시료 생성 — 프리셋 N종 등록",             test_generate_samples)
    h.run("주문 생성 후 RESERVED 상태",             test_generate_orders_reserved)
    h.run("상태 전이 — CONFIRMED 정상",             test_transition_confirmed)
    h.run("상태 전이 — PRODUCING (재고 0)",          test_transition_producing)
    h.run("상태 전이 — RELEASE",                    test_transition_release)
    h.run("상태 전이 — REJECTED",                   test_transition_rejected)
    h.run("ensure_stock — 부족 시 재고 보충",        test_ensure_stock)
    h.run("drain_stock — 재고 0으로 소진",           test_drain_stock)
    h.run("seed 고정 시 재현 가능한 결과",            test_seed_reproducible)
    h.run("reset — 전체 테이블 초기화",              test_reset)

    return h.report()


# ── 분포 ──────────────────────────────────────────────────

def test_status_list_count() -> None:
    rng = random.Random(42)
    lst = _build_status_list(15, rng)
    assert_eq(len(lst), 15)


def test_status_list_coverage() -> None:
    rng = random.Random(1)
    lst = _build_status_list(20, rng)
    statuses = set(lst)
    for s in OrderStatus:
        assert_true(s in statuses, f"{s.value} 가 분포에 없음")


# ── 시료 / 주문 생성 ──────────────────────────────────────

def test_generate_samples() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    ids = _generate_samples(ctx, 3, rng)
    assert_eq(len(ids), 3)
    for sid in ids:
        assert_true(ctx.sample_repo.exists(sid))


def test_generate_orders_reserved() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    ids = _generate_samples(ctx, 3, rng)
    orders = _generate_orders(ctx, 5, ids, rng)
    assert_eq(len(orders), 5)
    for order, _ in orders:
        assert_eq(order.status, OrderStatus.RESERVED)


# ── 상태 전이 ─────────────────────────────────────────────

def test_transition_confirmed() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    _generate_samples(ctx, 3, rng)

    order = ctx.order_service.place_order("고객", "A-001", 10)
    _ensure_stock(ctx, "A-001", 10)
    ctx.order_service.approve(order.order_id)

    updated = ctx.order_service.get(order.order_id)
    assert_eq(updated.status, OrderStatus.CONFIRMED)


def test_transition_producing() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    _generate_samples(ctx, 3, rng)

    order = ctx.order_service.place_order("고객", "A-001", 10)
    _drain_stock(ctx, "A-001")
    ctx.order_service.approve(order.order_id)

    updated = ctx.order_service.get(order.order_id)
    assert_eq(updated.status, OrderStatus.PRODUCING)


def test_transition_release() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    _generate_samples(ctx, 3, rng)

    order = ctx.order_service.place_order("고객", "A-001", 5)
    _ensure_stock(ctx, "A-001", 5)
    ctx.order_service.approve(order.order_id)
    ctx.release_service.release_one(order.order_id)

    updated = ctx.order_service.get(order.order_id)
    assert_eq(updated.status, OrderStatus.RELEASE)


def test_transition_rejected() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    _generate_samples(ctx, 3, rng)

    order = ctx.order_service.place_order("고객", "A-001", 5)
    ctx.order_service.reject(order.order_id)

    updated = ctx.order_service.get(order.order_id)
    assert_eq(updated.status, OrderStatus.REJECTED)


# ── 재고 헬퍼 ─────────────────────────────────────────────

def test_ensure_stock() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    _generate_samples(ctx, 3, rng)

    _drain_stock(ctx, "A-001")
    _ensure_stock(ctx, "A-001", 50)
    assert_true(ctx.sample_service.get("A-001").stock >= 50)


def test_drain_stock() -> None:
    ctx = _make_ctx()
    rng = random.Random(0)
    _generate_samples(ctx, 3, rng)

    _ensure_stock(ctx, "A-001", 100)
    _drain_stock(ctx, "A-001")
    assert_eq(ctx.sample_service.get("A-001").stock, 0)


# ── seed / reset ──────────────────────────────────────────

def test_seed_reproducible() -> None:
    def _run_with_seed(seed: int) -> list[OrderStatus]:
        ctx = _make_ctx()
        rng = random.Random(seed)
        ids    = _generate_samples(ctx, 3, rng)
        orders = _generate_orders(ctx, 10, ids, rng)
        return [desired for _, desired in orders]

    result1 = _run_with_seed(42)
    result2 = _run_with_seed(42)
    assert_eq(result1, result2, "같은 seed → 동일한 결과")


def test_reset() -> None:
    ctx  = _make_ctx()
    conn = ctx.sample_repo._conn

    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.order_service.place_order.__func__  # just to ensure service exists
    # Reset
    _reset(conn)

    samples = ctx.sample_repo.find_all()
    orders  = ctx.order_repo.find_all()
    assert_eq(len(samples), 0, "reset 후 시료 0건")
    assert_eq(len(orders),  0, "reset 후 주문 0건")


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
