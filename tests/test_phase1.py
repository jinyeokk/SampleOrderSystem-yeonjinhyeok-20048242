"""Phase 1 테스트: 시료 관리 (SampleService)."""
from repository.sample_repo import SampleRepository
from service.sample_service import DuplicateSampleIdError, SampleNotFoundError, SampleService
from tests.harness import TestHarness, assert_eq, assert_raises, assert_true


def _make_service() -> SampleService:
    return SampleService(SampleRepository())


def run_tests() -> bool:
    h = TestHarness("Phase 1 — 시료 관리")

    h.run("시료 등록 후 조회 가능",                   _test_register_and_get)
    h.run("중복 ID 등록 시 DuplicateSampleIdError",   _test_duplicate_id)
    h.run("존재하지 않는 ID 조회 시 SampleNotFoundError", _test_not_found)
    h.run("전체 조회는 ID 오름차순 정렬",              _test_get_all_sorted)
    h.run("이름 부분 일치 검색",                      _test_search_by_name)
    h.run("ID 부분 일치 검색",                        _test_search_by_id)
    h.run("검색 대소문자 무시",                        _test_search_case_insensitive)
    h.run("재고 증감 반영",                            _test_update_stock)
    h.run("required_production 수율 보정 계산",        _test_required_production)
    h.run("yield_percent 퍼센트 문자열 변환",          _test_yield_percent)
    h.run("_fmt_time: min/ea 형식 반환",               _test_fmt_time)
    h.run("_fmt_stock: ea 단위 및 재고 0 경고 표시",   _test_fmt_stock)

    return h.report()


# ── SampleService ──────────────────────────────────────────

def _test_register_and_get() -> None:
    svc = _make_service()
    svc.register("A-001", "갈륨비소 웨이퍼", 45.0, 0.92)
    sample = svc.get("A-001")
    assert_eq(sample.sample_id, "A-001")
    assert_eq(sample.name, "갈륨비소 웨이퍼")
    assert_eq(sample.stock, 0)


def _test_duplicate_id() -> None:
    svc = _make_service()
    svc.register("A-001", "갈륨비소 웨이퍼", 45.0, 0.92)
    assert_raises(DuplicateSampleIdError, svc.register, "A-001", "다른 이름", 30.0, 0.88)


def _test_not_found() -> None:
    svc = _make_service()
    assert_raises(SampleNotFoundError, svc.get, "X-999")


def _test_get_all_sorted() -> None:
    svc = _make_service()
    svc.register("B-001", "인화인듐", 120.0, 0.75)
    svc.register("A-001", "갈륨비소", 45.0, 0.92)
    svc.register("A-002", "실리콘",   30.0, 0.88)
    ids = [s.sample_id for s in svc.get_all()]
    assert_eq(ids, ["A-001", "A-002", "B-001"])


def _test_search_by_name() -> None:
    svc = _make_service()
    svc.register("A-001", "갈륨비소 웨이퍼", 45.0, 0.92)
    svc.register("A-002", "실리콘 기판",     30.0, 0.88)
    results = svc.search("갈륨")
    assert_eq(len(results), 1)
    assert_eq(results[0].sample_id, "A-001")


def _test_search_by_id() -> None:
    svc = _make_service()
    svc.register("A-001", "갈륨비소", 45.0, 0.92)
    svc.register("B-001", "실리콘",   30.0, 0.88)
    results = svc.search("b-")
    assert_eq(len(results), 1)
    assert_eq(results[0].sample_id, "B-001")


def _test_search_case_insensitive() -> None:
    svc = _make_service()
    svc.register("A-001", "GaAs Wafer", 45.0, 0.92)
    assert_eq(len(svc.search("gaas")), 1)
    assert_eq(len(svc.search("WAFER")), 1)


def _test_update_stock() -> None:
    svc = _make_service()
    svc.register("A-001", "갈륨비소", 45.0, 0.92)
    svc.update_stock("A-001", 100)
    assert_eq(svc.get("A-001").stock, 100)
    svc.update_stock("A-001", -30)
    assert_eq(svc.get("A-001").stock, 70)


def _test_required_production() -> None:
    svc = _make_service()
    svc.register("B-001", "인화인듐", 120.0, 0.75)
    sample = svc.get("B-001")
    assert_eq(sample.required_production(20), 27)  # ceil(20 / 0.75)
    assert_eq(sample.required_production(10), 14)  # ceil(10 / 0.75)


def _test_yield_percent() -> None:
    svc = _make_service()
    svc.register("A-001", "갈륨비소", 45.0, 0.92)
    assert_eq(svc.get("A-001").yield_percent(), "92%")


# ── 표시 형식 ─────────────────────────────────────────────

def _test_fmt_time() -> None:
    from menu.sample_menu import _fmt_time
    assert_eq(_fmt_time(45.0),  "45 min/ea")
    assert_eq(_fmt_time(30.0),  "30 min/ea")
    assert_eq(_fmt_time(120.0), "120 min/ea")


def _test_fmt_stock() -> None:
    from menu.sample_menu import _fmt_stock
    assert_eq(_fmt_stock(120), "120 ea")
    assert_eq(_fmt_stock(0),   "0 ea ⚠")
    assert_eq(_fmt_stock(1),   "1 ea")


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
