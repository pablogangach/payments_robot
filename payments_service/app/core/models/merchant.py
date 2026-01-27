from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid

class MerchantStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"

class BankingInfo(BaseModel):
    account_number: str
    routing_number: str

class MerchantBase(BaseModel):
    name: str
    email: str
    mcc: str
    country: str
    currency: str
    tax_id: str
    banking_info: Optional[BankingInfo] = None

class MerchantCreate(MerchantBase):
    pass

class Merchant(MerchantBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: MerchantStatus = MerchantStatus.ACTIVE
    api_key: str = Field(default_factory=lambda: f"pk_live_{str(uuid.uuid4())[:8]}")
