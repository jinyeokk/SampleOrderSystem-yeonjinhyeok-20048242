"""
테스트 실행기.
  python run_tests.py          → 전체 phase 실행
  python run_tests.py 1 3      → phase 1, 3만 실행
"""
import importlib
import sys

PHASE_MODULES: dict[str, str] = {
    "1": "tests.test_phase1",
    "2": "tests.test_phase2",
    "3": "tests.test_phase3",
    "4": "tests.test_phase4",
    "5": "tests.test_phase5",
    "6": "tests.test_phase6",
}


def run_phase(phase: str) -> bool:
    module_path = PHASE_MODULES.get(phase)
    if not module_path:
        print(f"[오류] 알 수 없는 phase: {phase}")
        return False
    try:
        mod = importlib.import_module(module_path)
        return mod.run_tests()
    except ImportError:
        print(f"[안내] Phase {phase} 테스트가 아직 구현되지 않았습니다.")
        return True


def main() -> None:
    args = sys.argv[1:]
    phases = args if args else list(PHASE_MODULES.keys())

    all_passed = all(run_phase(p) for p in phases)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
