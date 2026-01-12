import json
from typing import List
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

class RoutingService:
    def __init__(self, fee_service: FeeService, performance_repository: RoutingPerformanceRepository):
        self.fee_service = fee_service
        self.performance_repository = performance_repository
        self.client = aisuite.Client()

    def find_best_route(self, payment_create: PaymentCreate) -> PaymentProvider:
        """
        Uses an LLM to determine the best payment provider based on cost and performance.
        """
        if payment_create.provider:
            return payment_create.provider

        # 1. Gather context
        all_fees = self.fee_service.get_all_fees()
        all_performance = self.performance_repository.get_all()
        
        fees_json = json.dumps([fee.model_dump() for fee in all_fees])
        perf_json = json.dumps([p.model_dump() for p in all_performance], default=str)
        payment_json = payment_create.model_dump_json()

        prompt = f"""
        You are an expert in payment processing, specializing in Intelligent Routing.
        Your task is to find the best payment provider for a given transaction by balancing cost and performance.

        --- AVAILABLE DATA ---
        STATIC FEE STRUCTURES: {fees_json}
        REAL-TIME PERFORMANCE METRICS: {perf_json}
        INCOMING PAYMENT REQUEST: {payment_json}

        --- YOUR OBJECTIVE ---
        Analyze the data. Weight the cost against the performance (auth_rate, latency).
        Return ONLY the provider's name in a JSON object: {{"best_provider": "stripe", "reasoning": "..."}}
        """

        completion = self.client.chat.completions.create(
            model="openai:gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise routing engine."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        response_data = json.loads(completion.choices[0].message.content or "{}")
        provider_name = response_data.get("best_provider", PaymentProvider.INTERNAL.value)
        print(f"AI Routing Decision: Chose '{provider_name}'")
        return PaymentProvider(provider_name)

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
