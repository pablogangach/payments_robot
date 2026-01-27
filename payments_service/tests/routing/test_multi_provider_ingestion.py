import pytest
import os
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.routing.ingestion import DataIngestor, StripeCsvParser, AdyenCsvParser
from payments_service.app.routing.decisioning import RoutingPerformanceRepository, StaticAggregationStrategy, RoutingDimension
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore
from payments_service.tests.routing.providers import LocalFileDataProvider

def test_multi_provider_csv_ingestion():
    # 1. Setup
    repo = RoutingPerformanceRepository(InMemoryKeyValueStore())
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    
    # Paths to simulated "S3" files
    base_path = "payments_service/tests/data/raw_logs/"
    stripe_file = os.path.join(base_path, "stripe_export.csv")
    adyen_file = os.path.join(base_path, "adyen_export.csv")
    
    # 2. Ingest Stripe Data
    stripe_provider = LocalFileDataProvider(stripe_file, StripeCsvParser())
    ingestor.ingest_from_provider(stripe_provider)
    
    # 3. Ingest Adyen Data
    adyen_provider = LocalFileDataProvider(adyen_file, AdyenCsvParser())
    ingestor.ingest_from_provider(adyen_provider)
    
    # 4. Verification
    all_performance = repo.get_all()
    
    # We expect records for Stripe (Visa, MC) and Adyen (Visa, MC)
    # Stripe had 2 Visa (1 US, 1 UK) and 1 Mastercard
    assert len(all_performance) >= 3 # At least Stripe Visa, Stripe MC, Adyen Visa, Adyen MC
    
    # Verify Stripe Visa Domestic (US)
    stripe_visa_dim = RoutingDimension(
        payment_method_type="credit_card",
        payment_form="card_on_file",
        network="visa",
        card_type="credit",
        region="domestic",
        currency="USD"
    )
    stripe_visa_perf = next(p for p in all_performance if p.provider == PaymentProvider.STRIPE and p.dimension == stripe_visa_dim)
    assert stripe_visa_perf.metrics.auth_rate == 1.0 # Both Stripe Visa rows in CSV were 'available'
    
    # Verify Adyen Visa
    adyen_visa_dim = RoutingDimension(
        payment_method_type="credit_card",
        payment_form="card_on_file",
        network="visa",
        card_type="credit",
        region="domestic", # Adyen parser forced domestic for now
        currency="USD"
    )
    adyen_visa_perf = next(p for p in all_performance if p.provider == PaymentProvider.ADYEN and p.dimension == adyen_visa_dim)
    # Adyen Visa had 1 Settled, 1 Refund. Settled=success, Refund=failed in our parser logic.
    assert adyen_visa_perf.metrics.auth_rate == 0.5 

def test_stripe_parser_logic_specifically():
    parser = StripeCsvParser()
    # Mock a row from Stripe CSV
    row = {
        "amount": "150.00",
        "currency": "usd",
        "status": "available",
        "card_brand": "Amex",
        "card_country": "US",
        "created": "2026-01-11 12:00:00"
    }
    record = parser.parse(row)
    assert record.provider == PaymentProvider.STRIPE
    assert record.network == "amex"
    assert record.amount == 150.0
    assert record.region == "domestic"
