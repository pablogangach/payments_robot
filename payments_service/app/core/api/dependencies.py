from payments_service.app.core.repositories.merchant_repository import MerchantRepository
from payments_service.app.core.repositories.customer_repository import CustomerRepository
from payments_service.app.core.repositories.payment_repository import PaymentRepository
from payments_service.app.core.services.merchant_service import MerchantService
from payments_service.app.core.services.customer_service import CustomerService
from payments_service.app.core.services.payment_service import PaymentService

from payments_service.app.routing.services.routing_service import RoutingService
from payments_service.app.routing.services.fee_service import FeeService

from payments_service.app.processors.adapters.stripe_adapter import StripeProcessor
from payments_service.app.processors.adapters.adyen_adapter import AdyenProcessor
from payments_service.app.processors.adapters.braintree_adapter import BraintreeProcessor
from payments_service.app.processors.adapters.internal_mock_adapter import InternalMockProcessor

from payments_service.app.processors.registry import ProcessorRegistry
from payments_service.app.core.models.payment import PaymentProvider

# Singletons for in-memory persistence
merchant_repo = MerchantRepository()
customer_repo = CustomerRepository()
payment_repo = PaymentRepository()

# Processors Registration
processor_registry = ProcessorRegistry()
processor_registry.register(PaymentProvider.STRIPE, StripeProcessor())
processor_registry.register(PaymentProvider.ADYEN, AdyenProcessor())
processor_registry.register(PaymentProvider.BRAINTREE, BraintreeProcessor())
processor_registry.register(PaymentProvider.INTERNAL, InternalMockProcessor())

# Services
fee_service = FeeService()
routing_service = RoutingService(fee_service=fee_service)

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
