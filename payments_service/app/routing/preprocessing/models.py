from pydantic import BaseModel
from enum import Enum
from typing import Optional
from payments_service.app.core.models.payment import PaymentProvider

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

class FeeStructure(BaseModel):
    provider: PaymentProvider
    card_network: Optional[str] = "default"  # e.g., 'visa', 'mastercard', 'amex'
    card_type: Optional[str] = "default"  # e.g., 'credit', 'debit'
    region: Optional[str] = "default"  # e.g., 'domestic', 'international'
    fixed_fee: float  # e.g., 0.30 for $0.30
    variable_fee_percent: float  # e.g., 2.9 for 2.9%
