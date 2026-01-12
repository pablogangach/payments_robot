from typing import List, Any
from .models import RawTransactionRecord
from .interfaces import DataProvider
from ..decisioning.interfaces import IntelligenceStrategy
from ..decisioning.repository import RoutingPerformanceRepository

class DataIngestor:
    """
    Service responsible for orchestrating the ingestion of data from various providers
    and processing it through an intelligence strategy.
    """
    def __init__(
        self, 
        performance_repository: RoutingPerformanceRepository,
        intelligence_strategy: IntelligenceStrategy
    ):
        self.performance_repository = performance_repository
        self.intelligence_strategy = intelligence_strategy

    def ingest_from_provider(self, provider: DataProvider):
        """
        Fetches raw data from a provider, transforms it, and analyzes it.
        """
        raw_data = provider.fetch_data()
        
        # In this simplified version, we assume raw_data is already parsed 
        # into List[RawTransactionRecord] by the provider for convenience.
        # In a real scenario, there might be a separate Parsing layer.
        
        if not raw_data:
            return

        # Perform analysis
        performance_results = self.intelligence_strategy.analyze(raw_data)
        
        # Update repository
        for result in performance_results:
            self.performance_repository.save(result)
