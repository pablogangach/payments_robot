from typing import Optional, List
import uuid
from datetime import datetime, timezone # Keep this for now, as it's not explicitly removed and might be used elsewhere, though now_utc is preferred.
from payments_service.app.core.models.payment import Payment, PaymentCreate, PaymentStatus, PaymentProvider
from payments_service.app.core.models.merchant import Merchant, MerchantCreate
from payments_service.app.core.repositories.payment_repository import PaymentRepository
from payments_service.app.core.repositories.merchant_repository import MerchantRepository
from payments_service.app.core.repositories.customer_repository import CustomerRepository
from payments_service.app.core.repositories.precalculated_route_repository import PrecalculatedRouteRepository
from payments_service.app.routing.preprocessing import RoutingService
from payments_service.app.processors.registry import ProcessorRegistry
from payments_service.app.core.utils.datetime_utils import now_utc, normalize_to_utc

class PaymentService:
    def __init__(
        self, 
        payment_repo: PaymentRepository, 
        merchant_repo: MerchantRepository, 
        customer_repo: CustomerRepository,
        routing_service: RoutingService,
        processor_registry: ProcessorRegistry,
        precalculated_route_repository: Optional[PrecalculatedRouteRepository] = None,
        feedback_collector: Optional['FeedbackCollector'] = None
    ):
        self.payment_repo = payment_repo
        self.merchant_repo = merchant_repo
        self.customer_repo = customer_repo
        self.routing_service = routing_service
        self.processor_registry = processor_registry
        self.precalculated_route_repository = precalculated_route_repository
        self.feedback_collector = feedback_collector

    def create_charge(self, charge_in: PaymentCreate) -> Payment:
        # 1. Validate Entities
        merchant = self.merchant_repo.find_by_id(charge_in.merchant_id)
        if not merchant:
            raise KeyError(f"Merchant {charge_in.merchant_id} not found")

        customer = self.customer_repo.find_by_id(charge_in.customer_id)
        if not customer:
            raise KeyError(f"Customer {charge_in.customer_id} not found")

        # 2. Routing Decision
        provider_type = None
        reason = None

        # Check for pre-calculated route if it's a subscription renewal
        if charge_in.subscription_id and self.precalculated_route_repository:
            precalc = self.precalculated_route_repository.find_by_subscription_id(charge_in.subscription_id)
            if precalc and precalc.expires_at > now_utc():
                provider_type = precalc.provider
                reason = f"Pre-calculated: {precalc.routing_decision}"
                print(f"Using pre-calculated route for subscription {charge_in.subscription_id}: {provider_type.value}")

        if not provider_type:
            try:
                provider_type = self.routing_service.find_best_route(charge_in)
                reason = "AI Routing Decision (Live)"
            except Exception:
                from payments_service.app.core.models.payment import PaymentProvider
                provider_type = PaymentProvider.STRIPE
                reason = "Fallback: Routing Engine Unavailable"

        # 3. Get Processor Adapter
        processor = self.processor_registry.get_processor(provider_type)
        if not processor:
            raise ValueError(f"No processor registered for {provider_type}")

        # 4. Standardized Execution Contract
        from payments_service.app.processors.models import InternalChargeRequest
        internal_req = InternalChargeRequest(
            amount=charge_in.amount,
            currency=charge_in.currency,
            payment_method_token=customer.payment_method_token,
            merchant_id=charge_in.merchant_id,
            customer_id=charge_in.customer_id,
            description=charge_in.description
        )
        
        processor_resp = processor.process_charge(internal_req)

        # 5. Map Result to Payment Record
        payment = Payment(
            **charge_in.model_dump(exclude={'provider'}),
            provider=provider_type,
            routing_decision=reason,
            status=PaymentStatus.COMPLETED if processor_resp.status == "success" else PaymentStatus.FAILED,
            provider_payment_id=processor_resp.processor_transaction_id,
            updated_at=now_utc()
        )

        saved_payment = self.payment_repo.save(payment)

        # 6. Feedback Loop
        if self.feedback_collector:
            self.feedback_collector.collect(saved_payment)

        return saved_payment

    def get_payment(self, payment_id: str) -> Payment:
        payment = self.payment_repo.find_by_id(payment_id)
        if not payment:
            raise KeyError(f"Payment {payment_id} not found")
        return payment
