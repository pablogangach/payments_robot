import json
from typing import List, Any, Optional
try:
    import aisuite
    AISUITE_AVAILABLE = True
except ImportError:
    AISUITE_AVAILABLE = False
from payments_service.app.core.models.payment import PaymentProvider, PaymentCreate
from .interfaces import RoutingDecisionStrategy
from .models import ProviderPerformance

class FixedProviderStrategy(RoutingDecisionStrategy):
    """
    A simple strategy that always returns a fixed provider.
    Useful for testing and explicit overrides.
    """
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def decide(self, payment_in: PaymentCreate, performance_data: List[ProviderPerformance], fees: List[Any]) -> PaymentProvider:
        return self.provider

class DeterministicLeastCostStrategy(RoutingDecisionStrategy):
    """
    A rule-based strategy that calculates the cost for each provider
    based on the fee structure and selects the absolute cheapest.
    """
    def decide(self, payment_in: PaymentCreate, performance_data: List[ProviderPerformance], fees: List[Any]) -> PaymentProvider:
        if not fees:
            return PaymentProvider.STRIPE # Fallback
            
        amount = payment_in.amount
        
        # Simple cost calculation logic
        def calculate_cost(fee):
            return fee.fixed_fee + (amount * (fee.variable_fee_percent / 100))

        # Filter fees that match the context (simplified for now)
        # In a real app, fee would be chosen based on region/network
        ranked_providers = sorted(fees, key=lambda f: calculate_cost(f))
        
        if ranked_providers:
            return ranked_providers[0].provider
            
        return PaymentProvider.STRIPE

class LLMDecisionStrategy(RoutingDecisionStrategy):
    """
    Uses an LLM via aisuite to make a decision based on cost, 
    performance, and a specific objective.
    """
    def __init__(self, objective: str = "balanced", model: str = "openai:gpt-4o"):
        if not AISUITE_AVAILABLE:
            raise ImportError("aisuite is not installed. Please install it to use LLMDecisionStrategy.")
        self.objective = objective
        self.model = model
        self.client = aisuite.Client()

    def decide(self, payment_in: PaymentCreate, performance_data: List[ProviderPerformance], fees: List[Any]) -> PaymentProvider:
        fees_json = json.dumps([f.model_dump() for f in fees], default=str)
        perf_json = json.dumps([p.model_dump() for p in performance_data], default=str)
        payment_json = payment_in.model_dump_json()

        prompt = f"""
        You are an intelligent payment routing engine.
        Objective: {self.objective}

        --- AVAILABLE DATA ---
        FEES: {fees_json}
        PERFORMANCE: {perf_json}
        TRANSACTION: {payment_json}

        --- INSTRUCTION ---
        Select the best provider according to the objective. 
        Least Cost: Minimize total fees.
        Highest Auth: Maximize auth_rate.
        Balanced: Optimize for both.

        Return ONLY a JSON object: {{"best_provider": "...", "reasoning": "..."}}
        """

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise routing engine."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        response_data = json.loads(completion.choices[0].message.content or "{}")
        provider_name = response_data.get("best_provider", PaymentProvider.INTERNAL.value)
        return PaymentProvider(provider_name)
