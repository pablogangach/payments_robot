from typing import Dict, Optional, List
from payments_service.app.models.payment import Payment

class PaymentRepository:
    def __init__(self):
        # In-memory storage: payment_id -> Payment
        self._store: Dict[str, Payment] = {}

    def save(self, payment: Payment) -> Payment:
        self._store[payment.id] = payment
        return payment

    def find_by_id(self, payment_id: str) -> Optional[Payment]:
        return self._store.get(payment_id)

    def find_all(self) -> List[Payment]:
        return list(self._store.values())
