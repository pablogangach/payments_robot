from pydantic import BaseModel
from enum import Enum
from typing import Optional
from app.models.payment import PaymentProvider

class BillingType(str, Enum):
    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"

class Customer(BaseModel):
    id: str
    locale: str

class PaymentMethodDetails(BaseModel):
    type: str # e.g. "credit_card", "bank_transfer"
    # Placeholder for more details like issuing country, bin, etc.
    last4: Optional[str] = None 

class Product(BaseModel):
    id: str
    name: str

class PaymentContext(BaseModel):
    payment_method: PaymentMethodDetails
    customer: Customer
    product: Product
    billing_type: BillingType

class PaymentRoute(BaseModel):
    processor: PaymentProvider
    # Placeholder for more route details
    routing_reason: Optional[str] = None
