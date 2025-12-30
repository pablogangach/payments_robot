from payments_service.app.gateways.base import PaymentProcessor
from payments_service.app.models.gateway import InternalChargeRequest, InternalChargeResponse, ProcessorStatus
import uuid

class InternalMockProcessor(PaymentProcessor):
    """
    Mock processor for internal testing and E2E visualization.
    """
    
    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        # Simulate local success logic
        return InternalChargeResponse(
            status=ProcessorStatus.SUCCESS,
            processor_transaction_id=f"mock_txn_{uuid.uuid4().hex[:8]}",
            raw_response={"simulated": True, "fee": 0.05}
        )

    def refund(self, processor_transaction_id: str, amount: float) -> InternalChargeResponse:
        return InternalChargeResponse(status=ProcessorStatus.SUCCESS)

    @property
    def provider_name(self) -> str:
        return "internal"
