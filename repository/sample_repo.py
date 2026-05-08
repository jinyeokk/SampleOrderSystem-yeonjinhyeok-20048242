import sqlite3
from typing import Optional

from model.sample import Sample


class SampleRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, sample: Sample) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO samples VALUES (?, ?, ?, ?, ?)",
            (sample.sample_id, sample.name,
             sample.avg_production_time, sample.yield_rate, sample.stock),
        )
        self._conn.commit()

    def find_by_id(self, sample_id: str) -> Optional[Sample]:
        row = self._conn.execute(
            "SELECT * FROM samples WHERE sample_id = ?", (sample_id,)
        ).fetchone()
        return _to_sample(row) if row else None

    def find_all(self) -> list[Sample]:
        rows = self._conn.execute(
            "SELECT * FROM samples ORDER BY sample_id"
        ).fetchall()
        return [_to_sample(r) for r in rows]

    def exists(self, sample_id: str) -> bool:
        return self._conn.execute(
            "SELECT 1 FROM samples WHERE sample_id = ?", (sample_id,)
        ).fetchone() is not None

    def update_stock(self, sample_id: str, delta: int) -> None:
        self._conn.execute(
            "UPDATE samples SET stock = stock + ? WHERE sample_id = ?",
            (delta, sample_id),
        )
        self._conn.commit()


def _to_sample(row) -> Sample:
    return Sample(
        sample_id=row["sample_id"],
        name=row["name"],
        avg_production_time=row["avg_production_time"],
        yield_rate=row["yield_rate"],
        stock=row["stock"],
    )
