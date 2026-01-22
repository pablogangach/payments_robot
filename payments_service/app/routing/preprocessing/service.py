import json
from typing import List, Optional
import aisuite
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider, PaymentProvider
from .models import (
    FeeStructure, 
    PaymentContext, 
    PaymentRoute, 
    Customer, 
    PaymentMethodDetails, 
    Product, 
    BillingType
)
from ..decisioning.models import RoutingDimension
from ..decisioning.repository import RoutingPerformanceRepository

class FeeService:
    def __init__(self):
        # In a real application, this would come from a database.
        self.fees: List[FeeStructure] = [
            FeeStructure(
                provider=PaymentProvider.STRIPE,
                region="domestic",
                fixed_fee=0.30,
                variable_fee_percent=2.9,
            ),
            FeeStructure(
                provider=PaymentProvider.STRIPE,
                region="international",
                fixed_fee=0.30,
                variable_fee_percent=3.9,
            ),
            FeeStructure(
                provider=PaymentProvider.INTERNAL,
                region="domestic",
                card_type="debit",
                fixed_fee=0.25,
                variable_fee_percent=1.0,
            ),
            FeeStructure(
                provider=PaymentProvider.INTERNAL,
                fixed_fee=0.50,
                variable_fee_percent=2.5,
            ),
        ]

    def get_all_fees(self) -> List[FeeStructure]:
        return self.fees

from ..decisioning.interfaces import RoutingDecisionStrategy
from ..decisioning.decision_strategies import LLMDecisionStrategy

class RoutingService:
    def __init__(
        self, 
        fee_service: FeeService, 
        performance_repository: RoutingPerformanceRepository,
        strategy: Optional[RoutingDecisionStrategy] = None
    ):
        self.fee_service = fee_service
        self.performance_repository = performance_repository
        # Default to LLM strategy if none provided
        self.strategy = strategy or LLMDecisionStrategy()

    def find_best_route(self, payment_create: PaymentCreate) -> PaymentProvider:
        """
        Uses the injected strategy to determine the best payment provider.
        """
        if payment_create.provider:
            return payment_create.provider

        # 1. Gather context
        all_fees = self.fee_service.get_all_fees()
        all_performance = self.performance_repository.get_all()
        
        # 2. Delegate to strategy
        provider = self.strategy.decide(
            payment_in=payment_create,
            performance_data=all_performance,
            fees=all_fees
        )
        
        print(f"Routing Decision: Strategy {self.strategy.__class__.__name__} chose '{provider.value}'")
        return provider

class PreprocessingService:
    """
    Service to handle pre-processing of payments, such as preparing routes for recurring payments.
    """
    def __init__(self, performance_repository: RoutingPerformanceRepository):
        self.performance_repository = performance_repository

    def preprocess_recurrent_payment(
        self, 
        customer: Customer, 
        payment_method: PaymentMethodDetails, 
        product: Product, 
        billing_type: BillingType
    ) -> PaymentRoute:
        context = PaymentContext(
            payment_method=payment_method,
            customer=customer,
            product=product,
            billing_type=billing_type
        )
        return self._determine_route(context)

    def _determine_route(self, context: PaymentContext) -> PaymentRoute:
        # 1. Build Dimension from Context
        dimension = RoutingDimension(
            payment_method_type=context.payment_method.type,
            payment_form="card_on_file",
            network="visa",
            card_type="credit",
            region="domestic",
            currency="USD"
        )

        # 2. Get Candidates via Repository
        candidates = self.performance_repository.find_by_dimension(dimension)
        
        if not candidates:
            return PaymentRoute(
                processor=PaymentProvider.STRIPE,
                routing_reason="Default Fallback"
            )

        # 3. Select Best
        best_candidate = min(candidates, key=lambda c: c.metrics.cost_structure.fixed_fee)

        return PaymentRoute(
            processor=best_candidate.provider,
            routing_reason=f"Selected based on lowest fixed fee: {best_candidate.metrics.cost_structure.fixed_fee}"
        )
