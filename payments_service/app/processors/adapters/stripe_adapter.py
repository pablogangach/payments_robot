import stripe
import os
from payments_service.app.processors.interfaces import PaymentProcessor
from payments_service.app.processors.models.gateway import InternalChargeRequest, InternalChargeResponse, ProcessorStatus

class StripeProcessor(PaymentProcessor):
    """
    Adapter for Stripe Payment Gateway.
    Maps InternalChargeRequest to Stripe's PaymentIntent API.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STRIPE_API_KEY")
        if self.api_key:
            stripe.api_key = self.api_key

    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        if not self.api_key or self.api_key == "sk_test_mock":
            # Fallback to simulation if no real key is provided
            return self._simulate_charge(request)

        try:
            # Create a PaymentIntent in Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(request.amount * 100), # Stripe expects amounts in cents
                currency=request.currency.lower(),
                payment_method=request.payment_method_token,
                confirm=True,
                description=request.description,
                metadata=request.metadata,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
            )

            return InternalChargeResponse(
                status=ProcessorStatus.SUCCESS,
                processor_transaction_id=intent.id,
                raw_response=intent.to_dict()
            )
        except stripe.error.StripeError as e:
            return InternalChargeResponse(
                status=ProcessorStatus.FAILURE,
                error_code=e.code or "stripe_error",
                error_message=str(e),
                raw_response=e.json_body if hasattr(e, "json_body") else {}
            )
        except Exception as e:
            return InternalChargeResponse(
                status=ProcessorStatus.FAILURE,
                error_code="internal_error",
                error_message=f"Unexpected error: {str(e)}"
            )

    def _simulate_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        """Fallback mock logic for testing without keys."""
        if request.amount > 10000:
             return InternalChargeResponse(
                status=ProcessorStatus.FAILURE,
                error_code="amount_too_large",
                error_message="Simulated error: Amount exceeds test limit"
            )

        return InternalChargeResponse(
            status=ProcessorStatus.SUCCESS,
            processor_transaction_id=f"pi_mock_{os.urandom(4).hex()}",
            raw_response={"provider": "stripe", "fee": request.amount * 0.029 + 0.3, "mode": "simulated"}
        )

    def refund(self, processor_transaction_id: str, amount: float) -> InternalChargeResponse:
        try:
            if not self.api_key or self.api_key == "sk_test_mock":
                return InternalChargeResponse(status=ProcessorStatus.SUCCESS)
                
            refund_params = {
                "payment_intent": processor_transaction_id,
            }
            if amount is not None:
                refund_params["amount"] = int(amount * 100)
                
            refund = stripe.Refund.create(**refund_params)
            return InternalChargeResponse(
                status=ProcessorStatus.SUCCESS,
                processor_transaction_id=refund.id,
                raw_response=refund.to_dict()
            )
        except Exception as e:
            return InternalChargeResponse(
                status=ProcessorStatus.FAILURE,
                error_code="refund_failed",
                error_message=str(e)
            )

    @property
    def provider_name(self) -> str:
        return "stripe"
