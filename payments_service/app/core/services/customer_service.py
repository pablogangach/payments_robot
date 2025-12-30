from payments_service.app.core.models.customer import Customer, CustomerCreate
from payments_service.app.core.repositories.customer_repository import CustomerRepository
from payments_service.app.core.repositories.merchant_repository import MerchantRepository

class CustomerService:
    def __init__(self, customer_repo: CustomerRepository, merchant_repo: MerchantRepository):
        self.customer_repo = customer_repo
        self.merchant_repo = merchant_repo

    def create_customer(self, customer_in: CustomerCreate) -> Customer:
        # Validate merchant existence
        merchant = self.merchant_repo.find_by_id(customer_in.merchant_id)
        if not merchant:
            raise KeyError(f"Merchant {customer_in.merchant_id} not found")

        # Create customer
        customer = Customer(**customer_in.model_dump())
        return self.customer_repo.save(customer)

    def get_customer(self, customer_id: str) -> Customer:
        customer = self.customer_repo.find_by_id(customer_id)
        if not customer:
            raise KeyError(f"Customer {customer_id} not found")
        return customer
