from typing import List, Optional
from .models import ProviderPerformance, RoutingDimension
from ...core.repositories.datastore import KeyValueStore

class RoutingPerformanceRepository:
    """
    Repository for storing and querying provider performance data.
    Designed for fast dimension-based lookups using a Key-Value approach.
    """
    def __init__(self, store: KeyValueStore[List[ProviderPerformance]]):
        self._store = store

    def _get_key(self, dimension: RoutingDimension) -> str:
        # Use the model_dump_json for a stable hashable string key
        return dimension.model_dump_json()

    def save(self, performance: ProviderPerformance):
        """
        Upserts a performance record.
        """
        key = self._get_key(performance.dimension)
        existing_records = self._store.get(key) or []
        
        # Simple upsert logic: replace if provider already exists for this dimension
        updated = False
        for i, record in enumerate(existing_records):
            if record.provider == performance.provider:
                existing_records[i] = performance
                updated = True
                break
        
        if not updated:
            existing_records.append(performance)
        
        self._store.set(key, existing_records)

    def find_by_dimension(self, dimension: RoutingDimension) -> List[ProviderPerformance]:
        """
        Returns all provider performance records matching the specific dimension.
        """
        key = self._get_key(dimension)
        return self._store.get(key) or []

    def get_all(self) -> List[ProviderPerformance]:
        """
        Returns all performance records across all dimensions.
        """
        all_records = []
        for records_list in self._store.get_all():
            all_records.extend(records_list)
        return all_records
