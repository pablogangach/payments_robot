from payments_service.app.processors.interfaces import PaymentProcessor
from payments_service.app.processors.models import InternalChargeRequest, InternalChargeResponse, ProcessorStatus
import uuid

class BraintreeProcessor(PaymentProcessor):
    """
    Placeholder adapter for Braintree Payment Gateway.
    """
    
    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        # Simulate Braintree success logic
        return InternalChargeResponse(
            status=ProcessorStatus.SUCCESS,
            processor_transaction_id=f"bt_{uuid.uuid4().hex[:10]}",
            raw_response={"provider": "braintree", "cvv_verification": "match"}
        )

    def refund(self, processor_transaction_id: str, amount: float) -> InternalChargeResponse:
        return InternalChargeResponse(status=ProcessorStatus.SUCCESS)

    @property
    def provider_name(self) -> str:
        return "braintree"
