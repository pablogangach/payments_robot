import json
import redis
from typing import List, Optional
try:
    import aisuite
except ImportError:
    pass
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from .models import (
    FeeStructure, 
    PaymentContext, 
    PaymentRoute, 
    Customer, 
    PaymentMethodDetails, 
    Product, 
    BillingType
)
from ...core.models.subscription import Subscription
from ...core.models.precalculated_route import PrecalculatedRouteCreate
from ...core.repositories.subscription_repository import SubscriptionRepository
from ...core.repositories.precalculated_route_repository import PrecalculatedRouteRepository
from ...core.repositories.metadata_repository import CardBINRepository, InterchangeFeeRepository
from ..decisioning.models import RoutingDimension, ResolvedProvider
from ..decisioning.repository import RoutingPerformanceRepository
from ...core.utils.datetime_utils import now_utc, normalize_to_utc

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
from ..decisioning.decision_strategies import LLMDecisionStrategy, DeterministicLeastCostStrategy

class RoutingService:
    def __init__(
        self, 
        fee_service: FeeService, 
        performance_repository: RoutingPerformanceRepository,
        strategy: Optional[RoutingDecisionStrategy] = None
    ):
        self.fee_service = fee_service
        self.performance_repository = performance_repository
        # Default to Least Cost strategy if none provided (more robust than LLM for base setup)
        self.strategy = strategy or DeterministicLeastCostStrategy()

    def find_best_route(self, payment_create: PaymentCreate) -> PaymentProvider:
        """
        Uses the injected strategy to determine the best payment provider.
        """
        if payment_create.provider:
            return payment_create.provider

        # 1. Gather raw data
        all_fees = self.fee_service.get_all_fees()
        # In a real app, we'd filter by dimension here
        dimension = RoutingDimension(
            payment_method_type="credit_card",
            currency=payment_create.currency,
            region="domestic" # Default for now
        )
        performance_data = self.performance_repository.find_by_dimension(dimension)
        
        # 2. Reconcile into ResolvedProvider view (Deterministic Source of Truth)
        resolved_map = {}
        
        # Priority 1: Performance Data (Dynamic)
        for perf in performance_data:
            resolved_map[perf.provider] = ResolvedProvider(
                provider=perf.provider,
                fixed_fee=perf.metrics.cost_structure.fixed_fee,
                variable_fee_percent=perf.metrics.cost_structure.variable_fee_percent,
                auth_rate=perf.metrics.auth_rate,
                avg_latency_ms=perf.metrics.avg_latency_ms
            )
            
        # Priority 2: Static Fees (Fallback if not in Performance Data)
        for fee in all_fees:
            if fee.provider not in resolved_map:
                resolved_map[fee.provider] = ResolvedProvider(
                    provider=fee.provider,
                    fixed_fee=fee.fixed_fee,
                    variable_fee_percent=fee.variable_fee_percent,
                    auth_rate=0.95, # Default auth rate for static fees
                    avg_latency_ms=300 # Default latency for static fees
                )
        
        resolved_providers = list(resolved_map.values())

        # 3. Delegate to strategy
        provider = self.strategy.decide(
            payment_in=payment_create,
            providers=resolved_providers
        )
        
        print(f"Routing Decision: Strategy {self.strategy.__class__.__name__} chose '{provider.value}'")
        return provider

