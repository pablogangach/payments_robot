from abc import ABC, abstractmethod
from typing import List
from ..ingestion.models import RawTransactionRecord
from .models import ProviderPerformance

class IntelligenceStrategy(ABC):
    """
    Strategy pattern for processing raw data into actionable performance metrics.
    """
    @abstractmethod
    def analyze(self, records: List[RawTransactionRecord]) -> List[ProviderPerformance]:
        """
        Processes canonical transaction records and produces provider performance data.
        """
        pass
