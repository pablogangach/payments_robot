from typing import Dict, Optional, List
from payments_service.app.core.models.merchant import Merchant

class MerchantRepository:
    def __init__(self):
        # In-memory storage: merchant_id -> Merchant
        self._store: Dict[str, Merchant] = {}

    def save(self, merchant: Merchant) -> Merchant:
        # Check uniqueness constraints by scanning
        # Since this is an in-memory test repo, O(N) is acceptable and simpler
        for existing in self._store.values():
            if existing.tax_id == merchant.tax_id and existing.id != merchant.id:
                 raise ValueError(f"Merchant with Tax ID {merchant.tax_id} already exists.")
            
        self._store[merchant.id] = merchant
        return merchant

    def find_by_id(self, merchant_id: str) -> Optional[Merchant]:
        return self._store.get(merchant_id)

    def find_by_tax_id(self, tax_id: str) -> Optional[Merchant]:
        for merchant in self._store.values():
            if merchant.tax_id == tax_id:
                return merchant
        return None