class PreprocessingService:
    """
    Service to handle pre-processing of payments, such as preparing routes for recurring payments.
    """
    def __init__(
        self, 
        performance_repository: RoutingPerformanceRepository,
        bin_repository: CardBINRepository,
        fee_repository: InterchangeFeeRepository,
        redis_client: Optional[redis.Redis] = None,
        subscription_repository: Optional[SubscriptionRepository] = None,
        precalculated_route_repository: Optional[PrecalculatedRouteRepository] = None,
        routing_service: Optional[RoutingService] = None
    ):
        self.performance_repository = performance_repository
        self.bin_repository = bin_repository
        self.fee_repository = fee_repository
        self.redis_client = redis_client
        self.subscription_repository = subscription_repository
        self.precalculated_route_repository = precalculated_route_repository
        self.routing_service = routing_service

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
        # 1. Lookup BIN Metadata
        bin_data = None
        if context.payment_method.bin:
            bin_data = self.bin_repository.find_by_bin(context.payment_method.bin)

        # 2. Build Dimension from Context and BIN data
        network = bin_data.brand.lower() if bin_data and bin_data.brand else "visa"
        card_type = bin_data.type.lower() if bin_data and bin_data.type else "credit"
        region = "domestic" if bin_data and bin_data.country == "United States" else "international" # Logic shortcut

        dimension = RoutingDimension(
            payment_method_type=context.payment_method.type,
            payment_form="card_on_file",
            network=network,
            card_type=card_type,
            region=region,
            currency="USD"
        )

        # 3. Check Provider Health (Redis)
        healthy_providers = []
        all_providers = [PaymentProvider.STRIPE, PaymentProvider.ADYEN, PaymentProvider.BRAINTREE]
        
        if self.redis_client:
            for provider in all_providers:
                health = self.redis_client.get(f"provider_health:{provider.value.lower()}")
                if health != b"down":
                    healthy_providers.append(provider)
        else:
            healthy_providers = all_providers

        # 4. Get Candidates via Performance Repository
        candidates = self.performance_repository.find_by_dimension(dimension)
        
        # Filter by health
        candidates = [c for c in candidates if c.provider in healthy_providers]
        
        if not candidates:
            fallback = healthy_providers[0] if healthy_providers else PaymentProvider.STRIPE
            return PaymentRoute(
                processor=fallback,
                routing_reason="Default Fallback (No performance data or all preferred down)"
            )

        # 5. Select Best based on Estimated Cost (Interchange + Markup)
        # Simplified: interchange fees usually favor debit/domestic.
        # For this prototype, we'll use a scoring function.
        
        def score(candidate):
            # Base cost from performance records (markup)
            markup = candidate.metrics.cost_structure.fixed_fee
            # Potential auth rate penalty
            reliability_bonus = (1.0 - candidate.metrics.auth_rate) * 10
            return markup + reliability_bonus

        best_candidate = min(candidates, key=score)

        return PaymentRoute(
            processor=best_candidate.provider,
            routing_reason=f"Optimal route for {network} {card_type} ({region}). Scoring: {score(best_candidate):.4f}"
        )

    def precalculate_upcoming_renewals(self, lookahead_days: int = 7):
        """
        Scans for subscriptions renewing within the lookahead window and 
        pre-calculates the best routing decision.
        """
        if not self.subscription_repository or not self.precalculated_route_repository or not self.routing_service:
            print("Warning: Repositories or RoutingService not injected. Skipping pre-calculation.")
            return

        from datetime import timedelta
        now = now_utc()
        target_date = now + timedelta(days=lookahead_days)
        
        upcoming_subscriptions = self.subscription_repository.find_upcoming_renewals(now, target_date)
        print(f"Found {len(upcoming_subscriptions)} upcoming renewals.")

        for sub in upcoming_subscriptions:
            # Create a PaymentCreate object for the routing service
            payment_in = PaymentCreate(
                merchant_id=sub.merchant_id,
                customer_id=sub.customer_id,
                amount=sub.amount,
                currency=sub.currency,
                description=f"Pre-calculation for renewal of sub {sub.id}"
            )
            
            # Determine the best provider
            best_provider = self.routing_service.find_best_route(payment_in)
            
            # Persist the decision
            route_in = PrecalculatedRouteCreate(
                subscription_id=sub.id,
                provider=best_provider,
                routing_decision=f"Pre-calculated via {self.routing_service.strategy.__class__.__name__} at {now.isoformat()}",
                expires_at=sub.next_renewal_at + timedelta(hours=24) # Valid until slightly after renewal
            )
            self.precalculated_route_repository.save(route_in)
            print(f"Pre-calculated route for subscription {sub.id}: {best_provider.value}")
