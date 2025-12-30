from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class ProcessorStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    REQUIRES_ACTION = "requires_action"

class InternalChargeRequest(BaseModel):
    """
    Standardized request format for any payment gateway adapter.
    """
    amount: float
    currency: str
    payment_method_token: str
    merchant_id: str
    customer_id: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InternalChargeResponse(BaseModel):
    """
    Standardized response from any payment gateway adapter.
    """
    status: ProcessorStatus
    processor_transaction_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)
