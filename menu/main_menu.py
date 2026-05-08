import importlib

from app import AppContext
from utils.display import input_menu

_ROUTES: list[tuple[str, str, str]] = [
    ("1", "시료 관리",      "menu.sample_menu"),
    ("2", "시료 주문",      "menu.order_menu"),
    ("3", "주문 승인/거절", "menu.approval_menu"),
    ("4", "모니터링",       "menu.monitoring_menu"),
    ("5", "생산라인 조회",  "menu.production_menu"),
    ("6", "출고처리",       "menu.release_menu"),
    ("0", "종료",           ""),
]


def run(ctx: AppContext) -> None:
    while True:
        items = [(key, label) for key, label, _ in _ROUTES]
        choice = input_menu("반도체 시료 생산주문관리 시스템", items)
        if choice == "0":
            print("시스템을 종료합니다.")
            break
        _dispatch(choice, ctx)


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
