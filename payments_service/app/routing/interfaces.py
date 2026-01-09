from abc import ABC, abstractmethod
from typing import List, Any
from payments_service.app.routing.models.ingestion import RawTransactionRecord
from payments_service.app.routing.models.routing_data import ProviderPerformance

class DataProvider(ABC):
    """
    Interface for various data sources that provide raw transaction data.
    """
    @abstractmethod
    def fetch_data(self) -> List[Any]:
        """
        Retrieves raw data from the specific source.
        """
        pass

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
