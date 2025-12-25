from datetime import datetime, timezone
from payments_service.app.models.payment import Payment, PaymentCreate, PaymentStatus
from payments_service.app.repositories.payment_repository import PaymentRepository
from payments_service.app.repositories.merchant_repository import MerchantRepository
from payments_service.app.repositories.customer_repository import CustomerRepository
from payments_service.app.services.routing_service import RoutingService

class PaymentService:
    def __init__(
        self, 
        payment_repo: PaymentRepository, 
        merchant_repo: MerchantRepository, 
        customer_repo: CustomerRepository,
        routing_service: RoutingService
    ):
        self.payment_repo = payment_repo
        self.merchant_repo = merchant_repo
        self.customer_repo = customer_repo
        self.routing_service = routing_service

    def create_charge(self, charge_in: PaymentCreate) -> Payment:
        # 1. Validate Merchant
        merchant = self.merchant_repo.find_by_id(charge_in.merchant_id)
        if not merchant:
            raise KeyError(f"Merchant {charge_in.merchant_id} not found")

        # 2. Validate Customer
        customer = self.customer_repo.find_by_id(charge_in.customer_id)
        if not customer:
            raise KeyError(f"Customer {charge_in.customer_id} not found")

        # 3. Routing Decision (Simplified for E2E visualization)
        # In a real flow, this would call the Routing Engine
        try:
            provider = self.routing_service.find_best_route(charge_in)
            reason = "AI Routing Decision"
        except Exception:
            from payments_service.app.models.payment import PaymentProvider
            provider = PaymentProvider.STRIPE
            reason = "Fallback: Routing Engine Unavailable"

        # 4. Create Payment Record
        payment = Payment(
            **charge_in.model_dump(),
            provider=provider,
            routing_decision=reason,
            status=PaymentStatus.PENDING # Usually pending until processor confirms
        )
        
        # 5. Execute with Provider (Simulation)
        # if provider == STRIPE: stripe.PaymentIntent.create(...)
        # For this vertical slice, we simulate immediate success
        payment.status = PaymentStatus.COMPLETED
        payment.updated_at = datetime.now(timezone.utc)

        return self.payment_repo.save(payment)

    def get_payment(self, payment_id: str) -> Payment:
        payment = self.payment_repo.find_by_id(payment_id)
        if not payment:
            raise KeyError(f"Payment {payment_id} not found")
        return payment
