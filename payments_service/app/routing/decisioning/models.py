from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict, List
from payments_service.app.core.models.payment import PaymentProvider

class RoutingStrategy(str, Enum):
    LOWEST_COST = "lowest_cost"
    HIGHEST_SUCCESS_RATE = "highest_success_rate"
    HYBRID = "hybrid"

class RoutingDimension(BaseModel):
    """
    Represents the specific slice of traffic context for looking up performance data.
    """
    payment_method_type: str  # e.g., "credit_card"
    payment_form: str = "card_on_file" # e.g., "card_on_file", "apple_pay", "google_pay"
    network: str = "unknown" # e.g., "visa", "mastercard"
    card_type: str = "unknown" # e.g., "credit", "debit"
    region: str = "domestic" # e.g., "domestic", "international"
    currency: str = "USD"
    is_network_tokenized: bool = False

    class Config:
        frozen = True # Make it hashable so it can be used as a key if needed

class CostStructure(BaseModel):
    variable_fee_percent: float
    fixed_fee: float
    interchange_plus_basis_points: Optional[float] = 0.0

class PerformanceMetrics(BaseModel):
    auth_rate: float = Field(..., ge=0.0, le=1.0, description="0.0 to 1.0 success rate")
    fraud_rate: float = Field(..., ge=0.0, le=1.0, description="0.0 to 1.0 fraud rate")
    avg_latency_ms: int
    cost_structure: CostStructure

class ProviderPerformance(BaseModel):
    provider: PaymentProvider
    dimension: RoutingDimension
    metrics: PerformanceMetrics
    data_window: str = "30d"
