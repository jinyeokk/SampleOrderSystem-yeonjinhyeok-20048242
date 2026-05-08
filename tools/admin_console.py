#!/usr/bin/env python
"""관리자 콘솔 — DB에 저장된 데이터 실시간 조회 (읽기 전용).

실행:
    .venv/Scripts/python.exe tools/admin_console.py
"""
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import DBConnection, DB_PATH
from db.schema import initialize_schema
from model.order import OrderStatus
from model.production import QueueStatus
from repository.order_repo import OrderRepository
from repository.production_repo import ProductionRepository
from repository.sample_repo import SampleRepository
from utils.display import (
    TABLE_DIVIDER, TABLE_WIDTH,
    center_display, display_width,
    ljust_display, rjust_display,
)

_BANNER = "\n".join([
    "═" * TABLE_WIDTH,
    "  반도체 시료 생산주문관리 — 관리자 콘솔",
    f"  DB: {DB_PATH}",
    "═" * TABLE_WIDTH,
])

_HELP = """
명령어 목록:
  stats              현황 요약 (주문 건수 + 재고)
  samples            전체 시료 목록
  orders [STATUS]    주문 목록 (선택: RESERVED/PRODUCING/CONFIRMED/RELEASE/REJECTED)
  order <ID>         주문 단건 상세
  queue              생산 큐 전체 조회
  history [N]        최근 N건 주문 이력 (기본: 10)
  help               이 도움말
  exit / quit        종료
"""


@dataclass
class Repos:
    samples:    SampleRepository
    orders:     OrderRepository
    production: ProductionRepository


# ── 진입점 ────────────────────────────────────────────────

