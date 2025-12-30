from abc import ABC, abstractmethod
from payments_service.app.models.gateway import InternalChargeRequest, InternalChargeResponse

class PaymentProcessor(ABC):
    """
    Interface definition for all payment gateway adapters.
    This is the core contract for payment execution.
    """
    
    @abstractmethod
    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        """
        Execute a payment charge.
        """
        pass

    @abstractmethod
    def refund(self, processor_transaction_id: str, amount: float) -> InternalChargeResponse:
        """
        Refund a previously executed charge.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the name of the provider (e.g. 'stripe').
        """
        pass
