from payments_service.app.core.repositories.merchant_repository import MerchantRepository
from payments_service.app.core.repositories.customer_repository import CustomerRepository
from payments_service.app.core.repositories.payment_repository import PaymentRepository
from payments_service.app.core.services.merchant_service import MerchantService
from payments_service.app.core.services.customer_service import CustomerService
from payments_service.app.core.services.payment_service import PaymentService

from payments_service.app.routing.preprocessing import RoutingService, FeeService
from payments_service.app.routing.decisioning import RoutingPerformanceRepository, StaticAggregationStrategy
from payments_service.app.routing.decisioning.decision_strategies import LLMDecisionStrategy, DeterministicLeastCostStrategy
from payments_service.app.routing.ingestion import DataIngestor

from payments_service.app.processors.adapters.stripe_adapter import StripeProcessor
from payments_service.app.processors.adapters.adyen_adapter import AdyenProcessor
from payments_service.app.processors.adapters.braintree_adapter import BraintreeProcessor
from payments_service.app.processors.adapters.internal_mock_adapter import InternalMockProcessor

from payments_service.app.processors.registry import ProcessorRegistry
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore, InMemoryRelationalStore
# Singletons for in-memory persistence
# We now use specialized stores for different access patterns.
# Even for relational data, we use separate stores to simulate different tables/collections.
merchant_store = InMemoryRelationalStore()
customer_store = InMemoryRelationalStore()
payment_store = InMemoryRelationalStore()
intelligence_store = InMemoryKeyValueStore()

merchant_repo = MerchantRepository(merchant_store)
customer_repo = CustomerRepository(customer_store)
payment_repo = PaymentRepository(payment_store)
performance_repo = RoutingPerformanceRepository(intelligence_store)

# Processors Registration
processor_registry = ProcessorRegistry()
processor_registry.register(PaymentProvider.STRIPE, StripeProcessor())
processor_registry.register(PaymentProvider.ADYEN, AdyenProcessor())
processor_registry.register(PaymentProvider.BRAINTREE, BraintreeProcessor())
processor_registry.register(PaymentProvider.INTERNAL, InternalMockProcessor())

# Services
fee_service = FeeService()

from payments_service.app.routing.decisioning.decision_strategies import AISUITE_AVAILABLE

if AISUITE_AVAILABLE:
    routing_strategy = LLMDecisionStrategy(objective="balanced")
else:
    # Fallback to deterministic strategy if AI suite is not available
    routing_strategy = DeterministicLeastCostStrategy()

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
