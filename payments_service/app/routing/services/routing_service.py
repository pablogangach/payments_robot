import json
from typing import List
import aisuite
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.models.fees import FeeStructure
from payments_service.app.routing.services.fee_service import FeeService


class RoutingService:
    def __init__(self, fee_service: FeeService, performance_repository: 'RoutingPerformanceRepository'):
        self.fee_service = fee_service
        self.performance_repository = performance_repository
        self.client = aisuite.Client()

    def find_best_route(self, payment_create: PaymentCreate) -> PaymentProvider:
        """
        Uses an LLM to determine the best payment provider based on cost and performance.
        """
        if payment_create.provider:
            print(f"Forcing provider '{payment_create.provider.value}' as per request.")
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
        
        STATIC FEE STRUCTURES:
        {fees_json}

        REAL-TIME PERFORMANCE METRICS (by Dimension):
        {perf_json}

        INCOMING PAYMENT REQUEST:
        {payment_json}

        --- YOUR OBJECTIVE ---
        
        Analyze the fee structures AND the real-time performance data (auth_rate, latency).
        
        1. Identify the providers that match the transaction's dimension (currency, region, etc.).
        2. Calculate the total fee for each candidate.
        3. Weight the cost against the performance. If a provider is slightly more expensive but has a significantly higher auth_rate, it might be the better choice.
        
        Return ONLY the provider's name in a JSON object, like this:
        {{"best_provider": "stripe", "reasoning": "Higher auth rate for domestic Visa cards vs competitors."}}
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
        print(f"AI Routing Decision: Chose '{provider_name}' for payment of {payment_create.amount} {payment_create.currency}")
        return PaymentProvider(provider_name)