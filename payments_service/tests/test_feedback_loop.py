import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from payments_service.app.core.models.payment import Payment, PaymentStatus, PaymentProvider
from payments_service.app.routing.decisioning.feedback import (
    InMemoryFeedbackStore, 
    LocalFeedbackCollector
)
from payments_service.app.routing.ingestion.feedback_provider import InternalFeedbackDataProvider
from payments_service.app.routing.ingestion import DataIngestor
from payments_service.app.routing.decisioning import (
    RoutingPerformanceRepository, 
    StaticAggregationStrategy
)
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore

def test_feedback_collector_mapping():
    # Setup
    store = InMemoryFeedbackStore()
    collector = LocalFeedbackCollector(store)
    
    payment = Payment(
        merchant_id="m1",
        customer_id="c1",
        amount=150.0,
        currency="USD",
        provider=PaymentProvider.STRIPE,
        status=PaymentStatus.COMPLETED,
        updated_at=datetime.now(timezone.utc)
    )
    
    # Execute
    collector.collect(payment)
    
    # Verify
    records = store.get_all_records()
    assert len(records) == 1
    record = records[0]
    assert record.provider == PaymentProvider.STRIPE
    assert record.status == "succeeded"
    assert record.amount == 150.0

def test_full_feedback_loop_to_repository():
    # 1. Setup Infra
    store = InMemoryFeedbackStore()
    collector = LocalFeedbackCollector(store)
    feedback_provider = InternalFeedbackDataProvider(store)
    
    repo_store = InMemoryKeyValueStore()
    repo = RoutingPerformanceRepository(repo_store)
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    
    # 2. Simulate Payment Feedback
    p1 = Payment(
        merchant_id="m1", customer_id="c1", amount=100.0, currency="USD",
        provider=PaymentProvider.STRIPE, status=PaymentStatus.COMPLETED,
        updated_at=datetime.now(timezone.utc)
    )
    p2 = Payment(
        merchant_id="m2", customer_id="c2", amount=50.0, currency="USD",
        provider=PaymentProvider.STRIPE, status=PaymentStatus.FAILED,
        updated_at=datetime.now(timezone.utc)
    )
    
    collector.collect(p1)
    collector.collect(p2)
    
    # 3. Simulate Ingestion (The "Closing the Loop" part)
    ingestor.ingest_from_provider(feedback_provider)
    
    # 4. Verify Repository Metrics
    all_perf = repo.get_all()
    assert len(all_perf) == 1 # 1 Provider (Stripe) for the dimension
    stripe_perf = all_perf[0]
    
    # 1 Success, 1 Failure -> 0.5 Auth Rate
    assert stripe_perf.metrics.auth_rate == 0.5
    assert stripe_perf.provider == PaymentProvider.STRIPE
