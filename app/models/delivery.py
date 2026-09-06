from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Outcome(str, Enum):
    DELIVERED = "delivered"
    PENDING = "pending"
    DEAD = "dead"


class DeliveryDetails(BaseModel):
    id: UUID
    event_type: str
    payload: dict
    attempt_count: int
    status: Outcome
    next_attempt_at: datetime


class DeliveryOut(BaseModel):
    count: int
    deliveries: list[DeliveryDetails]
