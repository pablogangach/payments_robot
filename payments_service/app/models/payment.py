from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    INTERNAL = "internal" # For testing or other providers

class Payment(BaseModel):
    id: str
    amount: float
    currency: str
    description: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime
    updated_at: datetime
    provider: Optional[PaymentProvider] = None
    provider_payment_id: Optional[str] = None

class PaymentCreate(BaseModel):
    amount: float
    currency: str
    provider: Optional[PaymentProvider] = None
    description: str = "Default Payment Description"
