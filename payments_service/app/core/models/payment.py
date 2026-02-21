from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    ADYEN = "adyen"
    BRAINTREE = "braintree"
    INTERNAL = "internal" # For testing or other providers

import uuid

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    merchant_id: str
    customer_id: str
    amount: float
    currency: str
    description: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider: Optional[PaymentProvider] = None
    provider_payment_id: Optional[str] = None
    routing_decision: Optional[str] = None
    subscription_id: Optional[str] = None

class PaymentCreate(BaseModel):
    merchant_id: str
    customer_id: str
    amount: float
    currency: str
    description: str = "Default Payment Description"
    provider: Optional[PaymentProvider] = None
    subscription_id: Optional[str] = None
    
    # Internal fields for agentic routing context
    bin_metadata: Optional[Any] = None
    interchange_fees: Optional[list] = None
    provider_health: Optional[dict] = None
    payment_method: Optional[Any] = None # Added for BIN lookup in RoutingService
