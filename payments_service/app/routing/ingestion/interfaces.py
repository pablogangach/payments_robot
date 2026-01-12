from abc import ABC, abstractmethod
from typing import List, Any

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
