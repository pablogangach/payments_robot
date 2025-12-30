from typing import List
from payments_service.app.routing.models.routing_data import ProviderPerformance, RoutingDimension
from payments_service.app.core.models.payment import PaymentProvider
from app.repositories.performance_repository import RoutingPerformanceRepository

class RoutingDataManager:
    """
    Manager service responsible for ingesting and updating routing data.
    This is the 'Writer' in the CQRS-like split.
    """

    def __init__(self, performance_repository: RoutingPerformanceRepository):
        self.performance_repository = performance_repository

    def update_performance(self, performance: ProviderPerformance):
        """
        Updates (or adds) a performance record for a specific provider and dimension.
        """
        self.performance_repository.save(performance)

    def ingest_bulk_data(self, performances: List[ProviderPerformance]):
        """
        Ingest multiple performance records at once.
        """
        for p in performances:
            self.update_performance(p)
