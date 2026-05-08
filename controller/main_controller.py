from datetime import datetime

from app import AppContext
from model.order import OrderStatus
from model.production import QueueStatus
from utils.display import TABLE_DIVIDER, TABLE_WIDTH, center_display, display_width, print_box_menu

_BANNER = "\n".join([
    "═" * TABLE_WIDTH,
    "  반도체 시료 생산주문관리 시스템 v1.0",
    "  초기화 완료. 시스템이 준비되었습니다.",
    "═" * TABLE_WIDTH,
])

_MONITORED_STATUSES = [
    OrderStatus.RESERVED,
    OrderStatus.PRODUCING,
    OrderStatus.CONFIRMED,
    OrderStatus.RELEASE,
]

_MENU_ITEMS = [
    ("1", "시료 관리"),
    ("2", "시료 주문"),
    ("3", "주문 승인/거절"),
    ("4", "모니터링"),
    ("5", "생산라인 조회"),
    ("6", "출고처리"),
    ("0", "종료"),
]


class MainController:

    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._routes = {
            "1": self._run_sample,
            "2": self._run_order,
            "3": self._run_approval,
            "4": self._run_monitoring,
            "5": self._run_production,
            "6": self._run_release,
        }

    def run(self) -> None:
        print(_BANNER)
        while True:
            _print_summary(_collect_summary(self._ctx))
            print_box_menu("반도체 시료 생산주문관리 시스템", _MENU_ITEMS)
            choice = input("메뉴 선택 >> ").strip()
            if choice == "0":
                if _confirm_exit():
                    print("시스템을 종료합니다.")
                    break
            elif choice in self._routes:
                self._routes[choice]()
            else:
                print("[오류] 유효하지 않은 선택입니다.")

    # ── 서브 컨트롤러 실행 ────────────────────────────────

    def _run_sample(self) -> None:
        from controller.sample_controller import SampleController
        from view.sample_view import SampleView
        SampleController(self._ctx, SampleView()).run()

    def _run_order(self) -> None:
        from controller.order_controller import OrderController
        from view.order_view import OrderView
        OrderController(self._ctx, OrderView()).run()

    def _run_approval(self) -> None:
        from controller.approval_controller import ApprovalController
        from view.approval_view import ApprovalView
        ApprovalController(self._ctx, ApprovalView()).run()

    def _run_monitoring(self) -> None:
        from controller.monitoring_controller import MonitoringController
        from view.monitoring_view import MonitoringView
        MonitoringController(self._ctx, MonitoringView()).run()

    def _run_production(self) -> None:
        from controller.production_controller import ProductionController
        from view.production_view import ProductionView
        ProductionController(self._ctx, ProductionView()).run()

    def _run_release(self) -> None:
        from controller.release_controller import ReleaseController
        from view.release_view import ReleaseView
        ReleaseController(self._ctx, ReleaseView()).run()


# ── 현황 요약 (테스트 가능하도록 모듈 수준 함수로 노출) ────

def _collect_summary(ctx: AppContext) -> dict:
    samples = ctx.sample_repo.find_all()
    counts  = ctx.order_repo.count_by_status()
    waiting = ctx.production_repo.find_by_status(QueueStatus.WAITING)

    return {
        "sample_count":  len(samples),
        "total_stock":   sum(s.stock for s in samples),
        "total_orders":  sum(counts[s] for s in _MONITORED_STATUSES),
        "waiting_count": len(waiting),
        "reserved":      counts[OrderStatus.RESERVED],
        "producing":     counts[OrderStatus.PRODUCING],
        "confirmed":     counts[OrderStatus.CONFIRMED],
    }


def _print_summary(summary: dict) -> None:
    col  = TABLE_WIDTH // 4
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


def _confirm_exit() -> bool:
    answer = input("\n정말 종료하시겠습니까? (Y/N) >> ").strip()
    if _is_yes(answer):
        return True
    print("[안내] 계속 진행합니다.")
    return False


def _is_yes(answer: str) -> bool:
    return answer.lower() == "y"
