import math
from dataclasses import dataclass


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = 0

    def yield_percent(self) -> str:
        return f"{self.yield_rate * 100:.0f}%"

    def required_production(self, order_qty: int) -> int:
        return math.ceil(order_qty / self.yield_rate)
