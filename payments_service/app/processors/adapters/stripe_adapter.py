from payments_service.app.processors.interfaces import PaymentProcessor
from payments_service.app.processors.models import InternalChargeRequest, InternalChargeResponse, ProcessorStatus
import requests
import os

class StripeProcessor(PaymentProcessor):
    """
    Adapter for Stripe Payment Gateway.
    Maps InternalChargeRequest to Stripe's PaymentIntent API.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STRIPE_API_KEY", "sk_test_mock")

    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        # In a real implementation:
        # response = requests.post("https://api.stripe.com/v1/payment_intents", ...)
        
        # Simulation for contract demonstration
        if request.amount > 10000: # Simulate failure for large amounts in test
             return InternalChargeResponse(
                status=ProcessorStatus.FAILURE,
                error_code="amount_too_large",
                error_message="Simulated error: Amount exceeds test limit"
            )

        return InternalChargeResponse(
            status=ProcessorStatus.SUCCESS,
            processor_transaction_id=f"pi_mock_{os.urandom(4).hex()}",
            raw_response={"provider": "stripe", "fee": request.amount * 0.029 + 0.3}
        )

    def refund(self, processor_transaction_id: str, amount: float) -> InternalChargeResponse:
        return InternalChargeResponse(status=ProcessorStatus.SUCCESS)

    @property
    def provider_name(self) -> str:
        return "stripe"
