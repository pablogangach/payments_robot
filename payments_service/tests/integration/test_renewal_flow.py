import pytest
import requests
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time

from payments_service.app.core.repositories.models import Base, MerchantORM, CustomerORM, SubscriptionORM, PrecalculatedRouteORM
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.core.utils.datetime_utils import now_utc, normalize_to_utc

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/payments")
BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def db():
    engine = create_engine(DATABASE_URL)
    # Wipe and recreate for fresh integration test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_renewal_preprocessing_and_charge_flow(db):
    """
    End-to-end integration test for renewal pre-calculation:
    1. Seed Subscription
    2. Trigger Pre-calculation
    3. Process Charge
    4. Verify Pre-calculated route was used
    """
    # 1. Cleanup & Setup
    db.query(PrecalculatedRouteORM).delete()
    db.query(SubscriptionORM).delete()
    db.query(CustomerORM).delete()
    db.query(MerchantORM).filter(MerchantORM.id == "merch_integration").delete()
    db.commit()

    # Seed Merchant
    merch = MerchantORM(
        id="merch_integration", name="Integration Merchant", email="int@example.com",
        mcc="5411", country="US", currency="USD", tax_id="TAX-INT"
    )
    db.add(merch)
    
    # Seed Customer
    cust = CustomerORM(
        id="cust_integration", merchant_id="merch_integration", 
        email="cust@example.com", payment_method_token="tok_visa", name="Int Customer"
    )
    db.add(cust)
    
    # Seed Subscription (Renewing in 3 days)
    now = now_utc()
    sub = SubscriptionORM(
        id="sub_integration", customer_id="cust_integration", merchant_id="merch_integration",
        amount=99.99, currency="USD", next_renewal_at=now + timedelta(days=3), status="active"
    )
    db.add(sub)
    db.commit()

    # 2. Trigger Pre-calculation Worker Logic
    # We'll run the script as a subprocess or just call the service if we can reach it.
    # Since we are in the integration test, let's try running the actual script.
    import subprocess
    # Run for just one cycle or manually call the service logic.
    # To be safe and clean, let's call the service logic directly in this test environment.
    from payments_service.app.routing.preprocessing.service import PreprocessingService, FeeService
    from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
    from payments_service.app.core.repositories.subscription_repository import SubscriptionRepository
    from payments_service.app.core.repositories.precalculated_route_repository import PrecalculatedRouteRepository
    from payments_service.app.routing.preprocessing import RoutingService
    from payments_service.app.core.api.dependencies import _initialize_strategy, intelligence_store
    
    sub_repo = SubscriptionRepository(db)
    precalc_repo = PrecalculatedRouteRepository(db)
    perf_repo = RoutingPerformanceRepository(intelligence_store)
    routing_svc = RoutingService(FeeService(), perf_repo, _initialize_strategy())
    
    prep_svc = PreprocessingService(
        performance_repository=perf_repo,
        subscription_repository=sub_repo,
        precalculated_route_repository=precalc_repo,
        routing_service=routing_svc
    )
    
    prep_svc.precalculate_upcoming_renewals(lookahead_days=7)

    # 3. Verify PrecalculatedRoute was created
    precalc = precalc_repo.find_by_subscription_id("sub_integration")
    assert precalc is not None
    assert precalc.subscription_id == "sub_integration"
    print(f"Pre-calculated route created: {precalc.provider}")

    # 4. Process Charge via API
    charge_payload = {
        "amount": 99.99,
        "currency": "USD",
        "merchant_id": "merch_integration",
        "customer_id": "cust_integration",
        "subscription_id": "sub_integration",
        "description": "Renewal Charge"
    }
    
    # Wait a bit for the server to be ready if needed, 
    # but here we are calling the live local server started by docker.
    response = requests.post(f"{BASE_URL}/api/v1/payments/charge", json=charge_payload)
    
    if response.status_code != 201:
        print(f"FAILED: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    assert response.status_code == 201
    payment_data = response.json()
    
    # 5. Verify Pre-calculated route was used!
    assert "Pre-calculated" in payment_data["routing_decision"]
    assert payment_data["provider"] == precalc.provider.value
    print(f"Integration Success: Payment used pre-calculated route: {payment_data['routing_decision']}")
