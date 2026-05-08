"""Phase 2 테스트: 시료 주문 (OrderService)."""
from datetime import datetime

from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository
from model.order import OrderStatus
from service.order_service import OrderService
from service.sample_service import SampleNotFoundError, SampleService
from tests.harness import TestHarness, assert_eq, assert_raises, assert_true


def _make_services():
    from tests.db_helper import make_test_conn
    conn            = make_test_conn()
    sample_repo     = SampleRepository(conn)
    order_repo      = OrderRepository(conn)
    production_repo = ProductionRepository(conn)
    sample_svc      = SampleService(sample_repo)
    order_svc       = OrderService(order_repo, production_repo, sample_svc)
    return sample_svc, order_svc


def run_tests() -> bool:
    h = TestHarness("Phase 2 — 시료 주문")

    h.run("주문 생성 후 RESERVED 상태",              _test_place_order_reserved)
    h.run("존재하지 않는 시료 ID → SampleNotFoundError", _test_invalid_sample_id)
    h.run("주문 ID 형식 ORD-YYYYMMDD-NNN",           _test_order_id_format)
    h.run("당일 복수 주문 시 순번 증가",              _test_order_id_sequence)
    h.run("주문 필드 값 저장 확인",                   _test_order_fields)

    return h.report()


# ── OrderService ───────────────────────────────────────────

def _test_place_order_reserved() -> None:
    sample_svc, order_svc = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)

    order = order_svc.place_order("(주)반도체코리아", "A-001", 30)

    assert_eq(order.status, OrderStatus.RESERVED)


def _test_invalid_sample_id() -> None:
    _, order_svc = _make_services()
    assert_raises(SampleNotFoundError, order_svc.place_order, "고객", "X-999", 10)


def _test_order_id_format() -> None:
    sample_svc, order_svc = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)

    order = order_svc.place_order("고객", "A-001", 1)
    today = datetime.now().strftime("%Y%m%d")

    assert_true(order.order_id.startswith(f"ORD-{today}-"), f"ID 형식 불일치: {order.order_id}")
    assert_true(order.order_id.endswith("-001"), f"첫 순번 불일치: {order.order_id}")


def _test_order_id_sequence() -> None:
    sample_svc, order_svc = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)

    o1 = order_svc.place_order("고객1", "A-001", 1)
    o2 = order_svc.place_order("고객2", "A-001", 1)
    o3 = order_svc.place_order("고객3", "A-001", 1)

    assert_true(o1.order_id.endswith("-001"), o1.order_id)
    assert_true(o2.order_id.endswith("-002"), o2.order_id)
    assert_true(o3.order_id.endswith("-003"), o3.order_id)


def _test_order_fields() -> None:
    sample_svc, order_svc = _make_services()
    sample_svc.register("A-001", "갈륨비소", 45.0, 0.92)

    order = order_svc.place_order("(주)반도체코리아", "A-001", 30)

    assert_eq(order.customer_name, "(주)반도체코리아")
    assert_eq(order.sample_id,     "A-001")
    assert_eq(order.quantity,      30)
    assert_eq(order.reject_reason, "")


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
