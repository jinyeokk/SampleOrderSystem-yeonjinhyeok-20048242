"""경량 테스트 하네스 — 외부 의존성 없음."""
import sys
from typing import Callable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "") -> None:
        self.name = name
        self.passed = passed
        self.message = message


class TestHarness:
    def __init__(self, suite_name: str) -> None:
        self.suite_name = suite_name
        self._results: list[TestResult] = []

    def run(self, name: str, fn: Callable[[], None]) -> None:
        try:
            fn()
            self._results.append(TestResult(name, passed=True))
        except AssertionError as e:
            self._results.append(TestResult(name, passed=False, message=str(e)))
        except Exception as e:
            self._results.append(
                TestResult(name, passed=False, message=f"{type(e).__name__}: {e}")
            )

    def report(self) -> bool:
        passed = sum(1 for r in self._results if r.passed)
        total = len(self._results)
        bar = "─" * 50
        print(f"\n{bar}")
        print(f"  {self.suite_name}")
        print(bar)
        for r in self._results:
            mark = "✓" if r.passed else "✗"
            print(f"  {mark} {r.name}")
            if not r.passed:
                print(f"      → {r.message}")
        print(bar)
        print(f"  결과: {passed}/{total} 통과")
        print(f"{bar}\n")
        return passed == total


def assert_eq(actual, expected, msg: str = "") -> None:
    if actual != expected:
        label = f" ({msg})" if msg else ""
        raise AssertionError(f"기대값={expected!r}, 실제값={actual!r}{label}")


def assert_true(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "조건이 거짓입니다.")


def assert_raises(exc_type: type, fn: Callable, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"{exc_type.__name__} 예외가 발생해야 합니다.")
