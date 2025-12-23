from pydantic import BaseModel
from typing import Optional
from payments_service.app.models.payment import PaymentProvider


class FeeStructure(BaseModel):
    provider: PaymentProvider
    card_network: Optional[str] = "default"  # e.g., 'visa', 'mastercard', 'amex'
    card_type: Optional[str] = "default"  # e.g., 'credit', 'debit'
    region: Optional[str] = "default"  # e.g., 'domestic', 'international'
    fixed_fee: float  # e.g., 0.30 for $0.30
    variable_fee_percent: float  # e.g., 2.9 for 2.9%