from typing import Any, Type, TypeVar
from pydantic import BaseModel
from payments_service.app.core.models.payment import PaymentProvider, PaymentCreate
from payments_service.app.core.models.metadata import CardBIN, InterchangeFee
from payments_service.app.routing.decisioning.models import (
    RoutingDimension, 
    CostStructure, 
    PerformanceMetrics, 
    ProviderPerformance,
    ResolvedProvider
)

T = TypeVar("T", bound=BaseModel)

def create_mock(model_class: Type[T], **overrides) -> T:
    """
    Creates a Pydantic model with sensible defaults for mocking.
    """
    defaults = {}
    
    if model_class == RoutingDimension:
        defaults = {
            "payment_method_type": "credit_card",
            "payment_form": "card_on_file",
            "network": "visa",
            "card_type": "credit",
            "region": "domestic",
            "currency": "USD"
        }
    elif model_class == CostStructure:
        defaults = {
            "fixed_fee": 0.1,
            "variable_fee_percent": 2.9
        }
    elif model_class == PerformanceMetrics:
        defaults = {
            "auth_rate": 0.95,
            "fraud_rate": 0.01,
            "avg_latency_ms": 200,
            "cost_structure": create_mock(CostStructure)
        }
    elif model_class == ProviderPerformance:
        defaults = {
            "provider": PaymentProvider.STRIPE,
            "dimension": create_mock(RoutingDimension),
            "metrics": create_mock(PerformanceMetrics)
        }
    elif model_class == ResolvedProvider:
        defaults = {
            "provider": PaymentProvider.STRIPE,
            "fixed_fee": 0.1,
            "variable_fee_percent": 2.9,
            "auth_rate": 0.95,
            "avg_latency_ms": 200
        }
    elif model_class == CardBIN:
        defaults = {
            "bin": "411111",
            "brand": "Visa",
            "type": "credit",
            "country": "United States"
        }
    elif model_class == InterchangeFee:
        defaults = {
            "network": "visa",
            "card_type": "credit",
            "region": "domestic",
            "fee_percent": 1.5,
            "fee_fixed": 0.1
        }
    elif model_class == PaymentCreate:
        defaults = {
            "merchant_id": "m1",
            "customer_id": "c1",
            "amount": 10.0,
            "currency": "USD",
            "description": "Mock Payment"
        }
        
    defaults.update(overrides)
    return model_class(**defaults)
