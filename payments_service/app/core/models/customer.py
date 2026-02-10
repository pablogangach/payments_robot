from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime, timezone
import uuid

class CustomerBase(BaseModel):
    merchant_id: str
    name: Optional[str] = None
    email: str
    payment_method_token: str # Represents a vaulted token (e.g. pm_123 or tok_123)

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
