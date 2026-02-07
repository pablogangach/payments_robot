from abc import ABC, abstractmethod
from typing import List, Optional, Any
from ..ingestion.models import RawTransactionRecord
from .models import ProviderPerformance, RoutingDimension, ResolvedProvider
from payments_service.app.core.models.payment import PaymentProvider, PaymentCreate

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

class RoutingDecisionStrategy(ABC):
    """
    Interface for making the final routing decision.
    """
    @abstractmethod
    def decide(self, payment_in: PaymentCreate, providers: List[ResolvedProvider]) -> PaymentProvider:
        """
        Determines the best provider based on available context and performance.
        """
        pass
