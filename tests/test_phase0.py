"""Phase 0 테스트: 메인 화면 (AppContext 초기화 + 현황 요약 집계)."""
from app import AppContext
from controller.main_controller import _collect_summary, _is_yes
from tests.harness import TestHarness, assert_eq, assert_true


def _make_ctx() -> AppContext:
    return AppContext()


def run_tests() -> bool:
    h = TestHarness("Phase 0 — 메인 화면")

    h.run("AppContext 초기화 — 모든 서비스 생성", _test_app_context_init)
    h.run("빈 상태 요약 — 전체 0값",              _test_summary_empty)
    h.run("시료 등록 후 등록 시료 수 반영",        _test_summary_sample_count)
    h.run("재고 변경 후 총 재고 반영",             _test_summary_total_stock)
    h.run("주문 후 전체 주문 수 반영",             _test_summary_total_orders)
    h.run("REJECTED 는 전체 주문에서 제외",        _test_summary_rejected_excluded)
    h.run("생산 큐 WAITING 건수 반영",             _test_summary_waiting_count)
    h.run("주문 상태별 카운트 반영",               _test_summary_status_counts)
    h.run("종료 확인 — Y/y 만 긍정",              _test_is_yes)

    return h.report()


# ── AppContext ─────────────────────────────────────────────

def _test_app_context_init() -> None:
    ctx = _make_ctx()
    assert_true(ctx.sample_service    is not None)
    assert_true(ctx.order_service     is not None)
    assert_true(ctx.production_service is not None)
    assert_true(ctx.release_service   is not None)
    assert_true(ctx.monitoring_service is not None)


# ── 현황 요약 집계 ────────────────────────────────────────

def _test_summary_empty() -> None:
    summary = _collect_summary(_make_ctx())
    assert_eq(summary["sample_count"],  0)
    assert_eq(summary["total_stock"],   0)
    assert_eq(summary["total_orders"],  0)
    assert_eq(summary["waiting_count"], 0)
    assert_eq(summary["reserved"],      0)
    assert_eq(summary["producing"],     0)
    assert_eq(summary["confirmed"],     0)


def _test_summary_sample_count() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.register("A-002", "실리콘",   30.0, 0.88)
    assert_eq(_collect_summary(ctx)["sample_count"], 2)


def _test_summary_total_stock() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.register("A-002", "실리콘",   30.0, 0.88)
    ctx.sample_service.update_stock("A-001", 100)
    ctx.sample_service.update_stock("A-002",  65)
    assert_eq(_collect_summary(ctx)["total_stock"], 165)


def _test_summary_total_orders() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)
    ctx.order_service.place_order("고객1", "A-001", 5)
    ctx.order_service.place_order("고객2", "A-001", 5)
    assert_eq(_collect_summary(ctx)["total_orders"], 2)


def _test_summary_rejected_excluded() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)
    ctx.order_service.place_order("고객1", "A-001", 5)
    o2 = ctx.order_service.place_order("고객2", "A-001", 5)
    ctx.order_service.reject(o2.order_id, "테스트 거절")
    assert_eq(_collect_summary(ctx)["total_orders"], 1, "REJECTED 제외")


def _test_summary_waiting_count() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    # 재고 0 → 승인 시 생산 큐 WAITING 등록
    o = ctx.order_service.place_order("고객1", "A-001", 10)
    ctx.order_service.approve(o.order_id)
    assert_eq(_collect_summary(ctx)["waiting_count"], 1)


def _test_summary_status_counts() -> None:
    ctx = _make_ctx()
    ctx.sample_service.register("A-001", "갈륨비소", 45.0, 0.92)
    ctx.sample_service.update_stock("A-001", 100)

    ctx.order_service.place_order("고객1", "A-001", 5)          # RESERVED
    o2 = ctx.order_service.place_order("고객2", "A-001", 5)
    ctx.order_service.approve(o2.order_id)                       # CONFIRMED (재고 충분)

    summary = _collect_summary(ctx)
    assert_eq(summary["reserved"],  1)
    assert_eq(summary["confirmed"], 1)
    assert_eq(summary["producing"], 0)


# ── 종료 확인 ─────────────────────────────────────────────

def _test_is_yes() -> None:
    assert_true(_is_yes("Y"),  "대문자 Y")
    assert_true(_is_yes("y"),  "소문자 y")
    assert_true(not _is_yes("N"),   "N은 긍정 아님")
    assert_true(not _is_yes("n"),   "n은 긍정 아님")
    assert_true(not _is_yes(""),    "빈 입력은 긍정 아님")
    assert_true(not _is_yes("yes"), "yes는 긍정 아님")


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
