#!/usr/bin/env python
"""더미 데이터 생성 도구 — 연결된 DB에 테스트용 데이터를 삽입한다.

실행:
    .venv/Scripts/python.exe tools/dummy_data.py
    .venv/Scripts/python.exe tools/dummy_data.py --samples 5 --orders 20 --seed 42
    .venv/Scripts/python.exe tools/dummy_data.py --reset
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import AppContext
from db.connection import DBConnection, DB_PATH
from db.schema import initialize_schema
from model.order import OrderStatus
from utils.display import TABLE_DIVIDER, TABLE_WIDTH

# ── 사전 정의 데이터 ──────────────────────────────────────

SAMPLE_PRESETS = [
    {"sample_id": "A-001", "name": "갈륨비소 웨이퍼",   "avg_time": 45.0,  "yield": 0.92, "stock": 120},
    {"sample_id": "A-002", "name": "실리콘 기판",        "avg_time": 30.0,  "yield": 0.88, "stock": 45},
    {"sample_id": "B-001", "name": "인화인듐 박막",      "avg_time": 120.0, "yield": 0.75, "stock": 0},
    {"sample_id": "B-002", "name": "질화갈륨 에피층",    "avg_time": 90.0,  "yield": 0.80, "stock": 30},
    {"sample_id": "C-001", "name": "산화인듐주석 필름",  "avg_time": 60.0,  "yield": 0.85, "stock": 15},
]

CUSTOMERS = [
    "(주)반도체코리아", "ABC전자", "XYZ소재",
    "테스트고객", "신성반도체", "(주)한국웨이퍼",
    "글로벌칩스", "나노소재(주)", "퓨처테크",
]

# 상태 분포: 총 N건에 비례 배분
_DISTRIBUTION = [
    (OrderStatus.RESERVED,  0.20),
    (OrderStatus.PRODUCING, 0.20),
    (OrderStatus.CONFIRMED, 0.27),
    (OrderStatus.RELEASE,   0.27),
    (OrderStatus.REJECTED,  0.07),  # 나머지
]


# ── 진입점 ────────────────────────────────────────────────

def main() -> None:
    args = _parse_args()

    conn = DBConnection.get()
    initialize_schema(conn)

    print("═" * TABLE_WIDTH)
    seed_label = f"seed: {args.seed}" if args.seed is not None else "seed: 없음"
    print(f"  더미 데이터 생성 도구  ({seed_label})")
    print("═" * TABLE_WIDTH)

    rng = random.Random(args.seed)

    # 1. 초기화
    if args.reset:
        _print_step(1, 4, "DB 초기화...")
        ctx = AppContext(conn)
        _reset(conn)
        print("완료")
    else:
        _print_step(1, 4, "DB 초기화...")
        print("건너뜀 (--reset 없음)")

    ctx = AppContext(conn)

    # 2. 시료 생성
    _print_step(2, 4, "시료 생성...")
    sample_ids = _generate_samples(ctx, args.samples, rng)
    print(f"{len(sample_ids)}종 삽입")

    # 3. 주문 생성
    _print_step(3, 4, "주문 생성...")
    orders = _generate_orders(ctx, args.orders, sample_ids, rng)
    print(f"{args.orders}건 생성")

    # 4. 상태 전이
    _print_step(4, 4, "상태 전이 적용...")
    results = _apply_transitions(ctx, orders, rng)
    print("완료")

    _print_summary(results, sample_ids, conn)


# ── 생성 로직 ─────────────────────────────────────────────

def _generate_samples(ctx: AppContext, n: int, rng: random.Random) -> list[str]:
    presets = SAMPLE_PRESETS[:n] if n <= len(SAMPLE_PRESETS) else SAMPLE_PRESETS
    ids = []
    for p in presets:
        if not ctx.sample_repo.exists(p["sample_id"]):
            ctx.sample_service.register(
                p["sample_id"], p["name"], p["avg_time"], p["yield"]
            )
            ctx.sample_repo.update_stock(p["sample_id"], p["stock"])
        ids.append(p["sample_id"])
    return ids


def _generate_orders(
    ctx: AppContext, n: int, sample_ids: list[str], rng: random.Random
) -> list[tuple]:
    """(order, desired_status) 쌍 목록 반환."""
    statuses = _build_status_list(n, rng)
    result   = []
    for desired in statuses:
        customer  = rng.choice(CUSTOMERS)
        sample_id = rng.choice(sample_ids)
        qty       = rng.randint(3, 15)
        order     = ctx.order_service.place_order(customer, sample_id, qty)
        result.append((order, desired))
    return result


def _apply_transitions(
    ctx: AppContext, orders: list[tuple], rng: random.Random
) -> dict[OrderStatus, int]:
    counts = {s: 0 for s in OrderStatus}

    for order, desired in orders:
        try:
            if desired == OrderStatus.RESERVED:
                pass

            elif desired == OrderStatus.CONFIRMED:
                _ensure_stock(ctx, order.sample_id, order.quantity)
                ctx.order_service.approve(order.order_id)

            elif desired == OrderStatus.PRODUCING:
                _drain_stock(ctx, order.sample_id)
                ctx.order_service.approve(order.order_id)

            elif desired == OrderStatus.RELEASE:
                _ensure_stock(ctx, order.sample_id, order.quantity)
                ctx.order_service.approve(order.order_id)
                ctx.release_service.release_one(order.order_id)

            elif desired == OrderStatus.REJECTED:
                ctx.order_service.reject(order.order_id)

        except Exception as e:
            print(f"  [경고] {order.order_id} 전이 실패 ({desired.value}): {e}")
            desired = OrderStatus.RESERVED   # fallback

        counts[desired] += 1

    return counts


# ── 재고 헬퍼 ─────────────────────────────────────────────

def _ensure_stock(ctx: AppContext, sample_id: str, needed: int) -> None:
    sample = ctx.sample_service.get(sample_id)
    if sample.stock < needed:
        ctx.sample_repo.update_stock(sample_id, needed - sample.stock)


def _drain_stock(ctx: AppContext, sample_id: str) -> None:
    sample = ctx.sample_service.get(sample_id)
    if sample.stock > 0:
        ctx.sample_repo.update_stock(sample_id, -sample.stock)


# ── 유틸 ─────────────────────────────────────────────────

def _build_status_list(n: int, rng: random.Random) -> list[OrderStatus]:
    counts  = {s: max(1, round(n * r)) for s, r in _DISTRIBUTION}
    total   = sum(counts.values())
    # 오버/언더 보정
    diff = n - total
    pivot = OrderStatus.RESERVED
    counts[pivot] = max(0, counts[pivot] + diff)

    result = []
    for status, cnt in counts.items():
        result.extend([status] * cnt)
    rng.shuffle(result)
    return result[:n]


def _reset(conn) -> None:
    conn.executescript("""
        DELETE FROM order_history;
        DELETE FROM production_queue;
        DELETE FROM orders;
        DELETE FROM samples;
    """)
    conn.commit()


def _print_step(current: int, total: int, label: str) -> None:
    print(f"[{current}/{total}] {label:<24}", end="", flush=True)


def _print_summary(
    results: dict[OrderStatus, int], sample_ids: list[str], conn
) -> None:
    total = sum(results.values())
    prod_q = len(conn.execute(
        "SELECT 1 FROM production_queue WHERE status != 'DONE'"
    ).fetchall())

    print()
    print(TABLE_DIVIDER)
    print("  생성 결과 요약")
    print(TABLE_DIVIDER)
    print(f"  시료      : {len(sample_ids):>3}종")
    print(f"  주문 (합) : {total:>3}건")
    for status, count in results.items():
        suffix = f"  (생산 큐 {prod_q}건 등록)" if status == OrderStatus.PRODUCING and prod_q else ""
        print(f"    {status.value:<10}: {count:>3}건{suffix}")
    print(TABLE_DIVIDER)
    print(f"DB 경로: {DB_PATH}")
    print("완료. 'python tools/admin_console.py' 로 데이터를 확인하세요.")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="더미 데이터 생성 도구")
    p.add_argument("--samples", type=int, default=3,   help="생성할 시료 수 (최대 5, 기본: 3)")
    p.add_argument("--orders",  type=int, default=15,  help="생성할 주문 수 (기본: 15)")
    p.add_argument("--seed",    type=int, default=None, help="난수 시드 (재현 가능한 데이터)")
    p.add_argument("--reset",   action="store_true",   help="기존 DB 데이터 초기화 후 생성")
    return p.parse_args()


if __name__ == "__main__":
    main()
