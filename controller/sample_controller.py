from app import AppContext
from service.sample_service import DuplicateSampleIdError, SampleNotFoundError
from utils.validator import validate_max_length, validate_non_empty, validate_positive_float, validate_yield_rate
from view.sample_view import SampleView


class SampleController:

    def __init__(self, ctx: AppContext, view: SampleView) -> None:
        self._ctx  = ctx
        self._view = view

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "0":
                break
            elif choice == "1":
                self._register()
            elif choice == "2":
                self._list_all()
            elif choice == "3":
                self._search()
            else:
                self._view.error("유효하지 않은 선택입니다.")

    def _register(self) -> None:
        self._view.section("시료 등록")
        try:
            sample_id  = self._read_sample_id()
            name       = self._read_name()
            avg_time   = self._read_avg_time()
            yield_rate = self._read_yield_rate()
        except ValueError as e:
            self._view.error(str(e))
            return

        self._view.show_register_confirm(sample_id, name, avg_time, yield_rate)
        if not self._view.ask_register():
            self._view.info("등록이 취소되었습니다.")
            return

        try:
            sample = self._ctx.sample_service.register(sample_id, name, avg_time, yield_rate)
            self._view.show_register_success(sample)
        except DuplicateSampleIdError as e:
            self._view.error(f"이미 존재하는 시료 ID입니다: {e}")

    def _list_all(self) -> None:
        samples = self._ctx.sample_service.get_all()
        self._view.show_sample_table(f"시료 목록 (총 {len(samples)}건)", samples)
        self._view.wait()

    def _search(self) -> None:
        self._view.section("시료 검색")
        keyword = self._view.get_search_keyword()
        results = self._ctx.sample_service.search(keyword)
        if not results:
            self._view.show_no_result()
        else:
            self._view.show_sample_table(f"검색 결과 ({len(results)}건)", results)
        self._view.wait()

    # ── 입력 + 검증 ───────────────────────────────────────

    def _read_sample_id(self) -> str:
        val = self._view.get_sample_id()
        validate_non_empty(val, "시료 ID")
        validate_max_length(val, 20, "시료 ID")
        return val

    def _read_name(self) -> str:
        val = self._view.get_name()
        validate_non_empty(val, "시료명")
        validate_max_length(val, 50, "시료명")
        return val

    def _read_avg_time(self) -> float:
        return validate_positive_float(self._view.get_avg_time(), "평균 생산시간")

    def _read_yield_rate(self) -> float:
        return validate_yield_rate(self._view.get_yield_rate())
