import pytest
from app.services.routing_data_service import RoutingDataManager
from app.repositories.performance_repository import RoutingPerformanceRepository
from app.models.routing_data import RoutingDimension, ProviderPerformance, PerformanceMetrics, CostStructure
from app.models.payment import PaymentProvider

def test_manager_update_performance():
    repo = RoutingPerformanceRepository()
    manager = RoutingDataManager(repo)
    
    dim = RoutingDimension(
        payment_method_type="bank_transfer",
        network="ach",
        card_type="n/a",
        region="domestic"
    )
    
    # 1. Initially empty in repo
    assert len(repo.find_by_dimension(dim)) == 0
    
    # 2. Manager updates performance
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
    manager.update_performance(new_perf)
    
    # 3. Verify it's in repo
    results = repo.find_by_dimension(dim)
    assert len(results) == 1
    assert results[0].provider == PaymentProvider.INTERNAL
