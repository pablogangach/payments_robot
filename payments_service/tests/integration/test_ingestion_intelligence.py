import pytest
from datetime import datetime, timezone
from typing import List
from payments_service.app.core.models.payment import Payment, PaymentStatus, PaymentProvider
from payments_service.app.routing.ingestion.models import RawTransactionRecord
from payments_service.app.routing.ingestion.service import DataIngestor
from payments_service.app.routing.ingestion.data_generator import DataGenerator
from payments_service.app.routing.ingestion.feedback_provider import InternalFeedbackDataProvider
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.decisioning.strategies import StaticAggregationStrategy
from payments_service.app.routing.decisioning.feedback import InMemoryFeedbackStore, LocalFeedbackCollector
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore

class MockDataProvider:
    def __init__(self, records: List[RawTransactionRecord]):
        self.records = records
    
    def fetch_data(self) -> List[RawTransactionRecord]:
        return self.records

def test_ingestion_intelligence_path():
    """
    Flow 1: Ingestion & Intelligence Path
    Validates end-to-end data pipeline: 
    Raw data (Generator) + Real-time feedback (Collector) -> Ingestor -> Repository Metrics
    """
    # 1. Setup
    store = InMemoryKeyValueStore()
    repo = RoutingPerformanceRepository(store)
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    
    feedback_store = InMemoryFeedbackStore()
    collector = LocalFeedbackCollector(feedback_store)
    feedback_provider = InternalFeedbackDataProvider(feedback_store)
    
    generator = DataGenerator()

    # 2. Stage 1: Data Preparation
    # Generate 10 records for Stripe (all succeeded)
    historical_records = [
        generator.generate_record(provider=PaymentProvider.STRIPE) 
        for _ in range(10)
    ]
    for r in historical_records:
        r.status = "succeeded" 
        r.network = "visa"
        r.region = "domestic"
        r.payment_form = "card_on_file"
        r.currency = "USD"
        r.card_type = "credit"

    # Stage 2: Real-time Feedback Collection
    # Simulate a failed payment for Stripe
    payment = Payment(
        merchant_id="m1",
        customer_id="c1",
        amount=100.0,
        currency="USD",
        status=PaymentStatus.FAILED,
        provider=PaymentProvider.STRIPE,
        updated_at=datetime.now(timezone.utc)
    )
    
    print("Collecting real-time failed feedback for Stripe...")
    collector.collect(payment)
    
    # 3. Stage 3: Combined Ingestion
    # We combine both sources to simulate a full batch processing
    # validating that the intelligence engine correctly aggregates both sets.
    feedback_records = feedback_provider.fetch_data()
    all_records = historical_records + feedback_records
    
    print(f"Ingesting combined {len(all_records)} Stripe records...")
    ingestor.ingest_from_provider(MockDataProvider(all_records))
    
    # 4. Final Assertion
    # Stripe should now have 11 records total (10 success + 1 failed)
    # Auth rate should be 10/11 = ~0.909
    all_perf_final = repo.get_all()
    stripe_perf_final = next(p for p in all_perf_final if p.provider == PaymentProvider.STRIPE)
    
    expected_auth_rate = 10 / 11
    assert stripe_perf_final.metrics.auth_rate == pytest.approx(expected_auth_rate, rel=1e-2)
    print(f"Final Auth Rate for Stripe: {stripe_perf_final.metrics.auth_rate:.4f}")

if __name__ == "__main__":
    pytest.main([__file__])
