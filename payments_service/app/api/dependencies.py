from payments_service.app.repositories.merchant_repository import MerchantRepository
from payments_service.app.repositories.customer_repository import CustomerRepository
from payments_service.app.services.merchant_service import MerchantService
from payments_service.app.services.customer_service import CustomerService

# Singletons for in-memory persistence
merchant_repo = MerchantRepository()
customer_repo = CustomerRepository()

merchant_service = MerchantService(merchant_repo)
customer_service = CustomerService(customer_repo, merchant_repo)

def get_merchant_service():
    return merchant_service

def get_customer_service():
    return customer_service
