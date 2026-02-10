import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis

from payments_service.app.core.repositories.merchant_repository import MerchantRepository
from payments_service.app.core.repositories.customer_repository import CustomerRepository
from payments_service.app.core.repositories.payment_repository import PaymentRepository
from payments_service.app.core.services.merchant_service import MerchantService
from payments_service.app.core.services.customer_service import CustomerService
from payments_service.app.core.services.payment_service import PaymentService

from payments_service.app.routing.preprocessing import RoutingService, FeeService
from payments_service.app.routing.decisioning import RoutingPerformanceRepository, StaticAggregationStrategy
from payments_service.app.routing.decisioning.decision_strategies import PlannerRoutingStrategy, DeterministicLeastCostStrategy
from payments_service.app.routing.ingestion import DataIngestor

from payments_service.app.processors.adapters.stripe_adapter import StripeProcessor
from payments_service.app.processors.adapters.adyen_adapter import AdyenProcessor
from payments_service.app.processors.adapters.braintree_adapter import BraintreeProcessor
from payments_service.app.processors.adapters.internal_mock_adapter import InternalMockProcessor

from payments_service.app.processors.registry import ProcessorRegistry
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.core.repositories.datastore import (
    InMemoryKeyValueStore, 
    InMemoryRelationalStore,
    RedisKeyValueStore,
    PostgresRelationalStore
)
from payments_service.app.core.models.merchant import Merchant
from payments_service.app.core.repositories.models import Base, MerchantORM, CustomerORM, PaymentORM
from payments_service.app.core.models.merchant import Merchant
from payments_service.app.core.models.customer import Customer
from payments_service.app.core.models.payment import Payment

# Environment Config
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# --- Storage Layer Setup ---

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    # Bridge between SQLAlchemy and Pydantic
    merchant_store = PostgresRelationalStore(db_session, MerchantORM, Merchant)
    customer_store = PostgresRelationalStore(db_session, CustomerORM, Customer)
    payment_store = PostgresRelationalStore(db_session, PaymentORM, Payment)
else:
    merchant_store = InMemoryRelationalStore()
    customer_store = InMemoryRelationalStore()
    payment_store = InMemoryRelationalStore()

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL)
    # The store expects a model_class for validation. 
    # For List[ProviderPerformance], we'll need a wrapper or just use JSON.
    # RoutingPerformanceRepository uses KeyValueStore[List[ProviderPerformance]]
    intelligence_store = RedisKeyValueStore(redis_client, list) 
else:
    intelligence_store = InMemoryKeyValueStore()

# --- Repositories ---

merchant_repo = MerchantRepository(merchant_store)
customer_repo = CustomerRepository(customer_store)
payment_repo = PaymentRepository(payment_store)
performance_repo = RoutingPerformanceRepository(intelligence_store)

# --- Processors Registration ---
processor_registry = ProcessorRegistry()
processor_registry.register(PaymentProvider.STRIPE, StripeProcessor())
processor_registry.register(PaymentProvider.ADYEN, AdyenProcessor())
processor_registry.register(PaymentProvider.BRAINTREE, BraintreeProcessor())
processor_registry.register(PaymentProvider.INTERNAL, InternalMockProcessor())

# --- Services ---
fee_service = FeeService()

# --- Strategy Selection ---
STRATEGY_TYPE = os.getenv("ROUTING_STRATEGY", "LEAST_COST").upper()
ROUTING_MODEL = os.getenv("ROUTING_MODEL", "openai:gpt-4o")
ROUTING_OBJECTIVE = os.getenv("ROUTING_OBJECTIVE", "balanced")

from payments_service.app.routing.decisioning.interfaces import RoutingDecisionStrategy
from payments_service.app.routing.decisioning.decision_strategies import AISUITE_AVAILABLE, FixedProviderStrategy

def _initialize_strategy() -> RoutingDecisionStrategy:
    if STRATEGY_TYPE == "PLANNER":
        if not AISUITE_AVAILABLE:
            print("Warning: ROUTING_STRATEGY=PLANNER requested but aisuite not available. Falling back to LEAST_COST.")
            return DeterministicLeastCostStrategy()
        return PlannerRoutingStrategy(objective=ROUTING_OBJECTIVE, model=ROUTING_MODEL)
    
    if STRATEGY_TYPE == "LLM":
        if not AISUITE_AVAILABLE:
            print("Warning: ROUTING_STRATEGY=LLM requested but aisuite not available. Falling back to LEAST_COST.")
            return DeterministicLeastCostStrategy()
        from payments_service.app.routing.decisioning.decision_strategies import LLMDecisionStrategy
        return LLMDecisionStrategy(objective=ROUTING_OBJECTIVE, model=ROUTING_MODEL)
    
    if STRATEGY_TYPE == "FIXED":
        # Default fixed to INTERNAL for now, could be further parameterized
        return FixedProviderStrategy(provider=PaymentProvider.INTERNAL)
        
    return DeterministicLeastCostStrategy()

routing_strategy = _initialize_strategy()
print(f"Initialized Routing Strategy: {routing_strategy.__class__.__name__} (Config: {STRATEGY_TYPE})")

routing_service = RoutingService(
    fee_service=fee_service, 
    performance_repository=performance_repo,
    strategy=routing_strategy
)

# Ingestion
intelligence_strategy = StaticAggregationStrategy()
data_ingestor = DataIngestor(performance_repo, intelligence_strategy)

merchant_service = MerchantService(merchant_repo)
customer_service = CustomerService(customer_repo, merchant_repo)
payment_service = PaymentService(
    payment_repo=payment_repo,
    merchant_repo=merchant_repo,
    customer_repo=customer_repo,
    routing_service=routing_service,
    processor_registry=processor_registry
)

def get_payment_service():
    return payment_service

def get_merchant_service():
    return merchant_service

def get_customer_service():
    return customer_service
