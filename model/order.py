from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderStatus(Enum):
    RESERVED  = "RESERVED"
    REJECTED  = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE   = "RELEASE"


@dataclass
class Order:
    order_id: str
    customer_name: str
    sample_id: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
    reject_reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    released_at: Optional[datetime] = None
