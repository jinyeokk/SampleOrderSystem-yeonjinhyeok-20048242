3# Refactor R4 : 더미 데이터 생성 도구

## 1. 목적

R2(DB 연동) 완료 후 테스트 및 데모용 **현실적인 더미 데이터**를 생성하여 연결된 DB에 자동으로 삽입한다.  
시나리오 기반으로 전체 주문 흐름(RESERVED → CONFIRMED / PRODUCING → RELEASE)을 재현한다.

---

## 2. 실행 방법

```bash
# 기본 실행 (기본값으로 생성)
.venv/Scripts/python.exe tools/dummy_data.py

# 옵션 지정
.venv/Scripts/python.exe tools/dummy_data.py --samples 5 --orders 20 --seed 42

# DB 초기화 후 생성
.venv/Scripts/python.exe tools/dummy_data.py --reset
```

---

## 3. 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--samples N` | 3 | 생성할 시료 수 |
| `--orders N` | 15 | 생성할 주문 수 |
| `--seed N` | 없음 | 난수 시드 (재현 가능한 데이터) |
| `--reset` | False | 기존 DB 데이터 초기화 후 생성 |

---

## 4. 생성 데이터 사양

### 4.1 시료 데이터

```python
SAMPLE_PRESETS = [
    {"sample_id": "A-001", "name": "갈륨비소 웨이퍼",  "avg_time": 45.0,  "yield": 0.92, "stock": 120},
    {"sample_id": "A-002", "name": "실리콘 기판",       "avg_time": 30.0,  "yield": 0.88, "stock": 45},
    {"sample_id": "B-001", "name": "인화인듐 박막",     "avg_time": 120.0, "yield": 0.75, "stock": 0},
    {"sample_id": "B-002", "name": "질화갈륨 에피층",   "avg_time": 90.0,  "yield": 0.80, "stock": 30},
    {"sample_id": "C-001", "name": "산화인듐주석 필름", "avg_time": 60.0,  "yield": 0.85, "stock": 15},
]
```

### 4.2 주문 상태 분포 (기본 15건)

| 상태 | 비율 | 건수 |
|------|------|------|
| RESERVED | 20% | 3건 |
| PRODUCING | 20% | 3건 |
| CONFIRMED | 27% | 4건 |
| RELEASE | 27% | 4건 |
| REJECTED | 7% | 1건 |

### 4.3 고객명 풀

```python
CUSTOMERS = [
    "(주)반도체코리아", "ABC전자", "XYZ소재",
    "테스트고객", "신성반도체", "(주)한국웨이퍼",
    "글로벌칩스", "나노소재(주)", "퓨처테크",
]
```

---

## 5. 생성 시나리오

```
1. 시료 등록 (N종)
       ↓
2. 주문 생성 (RESERVED 상태)
       ↓
3. 상태 분포에 따라 상태 전이 적용
   ├─ CONFIRMED: approve() 호출 (재고 충분)
   ├─ PRODUCING: approve() 호출 (재고 부족) → 생산 큐 등록
   ├─ RELEASE:   approve() + release_one() 호출
   └─ REJECTED:  reject() 호출
       ↓
4. DB 커밋 및 결과 출력
```

---

## 6. 실행 결과 출력

```
════════════════════════════════════════════════════════════
  더미 데이터 생성 도구  (seed: 42)
════════════════════════════════════════════════════════════
[1/4] DB 초기화...       완료
[2/4] 시료 생성...       3종 삽입
[3/4] 주문 생성...       15건 생성
[4/4] 상태 전이 적용...  완료

────────────────────────────────────────────────────────────
  생성 결과 요약
────────────────────────────────────────────────────────────
  시료      :  3종
  주문 (합) : 15건
    RESERVED  :  3건
    PRODUCING :  3건  (생산 큐 3건 등록)
    CONFIRMED :  4건
    RELEASE   :  4건
    REJECTED  :  1건
────────────────────────────────────────────────────────────
DB 경로: data/semi.db
완료. 'python tools/admin_console.py' 로 데이터를 확인하세요.
```

---

## 7. 파일 구조

```
semi/
└── tools/
    ├── __init__.py
    ├── admin_console.py   # R3
    └── dummy_data.py      # 더미 데이터 생성 진입점
```

---

## 8. 구현 체크리스트

- [ ] `tools/dummy_data.py`
  - [ ] CLI 인수 파싱 (`argparse`: `--samples`, `--orders`, `--seed`, `--reset`)
  - [ ] `--reset` 옵션: 기존 데이터 삭제 후 재생성
  - [ ] 시료 프리셋 데이터 삽입
  - [ ] 주문 상태 분포에 따른 더미 주문 생성
  - [ ] 상태 전이 시나리오 실행 (service 계층 활용)
  - [ ] 생성 결과 요약 출력
  - [ ] `--seed` 옵션으로 재현 가능한 데이터 생성
  - [ ] R2 DB 연결 재사용 (`DBConnection.get()`)
