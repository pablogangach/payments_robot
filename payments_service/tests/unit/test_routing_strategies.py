import pytest
from payments_service.app.routing.decisioning.decision_strategies import (
    DeterministicLeastCostStrategy, 
    FixedProviderStrategy
)
from payments_service.app.routing.preprocessing.service import RoutingService, FeeService
from payments_service.app.core.models.payment import PaymentProvider, PaymentCreate
from payments_service.app.routing.decisioning import RoutingPerformanceRepository
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore

@pytest.fixture
def mock_fees():
    return FeeService()

@pytest.fixture
def mock_repo():
    store = InMemoryKeyValueStore()
    return RoutingPerformanceRepository(store)

from payments_service.app.routing.decisioning.models import ResolvedProvider

def test_fixed_provider_strategy():
    strategy = FixedProviderStrategy(PaymentProvider.ADYEN)
    payment = PaymentCreate(amount=100.0, currency="USD", merchant_id="m1", customer_id="c1")
    
    decision = strategy.decide(payment, [])
    assert decision == PaymentProvider.ADYEN

def test_deterministic_least_cost_strategy():
    strategy = DeterministicLeastCostStrategy()
    payment = PaymentCreate(amount=100.0, currency="USD", merchant_id="m1", customer_id="c1")
    
    # Reconciled providers
    providers = [
        ResolvedProvider(provider=PaymentProvider.STRIPE, fixed_fee=0.30, variable_fee_percent=2.9, auth_rate=0.99, avg_latency_ms=200),
        ResolvedProvider(provider=PaymentProvider.INTERNAL, fixed_fee=0.50, variable_fee_percent=2.5, auth_rate=0.99, avg_latency_ms=200),
    ]
    
    # Stripe: 0.30 + 100 * 0.029 = 3.20
    # Internal: 0.50 + 100 * 0.025 = 3.00
    # Internal is cheaper.
    
    decision = strategy.decide(payment, providers)
    assert decision == PaymentProvider.INTERNAL

def test_routing_service_integration(mock_fees, mock_repo):
    strategy = FixedProviderStrategy(PaymentProvider.BRAINTREE)
    service = RoutingService(
        fee_service=mock_fees,
        performance_repository=mock_repo,
        strategy=strategy
    )
    
    payment = PaymentCreate(amount=50.0, currency="USD", merchant_id="m1", customer_id="c1")
    decision = service.find_best_route(payment)
    
    assert decision == PaymentProvider.BRAINTREE
