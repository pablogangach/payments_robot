from typing import List
from .interfaces import DataProvider
from .models import RawTransactionRecord
from ..decisioning.feedback import FeedbackStore

class InternalFeedbackDataProvider(DataProvider):
    """
    Data provider that retrieves transactional feedback stored internally.
    """
    def __init__(self, store: FeedbackStore):
        self.store = store

    def fetch_data(self) -> List[RawTransactionRecord]:
        """
        Retrieves all records currently in the feedback store.
        """
        return self.store.get_all_records()
