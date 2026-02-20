from typing import List, Optional
from ..models.metadata import CardBIN, InterchangeFee
from .models import CardBINORM, InterchangeFeeORM
from .datastore import RelationalStore

class CardBINRepository:
    def __init__(self, store: RelationalStore[CardBIN]):
        self._store = store

    def save(self, card_bin: CardBIN) -> CardBIN:
        return self._store.save(card_bin.bin, card_bin)

    def find_by_bin(self, bin_prefix: str) -> Optional[CardBIN]:
        return self._store.find_by_id(bin_prefix)

    def list_all(self) -> List[CardBIN]:
        return self._store.list_all()

class InterchangeFeeRepository:
    def __init__(self, store: RelationalStore[InterchangeFee]):
        self._store = store

    def save(self, fee: InterchangeFee) -> InterchangeFee:
        # The store handles merge if ID is provided, but since we 
        # don't have a stable ID for fees yet, we use query-based match if needed.
        # For prototype, we'll just save.
        return self._store.save(None, fee)

    def list_all(self) -> List[InterchangeFee]:
        return self._store.list_all()
