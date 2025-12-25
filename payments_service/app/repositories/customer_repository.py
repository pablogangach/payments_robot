from typing import Dict, Optional, List
from payments_service.app.models.customer import Customer

class CustomerRepository:
    def __init__(self):
        # In-memory storage: customer_id -> Customer
        self._store: Dict[str, Customer] = {}

    def save(self, customer: Customer) -> Customer:
        self._store[customer.id] = customer
        return customer

    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        return self._store.get(customer_id)

    def find_by_merchant_id(self, merchant_id: str) -> List[Customer]:
        return [c for c in self._store.values() if c.merchant_id == merchant_id]
