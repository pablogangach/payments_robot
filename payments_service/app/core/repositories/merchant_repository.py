from typing import Optional, List
from payments_service.app.core.models.merchant import Merchant
from .datastore import DataStore

class MerchantRepository:
    def __init__(self, store: DataStore[Merchant]):
        self._store = store

    def save(self, merchant: Merchant) -> Merchant:
        # Check uniqueness constraints by scanning
        existing_with_tax_id = self.find_by_tax_id(merchant.tax_id)
        if existing_with_tax_id and existing_with_tax_id.id != merchant.id:
             raise ValueError(f"Merchant with Tax ID {merchant.tax_id} already exists.")
            
        return self._store.save(merchant.id, merchant)

    def find_by_id(self, merchant_id: str) -> Optional[Merchant]:
        return self._store.get(merchant_id)

    def find_by_tax_id(self, tax_id: str) -> Optional[Merchant]:
        results = self._store.find_by(lambda m: m.tax_id == tax_id)
        return results[0] if results else None
