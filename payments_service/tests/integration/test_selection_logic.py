import pytest
from datetime import datetime, timezone
from typing import List
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.ingestion.models import RawTransactionRecord
from payments_service.app.routing.ingestion.service import DataIngestor
from payments_service.app.routing.preprocessing.service import RoutingService, FeeService
from payments_service.app.routing.preprocessing.models import FeeStructure
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.decisioning.strategies import StaticAggregationStrategy
from payments_service.app.routing.decisioning.decision_strategies import DeterministicLeastCostStrategy
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore

class MockDataProvider:
    def __init__(self, records: List[RawTransactionRecord]):
        self.records = records
    
    def fetch_data(self) -> List[RawTransactionRecord]:
        return self.records

class MockFeeService(FeeService):
    def __init__(self, fees: List[FeeStructure]):
        self.fees = fees
    def get_all_fees(self) -> List[FeeStructure]:
        return self.fees

def test_selection_logic_cheapest_provider(docker_services):
    """
    Flow 2: Intelligence-Driven Selection
    Validates that the RoutingService selects the provider with the lowest cost.
    """
    # 1. Setup
    store = InMemoryKeyValueStore()
    repo = RoutingPerformanceRepository(store)
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    
    # Configure Fee Scenarios
    # Provider A (STRIPE): 2.9% + $0.30
    # Provider B (ADYEN): 2.0% + $0.10 (Clearly cheaper)
    fees = [
        FeeStructure(provider=PaymentProvider.STRIPE, fixed_fee=0.30, variable_fee_percent=2.9),
        FeeStructure(provider=PaymentProvider.ADYEN, fixed_fee=0.10, variable_fee_percent=2.0)
    ]
    fee_service = MockFeeService(fees)
    
    # Use DeterministicLeastCostStrategy for clear validation
    routing_strategy = DeterministicLeastCostStrategy()
    routing_service = RoutingService(
        fee_service=fee_service,
        performance_repository=repo,
        strategy=routing_strategy
    )

    # 2. Ingest some baseline data (not strictly used by LeastCost, but good for end-to-end)
    records = [
        RawTransactionRecord(
            provider=PaymentProvider.STRIPE,
            payment_form="card_on_file",
            processing_type="signature",
            amount=100.0,
            currency="USD",
            status="succeeded",
            latency_ms=200,
            bin="411111",
            card_type="credit",
            network="visa",
            region="domestic",
            timestamp=datetime.now(timezone.utc)
        ),
        RawTransactionRecord(
            provider=PaymentProvider.ADYEN,
            payment_form="card_on_file",
            processing_type="signature",
            amount=100.0,
            currency="USD",
            status="succeeded",
            latency_ms=200,
            bin="411111",
            card_type="credit",
            network="visa",
            region="domestic",
            timestamp=datetime.now(timezone.utc)
        )
    ]
    ingestor.ingest_from_provider(MockDataProvider(records))

    # 3. Request a decision for a $100 payment
    payment_create = PaymentCreate(
        merchant_id="m1",
        customer_id="c1",
        amount=100.0,
        currency="USD"
    )
    
    selected_provider = routing_service.find_best_route(payment_create)

    # 4. Assertion
    # Adyen (2.0% + 0.10 = $2.10) should be picked over Stripe (2.9% + 0.30 = $3.20)
    assert selected_provider == PaymentProvider.ADYEN
    print(f"Success: Selected cheapest provider '{selected_provider.value}'")

if __name__ == "__main__":
    pytest.main([__file__])
