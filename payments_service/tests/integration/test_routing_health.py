import pytest
import redis
import os
from unittest.mock import MagicMock
from payments_service.tests.factories import create_mock
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.routing.decisioning.models import ProviderPerformance, RoutingDimension, PerformanceMetrics, CostStructure
from payments_service.app.routing.preprocessing.service import PreprocessingService
from payments_service.app.routing.preprocessing.models import (
    Customer, PaymentMethodDetails, Product, BillingType
)

def test_routing_respects_health():
    # 1. Setup
    mock_perf_repo = MagicMock()
    mock_bin_repo = MagicMock()
    mock_fee_repo = MagicMock()
    mock_redis = MagicMock()
    
    service = PreprocessingService(
        performance_repository=mock_perf_repo,
        bin_repository=mock_bin_repo,
        fee_repository=mock_fee_repo,
        redis_client=mock_redis
    )
    
    dimension = create_mock(RoutingDimension)
    
    stripe_perf = create_mock(
        ProviderPerformance,
        provider=PaymentProvider.STRIPE,
        dimension=dimension,
        metrics=create_mock(PerformanceMetrics, auth_rate=0.98, cost_structure=create_mock(CostStructure, fixed_fee=0.1))
    )
    adyen_perf = create_mock(
        ProviderPerformance,
        provider=PaymentProvider.ADYEN,
        dimension=dimension,
        metrics=create_mock(PerformanceMetrics, auth_rate=0.95, cost_structure=create_mock(CostStructure, fixed_fee=0.05))
    )
    
    mock_perf_repo.find_by_dimension.return_value = [stripe_perf, adyen_perf]
    mock_bin_repo.find_by_bin.return_value = None # Use defaults
    
    # 3. Simulate SCENARIO: Adyen is CHEAPER but DOWN
    mock_redis.get.side_effect = lambda key: b"down" if "adyen" in key else b"up"
    
    # 4. Execute
    route = service.preprocess_recurrent_payment(
        customer=Customer(id="c1", locale="en_US"),
        payment_method=PaymentMethodDetails(type="credit_card", bin="411111"),
        product=Product(id="p1", name="Test"),
        billing_type=BillingType.MONTHLY
    )
    
    # 5. Assert: Should pick STRIPE because Adyen is down
    assert route.processor == PaymentProvider.STRIPE
    assert "Optimal route" in route.routing_reason
    print("Health-aware routing test passed!")

if __name__ == "__main__":
    test_routing_respects_health()
