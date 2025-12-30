from payments_service.app.gateways.base import PaymentProcessor
from payments_service.app.models.gateway import InternalChargeRequest, InternalChargeResponse, ProcessorStatus
import uuid

class AdyenProcessor(PaymentProcessor):
    """
    Placeholder adapter for Adyen Payment Gateway.
    """
    
    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        # Simulate Adyen success logic
        return InternalChargeResponse(
            status=ProcessorStatus.SUCCESS,
            processor_transaction_id=f"adyen_{uuid.uuid4().hex[:12]}",
            raw_response={"provider": "adyen", "risk_score": 0}
        )

    def refund(self, processor_transaction_id: str, amount: float) -> InternalChargeResponse:
        return InternalChargeResponse(status=ProcessorStatus.SUCCESS)

    @property
    def provider_name(self) -> str:
        return "adyen"
