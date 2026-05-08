from app import AppContext
from menu import main_menu


def main() -> None:
    ctx = AppContext()
    main_menu.run(ctx)


if __name__ == "__main__":
    main()
