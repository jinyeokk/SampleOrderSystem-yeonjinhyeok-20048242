from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QueueStatus(Enum):
    WAITING     = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE        = "DONE"


@dataclass
class ProductionQueue:
    queue_id: str
    order_id: str
    sample_id: str
    required_qty: int
    produced_qty: int = 0
    status: QueueStatus = QueueStatus.WAITING
    queued_at: datetime = field(default_factory=datetime.now)
