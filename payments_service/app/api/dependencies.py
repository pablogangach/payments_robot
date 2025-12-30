from payments_service.app.repositories.merchant_repository import MerchantRepository
from payments_service.app.repositories.customer_repository import CustomerRepository
from payments_service.app.repositories.payment_repository import PaymentRepository
from payments_service.app.services.merchant_service import MerchantService
from payments_service.app.services.customer_service import CustomerService
from payments_service.app.services.payment_service import PaymentService
from payments_service.app.services.routing_service import RoutingService
from payments_service.app.services.fee_service import FeeService

from payments_service.app.gateways.stripe_adapter import StripeProcessor
from payments_service.app.gateways.adyen_adapter import AdyenProcessor
from payments_service.app.gateways.braintree_adapter import BraintreeProcessor
from payments_service.app.gateways.internal_mock_adapter import InternalMockProcessor

# Singletons for in-memory persistence
merchant_repo = MerchantRepository()
customer_repo = CustomerRepository()
payment_repo = PaymentRepository()

# Processors
processors = {
    "stripe": StripeProcessor(),
    "adyen": AdyenProcessor(),
    "braintree": BraintreeProcessor(),
    "internal": InternalMockProcessor()
}

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
    processors=processors
)

def get_payment_service():
    return payment_service

def get_merchant_service():
    return merchant_service

def get_customer_service():
    return customer_service
