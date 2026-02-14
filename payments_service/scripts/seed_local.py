import os
import uuid
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from payments_service.app.core.models.merchant import Merchant, MerchantStatus
from payments_service.app.core.models.customer import Customer
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.routing.decisioning.models import (
    ProviderPerformance, 
    RoutingDimension, 
    PerformanceMetrics, 
    CostStructure
)
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.core.repositories.datastore import RedisKeyValueStore

# Config
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/payments")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def seed():
    print("Starting seeding process...")
    
    # 1. Postgres Seeding
    engine = create_engine(DB_URL)
    
    # Ensure tables exist
    from payments_service.app.core.repositories.models import Base
    print("Wiping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    from payments_service.app.core.repositories.models import MerchantORM, CustomerORM

    print("Seeding default merchant...")
    merchant = MerchantORM(
        id="default_merchant",
        name="Global E-Commerce Corp",
        email="admin@globalcorp.com",
        mcc="5411",
        country="US",
        currency="USD",
        tax_id="12-3456789",
        status="active"
    )
    session.add(merchant)
    
    print("Seeding default customer...")
    customer = CustomerORM(
        id="cust_123",
        merchant_id="default_merchant",
        email="john.doe@example.com",
        payment_method_token="tok_visa_123",
        status="active"
    )
    session.add(customer)
    session.commit()

    # 2. Redis Seeding
    redis_client = redis.from_url(REDIS_URL)
    store = RedisKeyValueStore(redis_client, model_class=list)
    repo = RoutingPerformanceRepository(store)
    
    dimension = RoutingDimension(
        payment_method_type="credit_card",
        region="domestic",
        currency="USD"
    )

    print("Seeding performance metrics...")
    # Seed Stripe (cheaper fixed, slightly higher variable)
    repo.save(ProviderPerformance(
        provider=PaymentProvider.STRIPE,
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.98,
            fraud_rate=0.01,
            avg_latency_ms=180,
            cost_structure=CostStructure(variable_fee_percent=2.9, fixed_fee=0.10)
        )
    ))

    # Seed Braintree (more expensive fixed, lower variable)
    repo.save(ProviderPerformance(
        provider=PaymentProvider.BRAINTREE,
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.97,
            fraud_rate=0.01,
            avg_latency_ms=210,
            cost_structure=CostStructure(variable_fee_percent=2.5, fixed_fee=0.30)
        )
    ))

    print("Seeding complete!")

if __name__ == "__main__":
    seed()
