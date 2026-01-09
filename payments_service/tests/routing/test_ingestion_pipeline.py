import pytest
from datetime import datetime, timedelta
from typing import List, Any
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.routing.models.ingestion import RawTransactionRecord
from payments_service.app.routing.interfaces import DataProvider
from payments_service.app.routing.repositories.performance_repository import RoutingPerformanceRepository
from payments_service.app.routing.services.intelligence_strategies import StaticAggregationStrategy
from payments_service.app.routing.services.ingestion_service import DataIngestor

class MockJsonDataProvider(DataProvider):
    """
    Simulates a data provider that fetches raw transaction data (already parsed).
    """
    def __init__(self, records: List[RawTransactionRecord]):
        self.records = records

    def fetch_data(self) -> List[RawTransactionRecord]:
        return self.records

def test_ingestion_pipeline_success():
    # 1. Setup
    repo = RoutingPerformanceRepository()
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    
    # Create sample records: 2 for Stripe (1 success, 1 fail), 1 for Adyen (success)
    # All for the same dimension: Visa, Domestic, card_on_file
    now = datetime.now()
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
            timestamp=now
        ),
        RawTransactionRecord(
            provider=PaymentProvider.STRIPE,
            payment_form="card_on_file",
            processing_type="signature",
            amount=50.0,
            currency="USD",
            status="failed",
            latency_ms=150,
            bin="411111",
            card_type="credit",
            network="visa",
            region="domestic",
            timestamp=now - timedelta(minutes=5)
        ),
        RawTransactionRecord(
            provider=PaymentProvider.ADYEN,
            payment_form="card_on_file",
            processing_type="signature",
            amount=200.0,
            currency="USD",
            status="succeeded",
            latency_ms=300,
            bin="411111",
            card_type="credit",
            network="visa",
            region="domestic",
            timestamp=now
        )
    ]
    
    provider = MockJsonDataProvider(records)
    
    # 2. Execute Ingestion
    ingestor.ingest_from_provider(provider)
    
    # 3. Verify Results in Repository
    all_performance = repo.get_all()
    assert len(all_performance) == 2 # 1 Stripe, 1 Adyen
    
    # Check Stripe Metrics (50% auth rate, 175ms avg latency)
    stripe_perf = next(p for p in all_performance if p.provider == PaymentProvider.STRIPE)
    assert stripe_perf.metrics.auth_rate == 0.5
    assert stripe_perf.metrics.avg_latency_ms == 175
    assert stripe_perf.dimension.payment_form == "card_on_file"
    
    # Check Adyen Metrics (100% auth rate, 300ms avg latency)
    adyen_perf = next(p for p in all_performance if p.provider == PaymentProvider.ADYEN)
    assert adyen_perf.metrics.auth_rate == 1.0
    assert adyen_perf.metrics.avg_latency_ms == 300
    
def test_ingestion_with_mobile_wallet():
    repo = RoutingPerformanceRepository()
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    
    now = datetime.now()
    records = [
        RawTransactionRecord(
            provider=PaymentProvider.STRIPE,
            payment_form="apple_pay",
            processing_type="network_token",
            amount=100.0,
            currency="USD",
            status="succeeded",
            latency_ms=100,
            bin="411111",
            card_type="credit",
            network="visa",
            region="domestic",
            timestamp=now
        )
    ]
    
    provider = MockJsonDataProvider(records)
    ingestor.ingest_from_provider(provider)
    
    # Verify it saved under the correct dimension
    all_perf = repo.get_all()
    assert len(all_perf) == 1
    assert all_perf[0].dimension.payment_form == "apple_pay"
    assert all_perf[0].metrics.auth_rate == 1.0
