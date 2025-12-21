from typing import List, Dict, Optional
from app.models.payment import PaymentProvider
from app.models.routing_data import (
    ProviderPerformance, 
    RoutingDimension, 
    PerformanceMetrics, 
    CostStructure
)

class RoutingPerformanceRepository:
    """
    Repository responsible for storing and retrieving provider performance metrics.
    Abstracts the data storage (In-Memory, Redis, DB).
    """

    def __init__(self):
        # In-memory store: Map[RoutingDimension, List[ProviderPerformance]]
        self._store: Dict[tuple, List[ProviderPerformance]] = {}
        self._initialize_mock_data()

    def find_by_dimension(self, dimension: RoutingDimension) -> List[ProviderPerformance]:
        """
        Retrieves performance metrics for all providers matching the given dimension.
        """
        key = self._make_key(dimension)
        return self._store.get(key, [])

    def save(self, performance: ProviderPerformance):
        """
        Updates (or adds) a performance record for a specific provider and dimension.
        """
        key = self._make_key(performance.dimension)
        
        if key not in self._store:
            self._store[key] = []

        # Remove existing record for this provider if exists
        self._store[key] = [
            p for p in self._store[key] 
            if p.provider != performance.provider
        ]
        self._store[key].append(performance)

    def _make_key(self, dimension: RoutingDimension) -> tuple:
        # Convert model to frozenset of items to be used as a dict key
        return tuple(sorted(dimension.model_dump().items()))

    def _initialize_mock_data(self):
        """
        Populate with some initial data for testing.
        """
        # 1. Domestic Visa Credit - Stripe (Good auth, Higher cost)
        dim_us_visa_credit = RoutingDimension(
            payment_method_type="credit_card",
            network="visa",
            card_type="credit",
            region="domestic",
            currency="USD",
            is_network_tokenized=False
        )
        
        stripe_perf = ProviderPerformance(
            provider=PaymentProvider.STRIPE,
            dimension=dim_us_visa_credit,
            metrics=PerformanceMetrics(
                auth_rate=0.98,
                fraud_rate=0.002,
                avg_latency_ms=300,
                cost_structure=CostStructure(
                    variable_fee_percent=2.9,
                    fixed_fee=0.30
                )
            )
        )
        self.save(stripe_perf)

        # 2. Domestic Visa Credit - Internal/Local (Lower auth, Cheaper)
        internal_perf = ProviderPerformance(
            provider=PaymentProvider.INTERNAL,
            dimension=dim_us_visa_credit,
            metrics=PerformanceMetrics(
                auth_rate=0.92,
                fraud_rate=0.005,
                avg_latency_ms=600,
                cost_structure=CostStructure(
                    variable_fee_percent=2.2,
                    fixed_fee=0.10
                )
            )
        )
        self.save(internal_perf)