def main() -> None:
    try:
        conn = DBConnection.get()
        initialize_schema(conn)
    except Exception as e:
        print(f"[오류] DB 연결 실패: {e}")
        sys.exit(1)

    repos = Repos(
        samples=SampleRepository(conn),
        orders=OrderRepository(conn),
        production=ProductionRepository(conn),
    )

    print(_BANNER)
    print("  [안내] 읽기 전용 모드. 데이터 변경 명령은 지원하지 않습니다.")
    print("  명령어를 입력하세요. (help: 도움말, exit: 종료)")

    while True:
        try:
            line = input("\nadmin >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not line:
            continue

        cmd, args = _parse(line)

        if cmd in ("exit", "quit"):
            print("종료합니다.")
            break
        elif cmd == "help":
            print(_HELP)
        elif cmd == "stats":
            cmd_stats(repos)
        elif cmd == "samples":
            cmd_samples(repos)
        elif cmd == "orders":
            cmd_orders(repos, args[0].upper() if args else None)
        elif cmd == "order":
            cmd_order(repos, args[0] if args else "")
        elif cmd == "queue":
            cmd_queue(repos)
        elif cmd == "history":
            limit = int(args[0]) if args and args[0].isdigit() else 10
            cmd_history(repos, limit)
        else:
            print(f"[오류] 알 수 없는 명령어: '{cmd}'  (help 로 도움말 확인)")


def _parse(line: str) -> tuple[str, list[str]]:
    parts = line.split()
    return parts[0].lower(), parts[1:]


# ── 명령어 핸들러 ─────────────────────────────────────────

def cmd_stats(repos: Repos) -> None:
    now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    samples = repos.samples.find_all()
    counts  = repos.orders.count_by_status()
    waiting = repos.production.find_by_status(QueueStatus.WAITING)

    total_stock   = sum(s.stock for s in samples)
    total_orders  = sum(counts[s] for s in [
        OrderStatus.RESERVED, OrderStatus.PRODUCING,
        OrderStatus.CONFIRMED, OrderStatus.RELEASE,
    ])

    title   = "  현황 요약"
    padding = TABLE_WIDTH - display_width(title) - len(now)

    print(TABLE_DIVIDER)
    print(f"{title}{' ' * padding}{now}")
    print(TABLE_DIVIDER)
    print(f"  등록 시료  : {len(samples):>4}종       총 재고    : {total_stock:>6} ea")
    print(f"  전체 주문  : {total_orders:>4}건       생산 대기  : {len(waiting):>6}건")
    print(TABLE_DIVIDER)
    r = counts[OrderStatus.RESERVED]
    p = counts[OrderStatus.PRODUCING]
    c = counts[OrderStatus.CONFIRMED]
    rl = counts[OrderStatus.RELEASE]
    rj = counts[OrderStatus.REJECTED]
    print(
        f"  RESERVED:{r:>3}건  PRODUCING:{p:>3}건  "
        f"CONFIRMED:{c:>3}건  RELEASE:{rl:>3}건  REJECTED:{rj:>3}건"
    )
    print(TABLE_DIVIDER)


def cmd_samples(repos: Repos) -> None:
    samples = repos.samples.find_all()
    print(TABLE_DIVIDER)
    print(f"  시료 목록 (총 {len(samples)}건)")
    print(TABLE_DIVIDER)
    print(
        f" {'시료 ID':<10}{ljust_display('시료명', 18)}"
        f"{'생산시간':>12}{'수율':>6}{'현재 재고':>10}"
    )
    print(TABLE_DIVIDER)
    for s in samples:
        stock_str = f"{s.stock} ea ⚠" if s.stock == 0 else f"{s.stock} ea"
        print(
            f" {s.sample_id:<10}{ljust_display(s.name, 18)}"
            f"{f'{s.avg_production_time:.0f} min/ea':>12}"
            f"{s.yield_percent():>6}"
            f"{stock_str:>10}"
        )
    print(TABLE_DIVIDER)


def cmd_orders(repos: Repos, status_filter: str | None) -> None:
    if status_filter:
        try:
            status = OrderStatus(status_filter)
            orders = repos.orders.find_by_status(status)
            title  = f"주문 목록 — {status.value} (총 {len(orders)}건)"
        except ValueError:
            valid = ", ".join(s.value for s in OrderStatus)
            print(f"[오류] 유효하지 않은 상태: '{status_filter}'\n  유효값: {valid}")
            return
    else:
        orders = repos.orders.find_all()
        title  = f"주문 목록 (총 {len(orders)}건)"

    # Build sample name map
    sample_map = {s.sample_id: s.name for s in repos.samples.find_all()}

    print(TABLE_DIVIDER)
    print(f"  {title}")
    print(TABLE_DIVIDER)
    print(
        f" {'주문 번호':<20}{ljust_display('고객명', 16)}"
        f"{ljust_display('시료명', 14)}{'수량':>6}  {'상태'}"
    )
    print(TABLE_DIVIDER)
    for o in orders:
        sample_name = sample_map.get(o.sample_id, o.sample_id)
        print(
            f" {o.order_id:<20}{ljust_display(o.customer_name, 16)}"
            f"{ljust_display(sample_name, 14)}{o.quantity:>4} ea"
            f"  {o.status.value}"
        )
    print(TABLE_DIVIDER)


def cmd_order(repos: Repos, order_id: str) -> None:
    if not order_id:
        print("[오류] 주문 ID를 입력하세요.  예) order ORD-20260508-001")
        return

    order = repos.orders.find_by_id(order_id)
    if not order:
        print(f"[오류] 해당 주문을 찾을 수 없습니다: {order_id}")
        return

    sample      = repos.samples.find_by_id(order.sample_id)
    sample_name = sample.name if sample else "-"

    print(TABLE_DIVIDER)
    print(f"  주문 상세 — {order.order_id}")
    print(TABLE_DIVIDER)
    print(f"  상태      : {order.status.value}")
    print(f"  고객명    : {order.customer_name}")
    print(f"  시료      : {sample_name} ({order.sample_id})")
    print(f"  주문 수량 : {order.quantity} ea")
    print(f"  현재 재고 : {sample.stock} ea" if sample else "  현재 재고 : -")
    print(f"  접수일시  : {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  최종 변경 : {order.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if order.reject_reason:
        print(f"  거절 사유 : {order.reject_reason}")
    if order.released_at:
        print(f"  출고 일시 : {order.released_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(TABLE_DIVIDER)


def cmd_queue(repos: Repos) -> None:
    sample_map = {s.sample_id: s.name for s in repos.samples.find_all()}
    queues     = (
        repos.production.find_by_status(QueueStatus.WAITING)
        + repos.production.find_by_status(QueueStatus.IN_PROGRESS)
        + repos.production.find_by_status(QueueStatus.DONE)
    )

    print(TABLE_DIVIDER)
    print(f"  생산 큐 (총 {len(queues)}건)")
    print(TABLE_DIVIDER)
    print(
        f" {'큐 ID':<10}{ljust_display('주문 번호', 20)}"
        f"{ljust_display('시료명', 16)}{'실생산량':>8}{'상태':>12}  등록일시"
    )
    print(TABLE_DIVIDER)
    for q in queues:
        sample_name = sample_map.get(q.sample_id, q.sample_id)
        dt_str      = q.queued_at.strftime("%m-%d %H:%M")
        print(
            f" {q.queue_id:<10}{q.order_id:<20}"
            f"{ljust_display(sample_name, 16)}"
            f"{f'{q.required_qty} ea':>8}"
            f"{q.status.value:>12}"
            f"  {dt_str}"
        )
    if not queues:
        print("  [안내] 생산 큐가 비어 있습니다.")
    print(TABLE_DIVIDER)


def cmd_history(repos: Repos, limit: int) -> None:
    history = repos.orders.get_recent_history(limit)
    print(TABLE_DIVIDER)
    print(f"  최근 주문 이력 ({len(history)}건)")
    print(TABLE_DIVIDER)
    print(f" {'시각':<20}{'주문 번호':<22}내용")
    print(TABLE_DIVIDER)
    for h in history:
        ts = h["changed_at"].strftime("%Y-%m-%d %H:%M:%S")
        print(f" {ts:<20}{h['order_id']:<22}{h['description']}")
    if not history:
        print("  [안내] 이력이 없습니다.")
    print(TABLE_DIVIDER)


if __name__ == "__main__":
    main()
