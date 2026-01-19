from typing import Optional, List
from payments_service.app.core.models.customer import Customer
from .datastore import DataStore

class CustomerRepository:
    def __init__(self, store: DataStore[Customer]):
        self._store = store

    def save(self, customer: Customer) -> Customer:
        return self._store.save(customer.id, customer)

    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        return self._store.get(customer_id)

    def find_by_merchant_id(self, merchant_id: str) -> List[Customer]:
        return self._store.find_by(lambda c: c.merchant_id == merchant_id)
