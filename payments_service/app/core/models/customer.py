from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid

class CustomerBase(BaseModel):
    merchant_id: str
    name: str
    email: str
    payment_method_token: str # Represents a vaulted token (e.g. pm_123 or tok_123)

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: "2024-01-01T00:00:00Z") # detailed timestamp in real app
