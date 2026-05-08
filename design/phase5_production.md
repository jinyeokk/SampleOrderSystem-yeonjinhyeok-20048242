# Phase 5 : 생산라인 조회

## 1. 서브메뉴 화면

```
╔══════════════════════════════════════╗
║          생산라인 조회                ║
╠══════════════════════════════════════╣
║  1. 생산 중 목록                     ║
║  2. 생산 대기 큐                     ║
║  3. 생산 완료 처리                   ║
║  0. 메인 메뉴로 돌아가기             ║
╚══════════════════════════════════════╝
메뉴 선택 >> 
```

---

## 2. 기능 상세

### 2.1 생산 중 목록

- 상태가 `PRODUCING`인 주문 + 연결된 생산 큐 항목 표시

```
──────────────────────────────────────────────────────────────────────────
  현재 생산 중 목록 (총 2건)
──────────────────────────────────────────────────────────────────────────
 주문 ID              고객명        시료명          주문량  생산량  생산시간(예상)
──────────────────────────────────────────────────────────────────────────
 ORD-20260508-002    ABC전자       인화인듐 박막      20     27    3,240분
 ORD-20260508-004    XYZ소재       실리콘 기판        50     57    1,710분
──────────────────────────────────────────────────────────────────────────
```

| 컬럼 | 설명 |
|------|------|
| 주문량 | 고객이 요청한 수량 |
| 생산량 | 수율 보정 후 실제 생산 필요량 (`ceil(주문량 / yield_rate)`) |
| 생산시간(예상) | `생산량 × avg_production_time` |

---

### 2.2 생산 대기 큐

- 아직 승인되지 않았거나, 생산 대기 중인 큐 항목 (`WAITING` 상태)

```
──────────────────────────────────────────────────────────────
  생산 대기 큐 (총 3건)
──────────────────────────────────────────────────────────────
 순번  주문 ID              시료명          생산량  큐 등록일시
──────────────────────────────────────────────────────────────
   1   ORD-20260508-005    갈륨비소 웨이퍼    45    2026-05-08 10:11
   2   ORD-20260508-006    실리콘 기판         57    2026-05-08 11:33
   3   ORD-20260508-007    인화인듐 박막       27    2026-05-08 14:02
──────────────────────────────────────────────────────────────
```

- 순번은 큐 등록일시 오름차순 (먼저 등록된 것이 우선)

---

### 2.3 생산 완료 처리

생산이 끝난 주문을 `CONFIRMED`로 전환하고 재고에 반영한다.

#### 입력 흐름

```
──────────────────────────────────────
  생산 완료 처리
──────────────────────────────────────
주문 ID 입력 >> ORD-20260508-002

──────────────────────────────────────
  생산 완료 처리 확인
──────────────────────────────────────
  주문 ID    : ORD-20260508-002
  고객명     : ABC전자
  시료       : B-001 인화인듐 박막
  주문 수량  : 20 개
  생산 수량  : 27 개 (수율 75%)
  재고 변동  : 0개 + 27개 생산 → 주문 20개 차감 → 잔여 7개
──────────────────────────────────────
생산 완료 처리하시겠습니까? (Y/N) >> Y

[완료] 생산 완료 처리됨.
       상태: PRODUCING → CONFIRMED
       재고: 0 → 7 (27개 생산, 20개 출고 차감)
```

#### 생산 완료 처리 로직

```
생산 완료 흐름:
    1. 주문 상태 확인 (PRODUCING 아니면 오류)
    2. 생산 큐 항목 조회
    3. 재고 += required_qty  (생산된 전체 수량 추가)
    4. 재고 -= order.quantity (주문 수량 차감)
    5. 생산 큐 상태 → DONE
    6. 주문 상태 → CONFIRMED
```

#### 오류 케이스

| 오류 | 메시지 |
|------|--------|
| PRODUCING 아닌 주문 | `[오류] 생산 중 상태가 아닙니다. (현재: CONFIRMED)` |
| 존재하지 않는 주문 | `[오류] 해당 주문을 찾을 수 없습니다.` |

---

## 3. 데이터 흐름

```
production_menu.py
    │
    ▼
production_service
    ├─ get_in_progress()
    │   └─ order_repo.find_by_status(PRODUCING)
    │      + production_repo.get_by_order_ids()
    │
    ├─ get_waiting_queue()
    │   └─ production_repo.find_by_status(WAITING)
    │      .orderBy(queued_at ASC)
    │
    └─ complete_production(order_id)
        ├─ order_repo.get(order_id)
        ├─ production_repo.get_by_order(order_id)
        ├─ sample_repo.update_stock(+required_qty - order.quantity)
        ├─ production_repo.update_status(DONE)
        └─ order_repo.update_status(CONFIRMED)
```

---

## 4. ProductionQueue 모델

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

class QueueStatus(Enum):
    WAITING     = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE        = "DONE"

@dataclass
class ProductionQueue:
    queue_id: str
    order_id: str
    sample_id: str
    required_qty: int        # ceil(주문수량 / yield_rate)
    produced_qty: int = 0
    status: QueueStatus = QueueStatus.WAITING
    queued_at: datetime = field(default_factory=datetime.now)
```

---

## 5. 구현 체크리스트

- [ ] ProductionQueue 데이터 클래스 정의
- [ ] ProductionRepository (enqueue / 상태 조회 / 상태 변경)
- [ ] ProductionService
  - [ ] get_in_progress() : PRODUCING 주문 + 생산 큐 조인
  - [ ] get_waiting_queue() : WAITING 큐 목록 (큐 등록순)
  - [ ] complete_production(order_id) : 재고 보정 + 상태 전환
- [ ] production_menu.py (화면 입출력)
- [ ] 생산 중 목록 화면
- [ ] 생산 대기 큐 화면
- [ ] 생산 완료 처리 화면
