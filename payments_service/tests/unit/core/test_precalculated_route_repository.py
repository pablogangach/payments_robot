import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from payments_service.app.core.repositories.models import Base
from payments_service.app.core.repositories.precalculated_route_repository import PrecalculatedRouteRepository
from payments_service.app.core.models.precalculated_route import PrecalculatedRouteCreate
from payments_service.app.core.models.payment import PaymentProvider

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_save_and_find_precalculated_route(db_session):
    repo = PrecalculatedRouteRepository(db_session)
    expiry = datetime.now(timezone.utc) + timedelta(hours=24)
    
    route_in = PrecalculatedRouteCreate(
        subscription_id="sub123",
        provider=PaymentProvider.ADYEN,
        routing_decision="Lowest cost",
        expires_at=expiry
    )
    
    saved_route = repo.save(route_in)
    assert saved_route.subscription_id == "sub123"
    assert saved_route.provider == PaymentProvider.ADYEN
    
    found_route = repo.find_by_subscription_id("sub123")
    assert found_route is not None
    assert found_route.provider == PaymentProvider.ADYEN

def test_upsert_precalculated_route(db_session):
    repo = PrecalculatedRouteRepository(db_session)
    
    # First save
    repo.save(PrecalculatedRouteCreate(
        subscription_id="sub1", provider=PaymentProvider.STRIPE, 
        routing_decision="D1", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    
    # Second save (Upsert)
    repo.save(PrecalculatedRouteCreate(
        subscription_id="sub1", provider=PaymentProvider.ADYEN, 
        routing_decision="D2", expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
    ))
    
    found = repo.find_by_subscription_id("sub1")
    assert found.provider == PaymentProvider.ADYEN
    assert found.routing_decision == "D2"

def test_delete_expired_routes(db_session):
    repo = PrecalculatedRouteRepository(db_session)
    now = datetime.now(timezone.utc)
    
    # 1. Expired
    repo.save(PrecalculatedRouteCreate(
        subscription_id="expired", provider=PaymentProvider.STRIPE, 
        routing_decision="D", expires_at=now - timedelta(hours=1)
    ))
    
    # 2. Not expired
    repo.save(PrecalculatedRouteCreate(
        subscription_id="valid", provider=PaymentProvider.STRIPE, 
        routing_decision="D", expires_at=now + timedelta(hours=1)
    ))
    
    repo.delete_expired(now)
    
    assert repo.find_by_subscription_id("expired") is None
    assert repo.find_by_subscription_id("valid") is not None
