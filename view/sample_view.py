from model.sample import Sample
from utils.display import TABLE_DIVIDER, ljust_display
from view.base_view import BaseView


class SampleView(BaseView):

    def show_menu(self) -> str:
        return super().show_menu("시료 관리", [
            ("1", "시료 등록"),
            ("2", "시료 목록"),
            ("3", "시료 검색"),
            ("0", "메인 메뉴로 돌아가기"),
        ])

    # ── 시료 등록 ─────────────────────────────────────────

    def get_sample_id(self) -> str:
        return self.get_input("시료 ID     ")

    def get_name(self) -> str:
        return self.get_input("시료명      ")

    def get_avg_time(self) -> str:
        return self.get_input("평균 생산시간 (min/ea)")

    def get_yield_rate(self) -> str:
        return self.get_input("수율 (0.01 ~ 1.00)   ")

    def show_register_confirm(
        self, sample_id: str, name: str, avg_time: float, yield_rate: float
    ) -> None:
        self.divider()
        print("  입력 내용 확인")
        self.divider()
        print(f"  시료 ID        : {sample_id}")
        print(f"  시료명         : {name}")
        print(f"  평균 생산시간  : {avg_time} min/ea")
        print(f"  수율           : {yield_rate} ({yield_rate * 100:.0f}%)")
        self.divider()

    def ask_register(self) -> bool:
        return self.confirm("등록하시겠습니까? (Y/N)")

    def show_register_success(self, sample: Sample) -> None:
        self.success(f"시료 '{sample.sample_id} {sample.name}' 이(가) 등록되었습니다.")

    # ── 시료 목록 / 검색 ──────────────────────────────────

    def get_search_keyword(self) -> str:
        return self.get_input("검색어 (이름 / ID)")

    def show_sample_table(self, title: str, samples: list[Sample]) -> None:
        print(TABLE_DIVIDER)
        print(f"  {title}")
        print(TABLE_DIVIDER)
        print(f" {'ID':<10}{ljust_display('시료명', 20)}{'평균생산시간':>14}{'수율':>6}{'현재 재고':>10}")
        print(TABLE_DIVIDER)
        for s in samples:
            print(
                f" {s.sample_id:<10}"
                f"{ljust_display(s.name, 20)}"
                f"{_fmt_time(s.avg_production_time):>14}"
                f"{s.yield_percent():>6}"
                f"{_fmt_stock(s.stock):>10}"
            )
        print(TABLE_DIVIDER)

    def show_no_result(self) -> None:
        self.info("검색 결과가 없습니다.")


# ── 표시 형식 (테스트 가능하도록 모듈 수준 함수로 노출) ────

def _fmt_time(minutes: float) -> str:
    return f"{minutes:.0f} min/ea"


def _fmt_stock(stock: int) -> str:
    return f"{stock} ea ⚠" if stock == 0 else f"{stock} ea"
