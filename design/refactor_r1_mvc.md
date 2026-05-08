# Refactor R1 : MVC 구조 전환

## 1. 목적

현재 `menu/*.py`에 혼재된 **입력 처리(Controller)**와 **출력 렌더링(View)** 역할을 분리한다.  
서비스 계층(Model)은 변경하지 않고, 프레젠테이션 계층만 구조화한다.

---

## 2. 현재 구조 vs MVC 구조

### 현재 (menu/ 혼합)

```
menu/sample_menu.py
    ├─ input()         ← Controller 역할
    ├─ service 호출    ← Controller 역할
    └─ print()         ← View 역할
```

### MVC 전환 후

```
Controller                Service (Model)            View
──────────                ───────────────            ────
sample_controller.py  →   sample_service.py  →  sample_view.py
    input() 처리               비즈니스 로직          print() 렌더링
    service 호출               (변경 없음)            데이터만 받아 출력
    view 호출
```

---

## 3. 디렉토리 구조

```
semi/
├── model/          # 변경 없음
├── repository/     # 변경 없음
├── service/        # 변경 없음
├── utils/          # 변경 없음
├── controller/     # NEW: 입력 처리 + 라우팅
│   ├── __init__.py
│   ├── main_controller.py
│   ├── sample_controller.py
│   ├── order_controller.py
│   ├── approval_controller.py
│   ├── monitoring_controller.py
│   ├── production_controller.py
│   └── release_controller.py
├── view/           # NEW: 콘솔 출력 전담
│   ├── __init__.py
│   ├── base_view.py           # 공통 출력 유틸 (테이블, 박스 메뉴 등)
│   ├── sample_view.py
│   ├── order_view.py
│   ├── approval_view.py
│   ├── monitoring_view.py
│   ├── production_view.py
│   └── release_view.py
└── menu/           # DEPRECATED: 전환 완료 후 제거
```

---

## 4. 역할 정의

| 계층 | 책임 | 금지 사항 |
|------|------|-----------|
| **Controller** | `input()` 수신, 유효성 검증, service 호출, view 호출 | `print()` 직접 호출 금지 |
| **View** | 데이터를 받아 `print()` 출력 | `input()`, service 호출 금지 |
| **Service (Model)** | 비즈니스 로직 | UI 관련 코드 금지 |

---

## 5. 변환 예시 — 시료 등록

### 현재 (menu/sample_menu.py)

```python
def _register(ctx: AppContext) -> None:
    print_section("시료 등록")          # View
    val = prompt("시료 ID")             # Controller
    sample = ctx.sample_service.register(...)  # Controller
    print(f"[완료] ...")                # View
```

### MVC 전환 후

```python
# controller/sample_controller.py
def register(ctx: AppContext, view: SampleView) -> None:
    view.show_register_form()           # View 호출
    try:
        sample_id = input("시료 ID >> ").strip()
        # ... 입력 수집
        sample = ctx.sample_service.register(sample_id, ...)
        view.show_register_success(sample)
    except (ValueError, DuplicateSampleIdError) as e:
        view.show_error(str(e))

# view/sample_view.py
class SampleView:
    def show_register_form(self) -> None:
        print_section("시료 등록")

    def show_register_success(self, sample: Sample) -> None:
        print(f"[완료] 시료 '{sample.sample_id} {sample.name}' 등록 완료.")

    def show_error(self, msg: str) -> None:
        print(f"[오류] {msg}")
```

---

## 6. main.py 변경

```python
# 현재
from menu import main_menu
main_menu.run(ctx)

# MVC 전환 후
from controller.main_controller import MainController
MainController(ctx).run()
```

---

## 7. 구현 체크리스트

- [ ] `view/base_view.py` — 공통 출력 메서드 (테이블, 박스, 메시지 등)
- [ ] `view/sample_view.py` ~ `view/release_view.py` — 각 도메인 View
- [ ] `controller/sample_controller.py` ~ `controller/release_controller.py`
- [ ] `controller/main_controller.py` — 라우팅 및 메뉴 루프
- [ ] `main.py` 진입점 변경
- [ ] 기존 `menu/*.py` 삭제
- [ ] 전체 테스트 60/60 통과 확인
