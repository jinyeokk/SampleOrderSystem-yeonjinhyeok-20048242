# 콘솔 애플리케이션 전체 설계

## 1. 애플리케이션 구조

```
semi/
├── main.py                  # 진입점, 메인 루프
├── menu/
│   ├── main_menu.py         # 메인 메뉴 라우터
│   ├── sample_menu.py       # Phase 1 : 시료 관리
│   ├── order_menu.py        # Phase 2 : 시료 주문
│   ├── approval_menu.py     # Phase 3 : 주문 승인/거절
│   ├── monitoring_menu.py   # Phase 4 : 모니터링
│   ├── production_menu.py   # Phase 5 : 생산라인 조회
│   └── release_menu.py      # Phase 6 : 출고처리
├── service/
│   ├── sample_service.py
│   ├── order_service.py
│   ├── production_service.py
│   └── release_service.py
├── repository/
│   ├── sample_repo.py
│   ├── order_repo.py
│   └── production_repo.py
├── model/
│   ├── sample.py
│   ├── order.py
│   └── production.py
└── utils/
    ├── display.py           # 테이블 출력, 구분선 등 공통 UI
    └── validator.py         # 입력값 검증
```

---

## 2. 데이터 모델

### Sample (시료)

| 필드 | 타입 | 설명 | 제약 |
|------|------|------|------|
| `sample_id` | str | 시료 고유 ID | 고유값, 필수 |
| `name` | str | 시료명 | 필수 |
| `avg_production_time` | float | 평균 생산 시간 (분/개) | > 0 |
| `yield_rate` | float | 수율 (0.0 ~ 1.0) | 0 < yield_rate ≤ 1 |
| `stock` | int | 현재 재고 수량 | ≥ 0 |

> **수율(yield_rate)** : 정상 시료 수 / 총 생산 시료 수  
> 예) 100개 생산 → 정상 90개 → yield_rate = 0.9  
> 필요 생산량 계산 : `ceil(주문수량 / yield_rate)`

### Order (주문)

| 필드 | 타입 | 설명 |
|------|------|------|
| `order_id` | str | 주문 고유 ID (자동 생성) |
| `customer_name` | str | 고객명 |
| `sample_id` | str | 시료 FK |
| `quantity` | int | 주문 수량 |
| `status` | enum | `RESERVED` \| `REJECTED` \| `PRODUCING` \| `CONFIRMED` \| `RELEASE` |
| `reject_reason` | str? | 거절 사유 |
| `created_at` | datetime | 주문 접수일시 |
| `updated_at` | datetime | 최종 상태 변경일시 |

### ProductionQueue (생산 큐)

| 필드 | 타입 | 설명 |
|------|------|------|
| `queue_id` | str | 큐 항목 ID |
| `order_id` | str | 연결 주문 ID |
| `sample_id` | str | 시료 ID |
| `required_qty` | int | 실제 생산 필요량 (수율 보정 후) |
| `produced_qty` | int | 현재까지 생산된 수량 |
| `status` | enum | `WAITING` \| `IN_PROGRESS` \| `DONE` |
| `queued_at` | datetime | 큐 등록일시 |

---

## 3. 주문 상태 전이

```
                  [재고 충분]
RESERVED ──────────────────────► CONFIRMED ──► RELEASE
         │                                      ▲
         │ [재고 부족]                           │
         └──────────────► PRODUCING ────────────┘
         │
         │ [거절]
         └──────────────► REJECTED  (모니터링 제외)
```

### 상태 전이 규칙 요약

| 현재 상태 | 액션 | 조건 | 다음 상태 |
|-----------|------|------|-----------|
| `RESERVED` | 승인 | 재고 ≥ 주문수량 | `CONFIRMED` |
| `RESERVED` | 승인 | 재고 < 주문수량 | `PRODUCING` |
| `RESERVED` | 거절 | - | `REJECTED` |
| `PRODUCING` | 생산 완료 | - | `CONFIRMED` |
| `CONFIRMED` | 출고 처리 | - | `RELEASE` |

---

## 4. 메인 메뉴 화면

```
╔══════════════════════════════════════╗
║   반도체 시료 생산주문관리 시스템     ║
╠══════════════════════════════════════╣
║  1. 시료 관리                        ║
║  2. 시료 주문                        ║
║  3. 주문 승인/거절                   ║
║  4. 모니터링                         ║
║  5. 생산라인 조회                    ║
║  6. 출고처리                         ║
║  0. 종료                             ║
╚══════════════════════════════════════╝
메뉴 선택 >> 
```

---

## 5. 공통 UI 규칙

| 규칙 | 내용 |
|------|------|
| 화면 너비 | 고정 60자 |
| 구분선 | `─` (U+2500) 60개 |
| 테이블 헤더 | 대문자, 구분선으로 분리 |
| 오류 메시지 | `[오류] ...` 접두사 |
| 성공 메시지 | `[완료] ...` 접두사 |
| 취소 | 빈 입력 Enter → 상위 메뉴로 복귀 |
| 뒤로가기 | `0` 입력 → 상위 메뉴 |

---

## 6. Phase 개발 순서

| Phase | 메뉴 | 선행 의존성 |
|-------|------|-------------|
| Phase 1 | 시료 관리 | 없음 |
| Phase 2 | 시료 주문 | Phase 1 |
| Phase 3 | 주문 승인/거절 | Phase 2 |
| Phase 4 | 모니터링 | Phase 1, 2, 3 |
| Phase 5 | 생산라인 조회 | Phase 3 |
| Phase 6 | 출고처리 | Phase 3 |
