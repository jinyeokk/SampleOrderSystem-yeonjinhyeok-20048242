import importlib
from datetime import datetime

from app import AppContext
from model.order import OrderStatus
from model.production import QueueStatus
from utils.display import TABLE_DIVIDER, TABLE_WIDTH, center_display, display_width, input_menu

_ROUTES: list[tuple[str, str, str]] = [
    ("1", "시료 관리",      "menu.sample_menu"),
    ("2", "시료 주문",      "menu.order_menu"),
    ("3", "주문 승인/거절", "menu.approval_menu"),
    ("4", "모니터링",       "menu.monitoring_menu"),
    ("5", "생산라인 조회",  "menu.production_menu"),
    ("6", "출고처리",       "menu.release_menu"),
    ("0", "종료",           ""),
]

_MONITORED_STATUSES = [
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASE,
]

_BANNER = "\n".join([
    "═" * TABLE_WIDTH,
    "  반도체 시료 생산주문관리 시스템 v1.0",
    "  초기화 완료. 시스템이 준비되었습니다.",
    "═" * TABLE_WIDTH,
])


def run(ctx: AppContext) -> None:
    print(_BANNER)
    while True:
        _print_summary(_collect_summary(ctx))
        items = [(key, label) for key, label, _ in _ROUTES]
        choice = input_menu("반도체 시료 생산주문관리 시스템", items)
        if choice == "0":
            if _confirm_exit():
                print("시스템을 종료합니다.")
                break
        else:
            _dispatch(choice, ctx)


# ── 현황 요약 ─────────────────────────────────────────────

def _collect_summary(ctx: AppContext) -> dict:
    samples = ctx.sample_repo.find_all()
    counts  = ctx.order_repo.count_by_status()
    waiting = ctx.production_repo.find_by_status(QueueStatus.WAITING)

    return {
        "sample_count": len(samples),
        "total_stock":  sum(s.stock for s in samples),
        "total_orders": sum(counts[s] for s in _MONITORED_STATUSES),
        "waiting_count": len(waiting),
        "reserved":  counts[OrderStatus.RESERVED],
        "producing": counts[OrderStatus.PRODUCING],
        "confirmed": counts[OrderStatus.CONFIRMED],
    }


def _print_summary(summary: dict) -> None:
    col = TABLE_WIDTH // 4   # 15 chars per column
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    title   = "  현황 요약"
    padding = TABLE_WIDTH - display_width(title) - len(now)

    headers = ["등록 시료", "총 재고", "전체 주문", "생산 대기"]
    values  = [
        f"{summary['sample_count']}종",
        f"{summary['total_stock']}개",
        f"{summary['total_orders']}건",
        f"{summary['waiting_count']}건",
    ]

    print(TABLE_DIVIDER)
    print(f"{title}{' ' * padding}{now}")
    print(TABLE_DIVIDER)
    print("".join(center_display(h, col) for h in headers))
    print("".join(center_display("─" * 10, col) for _ in headers))
    print("".join(center_display(v, col) for v in values))
    print(TABLE_DIVIDER)
    r, p, c = summary["reserved"], summary["producing"], summary["confirmed"]
    print(f"  RESERVED: {r}건   PRODUCING: {p}건   CONFIRMED: {c}건")
    print(TABLE_DIVIDER)


# ── 라우팅 / 종료 ─────────────────────────────────────────

def _dispatch(choice: str, ctx: AppContext) -> None:
    for key, label, module_path in _ROUTES:
        if choice != key or not module_path:
            continue
        try:
            mod = importlib.import_module(module_path)
            mod.run(ctx)
        except ImportError:
            print(f"[안내] '{label}' 메뉴는 아직 구현되지 않았습니다.")
            input("Enter를 눌러 계속...")
        return
    print("[오류] 유효하지 않은 선택입니다.")


def _confirm_exit() -> bool:
    answer = input("\n정말 종료하시겠습니까? (Y/N) >> ").strip()
    if _is_yes(answer):
        return True
    print("[안내] 계속 진행합니다.")
    return False


def _is_yes(answer: str) -> bool:
    return answer.lower() == "y"
