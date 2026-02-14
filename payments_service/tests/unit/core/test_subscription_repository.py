import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from payments_service.app.core.repositories.models import Base
from payments_service.app.core.repositories.subscription_repository import SubscriptionRepository
from payments_service.app.core.models.subscription import SubscriptionCreate, SubscriptionStatus

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_save_and_find_subscription(db_session):
    repo = SubscriptionRepository(db_session)
    next_renewal = datetime.now(timezone.utc) + timedelta(days=30)
    
    sub_in = SubscriptionCreate(
        customer_id="cust1",
        merchant_id="merch1",
        amount=10.0,
        currency="USD",
        next_renewal_at=next_renewal
    )
    
    saved_sub = repo.save(sub_in)
    assert saved_sub.id is not None
    assert saved_sub.customer_id == "cust1"
    assert saved_sub.next_renewal_at.replace(tzinfo=timezone.utc) == next_renewal
    
    found_sub = repo.find_by_id(saved_sub.id)
    assert found_sub is not None
    assert found_sub.id == saved_sub.id

def test_find_upcoming_renewals(db_session):
    repo = SubscriptionRepository(db_session)
    now = datetime.now(timezone.utc)
    
    # 1. Renewal in 3 days (Should be found)
    sub1 = repo.save(SubscriptionCreate(
        customer_id="c1", merchant_id="m1", amount=10, currency="USD", 
        next_renewal_at=now + timedelta(days=3)
    ))
    
    # 2. Renewal in 10 days (Should NOT be found with 7 day lookahead)
    sub2 = repo.save(SubscriptionCreate(
        customer_id="c2", merchant_id="m1", amount=10, currency="USD", 
        next_renewal_at=now + timedelta(days=10)
    ))
    
    # 3. Inactive subscription (Should NOT be found)
    sub3 = repo.save(SubscriptionCreate(
        customer_id="c3", merchant_id="m1", amount=10, currency="USD", 
        next_renewal_at=now + timedelta(days=2)
    ))
    # Manually update status to inactive
    from payments_service.app.core.repositories.models import SubscriptionORM
    db_sub3 = db_session.query(SubscriptionORM).filter_by(id=sub3.id).first()
    db_sub3.status = "cancelled"
    db_session.commit()

    upcoming = repo.find_upcoming_renewals(now, now + timedelta(days=7))
    
    assert len(upcoming) == 1
    assert upcoming[0].id == sub1.id
