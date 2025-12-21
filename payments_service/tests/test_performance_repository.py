import pytest
from app.repositories.performance_repository import RoutingPerformanceRepository
from app.models.routing_data import RoutingDimension, ProviderPerformance, PerformanceMetrics, CostStructure
from app.models.payment import PaymentProvider

def test_find_by_dimension_exact_match():
    repo = RoutingPerformanceRepository()
    
    # Use the dimension we know exists from mock data
    dim = RoutingDimension(
        payment_method_type="credit_card",
        network="visa",
        card_type="credit",
        region="domestic",
        currency="USD",
        is_network_tokenized=False
    )
    
    results = repo.find_by_dimension(dim)
    
    assert len(results) == 2
    # Verify we got both Stripe and Internal
    providers = {r.provider for r in results}
    assert PaymentProvider.STRIPE in providers
    assert PaymentProvider.INTERNAL in providers

def test_find_by_dimension_no_match():
    repo = RoutingPerformanceRepository()
    
    # Dimension that doesn't exist
    dim = RoutingDimension(
        payment_method_type="unknown_method",
        network="visa",
        card_type="credit", 
        region="mars"
    )
    
    results = repo.find_by_dimension(dim)
    assert len(results) == 0

def test_save_performance():
    repo = RoutingPerformanceRepository()
    
    dim = RoutingDimension(
        payment_method_type="bank_transfer",
        network="ach",
        card_type="n/a",
        region="domestic"
    )
    
    # 1. Initially empty
    assert len(repo.find_by_dimension(dim)) == 0
    
    # 2. Add performance record
    new_perf = ProviderPerformance(
        provider=PaymentProvider.INTERNAL,
        dimension=dim,
        metrics=PerformanceMetrics(
            auth_rate=0.99,
            fraud_rate=0.0,
            avg_latency_ms=1000,
            cost_structure=CostStructure(variable_fee_percent=0.5, fixed_fee=0.0)
        )
    )
    repo.save(new_perf)
    
    # 3. Verify it's retrieved
    results = repo.find_by_dimension(dim)
    assert len(results) == 1
    assert results[0].provider == PaymentProvider.INTERNAL
    assert results[0].metrics.auth_rate == 0.99
