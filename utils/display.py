import unicodedata

TABLE_WIDTH = 60
TABLE_DIVIDER = "─" * TABLE_WIDTH
MENU_INNER = 38


def display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in text)


def ljust_display(text: str, width: int, fill: str = " ") -> str:
    pad = max(0, width - display_width(text))
    return text + fill * pad


def center_display(text: str, width: int, fill: str = " ") -> str:
    pad = max(0, width - display_width(text))
    left = pad // 2
    return fill * left + text + fill * (pad - left)


def print_divider() -> None:
    print(TABLE_DIVIDER)


def print_section(title: str) -> None:
    print(TABLE_DIVIDER)
    print(f"  {title}")
    print(TABLE_DIVIDER)


def print_box_menu(title: str, items: list[tuple[str, str]]) -> None:
    border = "═" * MENU_INNER
    print(f"╔{border}╗")
    print(f"║{center_display(title, MENU_INNER)}║")
    print(f"╠{border}╣")
    for key, label in items:
        line = f"  {key}. {label}"
        print(f"║{ljust_display(line, MENU_INNER)}║")
    print(f"╚{border}╝")


def input_menu(title: str, items: list[tuple[str, str]]) -> str:
    print_box_menu(title, items)
    return input("메뉴 선택 >> ").strip()


def prompt(label: str) -> str:
    return input(f"{label} >> ").strip()


def fmt_production_time(minutes: float) -> str:
    m = int(minutes)
    if m < 60:
        return f"{m}분"
    h, r = divmod(m, 60)
    return f"{h}시간 {r}분" if r else f"{h}시간"


def fmt_stock(stock: int) -> str:
    return f"{stock} ⚠" if stock == 0 else str(stock)
