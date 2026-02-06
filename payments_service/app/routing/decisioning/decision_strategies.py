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
from .planner import RoutingPlanner

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

class PlannerRoutingStrategy(RoutingDecisionStrategy):
    """
    A sophisticated strategy that uses a Planner to generate and execute 
    a multi-agent routing plan.
    """
    def __init__(self, objective: str = "balanced", model: str = "openai:gpt-4o"):
        self.objective = objective
        self.model = model
        self.planner = RoutingPlanner(model=model)
        self.client = aisuite.Client()

    def decide(self, payment_in: PaymentCreate, performance_data: List[ProviderPerformance], fees: List[Any]) -> PaymentProvider:
        # 1. Prepare context
        context = {
            "payment": payment_in.model_dump(),
            "performance": [p.model_dump() for p in performance_data],
            "fees": [f.model_dump() for f in fees]
        }

        # 2. Generate Plan
        plan = self.planner.generate_plan(self.objective, context)
        print(f"Generated Plan: {json.dumps(plan, indent=2)}")

        # 3. Execute Plan
        results = self.planner.execute_plan(plan, context)

        # 4. Final Synthesis
        prompt = """
        You are the Final Decision Agent. 
        Objective: {objective}
        Transaction: {payment_json}
        
        --- AGENT EVIDENCE ---
        {results_json}
        
        --- INSTRUCTION ---
        Based on the evidence from our specialists, select the best provider.
        Return ONLY a JSON object: {{"best_provider": "...", "reasoning": "..."}}
        """.format(
            objective=self.objective,
            payment_json=json.dumps(context['payment'], default=str),
            results_json=json.dumps(results, default=str)
        )

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        response_data = json.loads(completion.choices[0].message.content or "{}")
        provider_name = response_data.get("best_provider", PaymentProvider.INTERNAL.value)
        
        print(f"Final Decision via Planner: {provider_name}")
        print(f"Reasoning: {response_data.get('reasoning')}")
        
        return PaymentProvider(provider_name)
