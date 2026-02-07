import pytest
import os
from payments_service.app.core.models.merchant import Merchant, MerchantStatus
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.routing.decisioning.models import (
    ProviderPerformance, 
    RoutingDimension, 
    PerformanceMetrics,
    CostStructure
)
from payments_service.app.core.api.dependencies import (
    merchant_repo, 
    performance_repo, 
    routing_service
)

def test_routing_flow_real_storage(docker_services):
    """
    Validates that the routing engine correctly uses real Postgres and Redis data.
    """
    import uuid
    import random
    unique_tax_id = f"TX-{random.randint(1000000, 9999999)}"
    unique_merchant_id = str(uuid.uuid4())
    
    # 1. Seed a Merchant in Postgres
    merchant = Merchant(
        id=unique_merchant_id,
        name="Test Merchant",
        email=f"test-{unique_merchant_id}@example.com",
        mcc="5411",
        country="US",
        currency="USD",
        tax_id=unique_tax_id,
        status=MerchantStatus.ACTIVE
    )
    merchant_repo.save(merchant)
    
    # Verify it was saved and can be retrieved
    retrieved_merchant = merchant_repo.find_by_id(merchant.id)
    assert retrieved_merchant is not None
    assert retrieved_merchant.name == "Test Merchant"

    # 2. Seed Performance Metrics in Redis
    dimension = RoutingDimension(
        payment_method_type="credit_card",
        region="domestic",
        currency="USD"
    )

    # Provider A: Low Cost (0.10)
    perf_a = ProviderPerformance(
        provider=PaymentProvider.STRIPE,
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.99,
            fraud_rate=0.01,
            avg_latency_ms=200,
            cost_structure=CostStructure(variable_fee_percent=0.01, fixed_fee=0.10)
        )
    )

    # Provider B: High Cost (0.30)
    perf_b = ProviderPerformance(
        provider=PaymentProvider.BRAINTREE,
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.99,
            fraud_rate=0.01,
            avg_latency_ms=200,
            cost_structure=CostStructure(variable_fee_percent=0.01, fixed_fee=0.30)
        )
    )

    performance_repo.save(perf_a)
    performance_repo.save(perf_b)

    # Verify they were saved to Redis
    all_perf = performance_repo.find_by_dimension(dimension)
    assert len(all_perf) == 2

    # 3. Trigger Routing Decision
    from payments_service.app.core.models.payment import PaymentCreate
    payment_in = PaymentCreate(
        merchant_id=merchant.id,
        customer_id="cust_123",
        amount=100.0,
        currency="USD"
    )
    
    # We use DeterministicLeastCostStrategy (likely the fallback in dependencies if LLM isn't configured)
    decision = routing_service.find_best_route(payment_in)
    
    # 4. Assertions
    # Stripe (perf_a) should be chosen as it has a lower fixed fee (0.10 vs 0.30)
    assert decision == PaymentProvider.STRIPE
    print(f"\nSuccessfully routed to {decision} based on persistent metrics.")
