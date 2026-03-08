import braintree
import os
from typing import Optional, Dict, Any
from payments_service.app.processors.interfaces import PaymentProcessor
from payments_service.app.processors.models import InternalChargeRequest, InternalChargeResponse

class BraintreeProcessor(PaymentProcessor):
    """
    Braintree implementation of the PaymentProcessor interface.
    Uses the official Braintree Python SDK.
    """

    def __init__(self, merchant_id: str, public_key: str, private_key: str, environment: str = "sandbox"):
        braintree_env = braintree.Environment.Sandbox if environment == "sandbox" else braintree.Environment.Production
        self.gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                braintree_env,
                merchant_id=merchant_id,
                public_key=public_key,
                private_key=private_key
            )
        )

    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        """
        Execute a payment charge using Braintree's 'sale' method.
        """
        nonce = "fake-valid-nonce"
        
        try:
            result = self.gateway.transaction.sale({
                "amount": f"{request.amount:.2f}",
                "payment_method_nonce": nonce,
                "options": {
                    "submit_for_settlement": True
                }
            })

            if result.is_success:
                return InternalChargeResponse(
                    status="success",
                    processor_transaction_id=result.transaction.id,
                    raw_response={
                        "id": result.transaction.id,
                        "status": result.transaction.status,
                        "type": result.transaction.type,
                        "amount": str(result.transaction.amount)
                    }
                )
            else:
                error_message = result.message if hasattr(result, 'message') else "Unknown Braintree Error"
                return InternalChargeResponse(
                    status="failure",
                    error_message=f"Braintree Sale Failed: {error_message}",
                    raw_response={"errors": [e.message for e in result.errors.deep_errors]}
                )
        except Exception as e:
            return InternalChargeResponse(
                status="failure",
                error_message=f"Braintree SDK Error: {str(e)}",
                raw_response={"error_type": type(e).__name__}
            )

    def refund(self, processor_transaction_id: str, amount: Optional[float] = None) -> InternalChargeResponse:
        """
        Refund a previously executed Braintree transaction.
        Handles both 'void' (if not yet settled) and 'refund' (if settled).
        """
        try:
            # 1. Check transaction status to decide between void and refund
            tx = self.gateway.transaction.find(processor_transaction_id)
            
            # Non-settled transactions (authorized, submitted_for_settlement, settling) should be voided
            # Note: partial void is not possible, it's always the full amount.
            if tx.status in [
                braintree.Transaction.Status.Authorized,
                braintree.Transaction.Status.SubmittedForSettlement,
                braintree.Transaction.Status.Settling
            ]:
                result = self.gateway.transaction.void(processor_transaction_id)
                action = "Void"
            else:
                # Settled transactions can be refunded (full or partial)
                result = self.gateway.transaction.refund(processor_transaction_id, amount)
                action = "Refund"

            if result.is_success:
                return InternalChargeResponse(
                    status="success",
                    processor_transaction_id=result.transaction.id,
                    raw_response={
                        "id": result.transaction.id,
                        "status": result.transaction.status,
                        "action_taken": action
                    }
                )
            else:
                error_message = result.message if hasattr(result, 'message') else f"Unknown Braintree {action} Error"
                return InternalChargeResponse(
                    status="failure",
                    error_message=f"Braintree {action} Failed: {error_message}",
                    raw_response={"errors": [e.message for e in result.errors.deep_errors]}
                )
        except Exception as e:
            return InternalChargeResponse(
                status="failure",
                error_message=f"Braintree SDK {action if 'action' in locals() else 'Refund'} Error: {str(e)}",
                raw_response={"error_type": type(e).__name__}
            )

    @property
    def provider_name(self) -> str:
        return "braintree"
