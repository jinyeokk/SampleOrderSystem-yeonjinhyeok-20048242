# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

반도체 시료 생산주문관리 시스템 — Python 콘솔 애플리케이션.  
시료 등록부터 주문 접수·승인·생산·출고까지 전 과정을 7개 Phase로 나눠 개발한다.

## 명령어

```bash
# 앱 실행
.venv/Scripts/python.exe main.py

# 특정 phase 테스트
.venv/Scripts/python.exe -m tests.test_phase0

# 전체 / 복수 phase 테스트
.venv/Scripts/python.exe run_tests.py
.venv/Scripts/python.exe run_tests.py 0 1 3
```

> Python은 반드시 `.venv/Scripts/python.exe`를 사용한다 (Windows venv).

## 아키텍처

```
model/ → repository/ → service/ → menu/
```

- **model/**: 순수 dataclass (Sample, Order, ProductionQueue). 외부 의존 없음.
- **repository/**: in-memory dict 저장소. 각 repo는 해당 모델만 책임진다.
- **service/**: 비즈니스 로직. repo와 다른 service를 생성자 주입으로 받는다.
- **menu/**: 콘솔 I/O만 담당. service 호출 후 결과 출력. 로직 없음.
- **app.py** (`AppContext`): 모든 repo·service를 한 곳에서 생성·연결하는 DI 컨테이너.
- **utils/display.py**: CJK 이중폭 보정(`display_width`, `ljust_display`, `center_display`), 박스 메뉴, 테이블 출력.
- **utils/validator.py**: 입력값 검증 함수 (ValueError 발생).
- **tests/harness.py**: 외부 라이브러리 없는 경량 테스트 하네스 (`TestHarness`, `assert_eq`, `assert_raises`).

### 의존성 흐름

```
AppContext
  ├─ SampleService(SampleRepository)
  ├─ OrderService(OrderRepository, ProductionRepository, SampleService)
  ├─ ProductionService(OrderService, OrderRepository, ProductionRepository, SampleService)
  ├─ ReleaseService(OrderService, OrderRepository)
  └─ MonitoringService(OrderRepository, SampleRepository, ProductionRepository)
```

### 주문 상태 전이

```
RESERVED → CONFIRMED  (승인, 재고 충분 → 재고 차감)
RESERVED → PRODUCING  (승인, 재고 부족 → 생산 큐 WAITING 등록)
RESERVED → REJECTED   (거절)
PRODUCING → CONFIRMED (생산 완료 → stock += required_qty - order.quantity)
CONFIRMED → RELEASE   (출고)
```

REJECTED는 모니터링 및 메인 현황 집계에서 제외된다.

## Git 브랜치 전략

| 브랜치 | 내용 |
|--------|------|
| `master` | 전체 infrastructure (model/repo/service/utils/harness/AppContext) |
| `phase/0-main-screen` | `menu/main_menu.py` 개편 (배너·현황 요약·종료 확인) + `tests/test_phase0.py` |
| `phase/1-sample-management` | `menu/sample_menu.py` + `tests/test_phase1.py` |
| `phase/2-order` | `menu/order_menu.py` + `tests/test_phase2.py` |
| `phase/3-approval` | `menu/approval_menu.py` + `tests/test_phase3.py` |
| `phase/4-monitoring` | `menu/monitoring_menu.py` + `tests/test_phase4.py` |
| `phase/5-production` | `menu/production_menu.py` + `tests/test_phase5.py` |
| `phase/6-release` | `menu/release_menu.py` + `tests/test_phase6.py` |

각 phase 브랜치는 이전 phase 브랜치에서 분기한다 (선형 이력).

## 테스트 작성 규칙

- 각 테스트 파일은 `run_tests() -> bool` 함수를 노출해야 한다.
- 메뉴(`menu/`)는 I/O 의존이므로 테스트하지 않는다 — service 계층만 테스트.
- 예외: `menu/main_menu.py`의 순수 로직 함수(`_collect_summary`, `_is_yes`)는 직접 임포트해 테스트한다.
- 테스트마다 독립적인 인스턴스를 생성한다 (`_make_ctx()` 또는 `_make_service()` 패턴).

## 주요 설계 결정

- **수율 보정**: `ceil(주문수량 / yield_rate)` → `Sample.required_production()`.
- **생산 완료 재고**: `stock += required_qty - order.quantity` (생산 후 주문 수량 즉시 차감).
- **주문 ID**: `ORD-{YYYYMMDD}-{NNN}` (당일 접수 건수 기반 순번).
- **메인 현황 요약**: 서브메뉴 복귀 시마다 재집계. REJECTED·RELEASE는 요약 2행에서 생략.
- **미구현 메뉴**: `ImportError`를 잡아 "[안내] 아직 구현되지 않았습니다." 출력.
- **Windows 출력**: `sys.stdout.reconfigure(encoding="utf-8")` — harness와 run_tests에 적용.
