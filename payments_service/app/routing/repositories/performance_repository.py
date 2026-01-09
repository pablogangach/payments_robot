from typing import List, Optional
from payments_service.app.routing.models.routing_data import ProviderPerformance, RoutingDimension

class RoutingPerformanceRepository:
    """
    In-memory repository for storing and querying provider performance data.
    Designed for fast dimension-based lookups.
    """
    def __init__(self):
        # Keyed by RoutingDimension (which is frozen/hashable)
        self._data: dict[RoutingDimension, List[ProviderPerformance]] = {}

    def save(self, performance: ProviderPerformance):
        """
        Upserts a performance record.
        """
        dimension = performance.dimension
        if dimension not in self._data:
            self._data[dimension] = []
        
        # Simple upsert logic: replace if provider already exists for this dimension
        existing_records = self._data[dimension]
        for i, record in enumerate(existing_records):
            if record.provider == performance.provider:
                existing_records[i] = performance
                return
        
        existing_records.append(performance)

    def find_by_dimension(self, dimension: RoutingDimension) -> List[ProviderPerformance]:
        """
        Returns all provider performance records matching the specific dimension.
        """
        return self._data.get(dimension, [])

    def get_all(self) -> List[ProviderPerformance]:
        """
        Returns all performance records across all dimensions.
        """
        all_records = []
        for records in self._data.values():
            all_records.extend(records)
        return all_records
