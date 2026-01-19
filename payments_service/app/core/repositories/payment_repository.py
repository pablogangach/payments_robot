from typing import Optional, List
from payments_service.app.core.models.payment import Payment
from .datastore import DataStore

class PaymentRepository:
    def __init__(self, store: DataStore[Payment]):
        self._store = store

    def save(self, payment: Payment) -> Payment:
        return self._store.save(payment.id, payment)

    def find_by_id(self, payment_id: str) -> Optional[Payment]:
        return self._store.get(payment_id)

    def find_all(self) -> List[Payment]:
        return self._store.get_all()
