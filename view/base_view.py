"""공통 View 메서드 — 모든 View가 상속한다."""
from utils.display import TABLE_DIVIDER, print_box_menu, print_section


class BaseView:

    # ── 메시지 출력 ───────────────────────────────────────

    def error(self, msg: str) -> None:
        print(f"[오류] {msg}")

    def success(self, msg: str) -> None:
        print(f"[완료] {msg}")

    def info(self, msg: str) -> None:
        print(f"[안내] {msg}")

    def divider(self) -> None:
        print(TABLE_DIVIDER)

    def section(self, title: str) -> None:
        print_section(title)

    # ── 입력 수집 ─────────────────────────────────────────

    def get_input(self, prompt: str) -> str:
        return input(f"{prompt} >> ").strip()

    def confirm(self, prompt: str) -> bool:
        return input(f"{prompt} >> ").strip().upper() == "Y"

    def wait(self) -> None:
        input("\nEnter를 눌러 계속...")

    def show_menu(self, title: str, items: list[tuple[str, str]]) -> str:
        print_box_menu(title, items)
        return input("메뉴 선택 >> ").strip()
