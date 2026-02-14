from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

from enum import Enum

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    merchant_id: str
    amount: float
    currency: str
    next_renewal_at: datetime
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubscriptionCreate(BaseModel):
    customer_id: str
    merchant_id: str
    amount: float
    currency: str
    next_renewal_at: datetime
