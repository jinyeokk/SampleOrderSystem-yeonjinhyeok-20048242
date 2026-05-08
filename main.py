from app import AppContext
from controller.main_controller import MainController


def main() -> None:
    ctx = AppContext()
    MainController(ctx).run()


if __name__ == "__main__":
    main()
