import pytest
from datetime import datetime
from typing import Dict, Any
from payments_service.app.routing.ingestion.models import RawTransactionRecord
from payments_service.app.routing.ingestion.parsers import StripeCsvParser
from payments_service.app.routing.decisioning.models import RoutingDimension, ProviderPerformance, PerformanceMetrics, CostStructure
from payments_service.app.routing.decisioning.strategies import StaticAggregationStrategy
from payments_service.app.routing.preprocessing.service import RoutingService, FeeService
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.core.repositories.datastore import KeyValueStore
from payments_service.app.core.models.payment import PaymentProvider, PaymentCreate

def test_dynamic_field_propagation():
    # 1. Simulate a raw record with an extra field "merchant_category"
    row = {
        "amount": "100.0",
        "currency": "usd",
        "status": "available",
        "card_brand": "visa",
        "card_country": "US",
        "created": "2023-01-01 12:00:00",
        "merchant_category": "gaming" # This is the extra field
    }
    
    parser = StripeCsvParser()
    record = parser.parse(row)
    
    assert "merchant_category" in record.extra_fields
    assert record.extra_fields["merchant_category"] == "gaming"

    # 2. Aggregate using StaticAggregationStrategy with dynamic dimensions enabled
    strategy = StaticAggregationStrategy(dynamic_dimensions=["merchant_category"])
    performances = strategy.analyze([record])
    
    assert len(performances) == 1
    perf = performances[0]
    # Check that merchant_category is in the dimension
    assert hasattr(perf.dimension, "merchant_category")
    assert perf.dimension.merchant_category == "gaming"

    # 3. Setup RoutingService and verify it finds the performance data
    class MockStore(KeyValueStore):
        def __init__(self):
            self.data = {}
        def get(self, key): return self.data.get(key)
        def set(self, key, val): self.data[key] = val
        def delete(self, key): 
            if key in self.data: del self.data[key]
        def get_all(self): return list(self.data.values())
        def set_all(self, data): self.data = data

    repo = RoutingPerformanceRepository(MockStore())
    repo.save(perf)
    
    fee_service = FeeService()
    # Construct a dimension that includes the merchant_category
    dim = RoutingDimension(
        payment_method_type="credit_card",
        payment_form="card_on_file",
        network="visa",
        card_type="credit",
        currency="USD",
        region="domestic",
        merchant_category="gaming" # Injected manually for lookup in this test
    )
    
    service = RoutingService(fee_service=fee_service, performance_repository=repo)
    
    # Debug keys
    print(f"DEBUG: Saved Key: {repo._get_key(perf.dimension)}")
    print(f"DEBUG: Lookup Key: {repo._get_key(dim)}")

    # We need to mock find_best_route's dimension construction or pass it in.
    # For this test, let's verify find_by_dimension directly with the dynamic dim.
    found_perf = repo.find_by_dimension(dim)
    assert len(found_perf) == 1
    assert found_perf[0].provider == PaymentProvider.STRIPE
    
    # Now verify the LLM strategy context (conceptual check)
    # We'll manually run the reconciliation logic from RoutingService
    extra_from_dim = found_perf[0].dimension.model_extra or {}
    
    assert "merchant_category" in extra_from_dim
    assert extra_from_dim["merchant_category"] == "gaming"
