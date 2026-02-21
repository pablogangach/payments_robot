from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from payments_service.app.core.models.payment import PaymentProvider

class RawTransactionRecord(BaseModel):
    """
    Standardized internal representation of a single transaction's outcome
    ingested from external or internal sources.
    """
    provider: PaymentProvider
    payment_form: str  # e.g., "card_on_file", "apple_pay", "google_pay"
    processing_type: str  # e.g., "signature", "network_token", "pinless"
    amount: float
    currency: str
    status: str  # e.g., "succeeded", "failed", "declined"
    error_code: Optional[str] = None
    latency_ms: int
    bin: str  # first 6-8 digits
    card_type: str  # e.g., "credit", "debit"
    network: str  # e.g., "visa", "mastercard"
    region: str  # e.g., "domestic", "international"
    timestamp: datetime
    extra_fields: Dict[str, Any] = Field(default_factory=dict)
