from typing import Dict, Optional
from payments_service.app.processors.interfaces import PaymentProcessor
from payments_service.app.core.models.payment import PaymentProvider

class ProcessorRegistry:
    """
    Central registry for payment processor implementations.
    Provides a simple way to register and retrieve processors.
    """
    def __init__(self):
        self._processors: Dict[str, PaymentProcessor] = {}

    def register(self, provider: PaymentProvider, processor: PaymentProcessor):
        """
        Registers a processor for a given provider.
        """
        self._processors[provider.value] = processor

    def get_processor(self, provider: PaymentProvider) -> Optional[PaymentProcessor]:
        """
        Retrieves the processor for a given provider.
        """
        return self._processors.get(provider.value)

    def list_providers(self) -> list[str]:
        """
        Lists all registered providers.
        """
        return list(self._processors.keys())
