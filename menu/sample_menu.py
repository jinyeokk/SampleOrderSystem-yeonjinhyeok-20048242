from app import AppContext
from service.sample_service import DuplicateSampleIdError
from utils.display import (
    TABLE_DIVIDER,
    input_menu,
    ljust_display,
    print_divider,
    print_section,
    prompt,
)
from utils.validator import (
    validate_max_length,
    validate_non_empty,
    validate_positive_float,
    validate_yield_rate,
)


def run(ctx: AppContext) -> None:
    while True:
        choice = input_menu("시료 관리", [
            ("1", "시료 등록"),
            ("2", "시료 목록"),
            ("3", "시료 검색"),
            ("0", "메인 메뉴로 돌아가기"),
        ])
        if choice == "0":
            break
        elif choice == "1":
            _register(ctx)
        elif choice == "2":
            _list_all(ctx)
        elif choice == "3":
            _search(ctx)
        else:
            print("[오류] 유효하지 않은 선택입니다.")


def _register(ctx: AppContext) -> None:
    print_section("시료 등록")
    try:
        sample_id = _input_sample_id()
        name      = _input_name()
        avg_time  = _input_avg_production_time()
        yield_rate = _input_yield_rate()
    except ValueError as e:
        print(f"[오류] {e}")
        return

    _print_registration_summary(sample_id, name, avg_time, yield_rate)
    if prompt("등록하시겠습니까? (Y/N)").upper() != "Y":
        print("[안내] 등록이 취소되었습니다.")
        return

    try:
        sample = ctx.sample_service.register(sample_id, name, avg_time, yield_rate)
        print(f"[완료] 시료 '{sample.sample_id} {sample.name}' 이(가) 등록되었습니다.")
    except DuplicateSampleIdError as e:
        print(f"[오류] 이미 존재하는 시료 ID입니다: {e}")


def _list_all(ctx: AppContext) -> None:
    samples = ctx.sample_service.get_all()
    _print_sample_table(f"시료 목록 (총 {len(samples)}건)", samples)
    input("\nEnter를 눌러 계속...")


def _search(ctx: AppContext) -> None:
    print_section("시료 검색")
    keyword = prompt("검색어 (이름 / ID)")
    results = ctx.sample_service.search(keyword)
    if not results:
        print("[안내] 검색 결과가 없습니다.")
    else:
        _print_sample_table(f"검색 결과 ({len(results)}건)", results)
    input("\nEnter를 눌러 계속...")


# ── 테이블 출력 ───────────────────────────────────────────
# 컬럼: ID(10) + 이름(20) + 평균생산시간(14) + 수율(6) + 재고(10) = 60

def _print_sample_table(title: str, samples) -> None:
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


def _fmt_time(minutes: float) -> str:
    return f"{minutes:.0f} min/ea"


def _fmt_stock(stock: int) -> str:
    return f"{stock} ea ⚠" if stock == 0 else f"{stock} ea"


# ── 등록 확인 ─────────────────────────────────────────────

def _print_registration_summary(
    sample_id: str, name: str, avg_time: float, yield_rate: float
) -> None:
    print_divider()
    print("  입력 내용 확인")
    print_divider()
    print(f"  시료 ID        : {sample_id}")
    print(f"  시료명         : {name}")
    print(f"  평균 생산시간  : {avg_time} min/ea")
    print(f"  수율           : {yield_rate} ({yield_rate * 100:.0f}%)")
    print_divider()


# ── 입력 헬퍼 ─────────────────────────────────────────────

def _input_sample_id() -> str:
    val = prompt("시료 ID     ")
    validate_non_empty(val, "시료 ID")
    validate_max_length(val, 20, "시료 ID")
    return val


def _input_name() -> str:
    val = prompt("시료명      ")
    validate_non_empty(val, "시료명")
    validate_max_length(val, 50, "시료명")
    return val


def _input_avg_production_time() -> float:
    return validate_positive_float(prompt("평균 생산시간 (min/ea)"), "평균 생산시간")


def _input_yield_rate() -> float:
    return validate_yield_rate(prompt("수율 (0.01 ~ 1.00)   "))
