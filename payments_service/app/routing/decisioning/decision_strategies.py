import json
from typing import List, Any, Optional, Dict
from collections import defaultdict
try:
    import aisuite
    AISUITE_AVAILABLE = True
except ImportError:
    AISUITE_AVAILABLE = False
from payments_service.app.core.models.payment import PaymentProvider, PaymentCreate
from .interfaces import RoutingDecisionStrategy
from .models import ProviderPerformance, ResolvedProvider
from .planner import RoutingPlanner

class FixedProviderStrategy(RoutingDecisionStrategy):
    """
    A simple strategy that always returns a fixed provider.
    Useful for testing and explicit overrides.
    """
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def decide(self, payment_in: PaymentCreate, providers: List[ResolvedProvider]) -> PaymentProvider:
        return self.provider

class DeterministicLeastCostStrategy(RoutingDecisionStrategy):
    """
    A rule-based strategy that calculates the cost for each provider
    based on the fee structure and selects the absolute cheapest.
    """
    def decide(self, payment_in: PaymentCreate, providers: List[ResolvedProvider]) -> PaymentProvider:
        if not providers:
            return PaymentProvider.STRIPE
            
        amount = payment_in.amount
        costs = {}
        for p in providers:
            cost = p.fixed_fee + (amount * (p.variable_fee_percent / 100))
            costs[p.provider] = cost
            
        best_provider = min(costs, key=costs.get)
        return PaymentProvider(best_provider)

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

    def decide(self, payment_in: PaymentCreate, providers: List[ResolvedProvider]) -> PaymentProvider:
        try:
            provider_json = json.dumps([p.model_dump() for p in providers], default=str)
            payment_json = payment_in.model_dump_json()

            prompt = f"""
            You are an intelligent payment routing engine.
            Objective: {self.objective}

            --- RESOLVED PROVIDER DATA ---
            PROVIDERS: {provider_json}
            TRANSACTION: {payment_json}

            --- INSTRUCTION ---
            Select the best provider according to the objective. 
            Each provider record contains the final reconciled cost and performance metrics.
            
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
            provider_name = response_data.get("best_provider", PaymentProvider.STRIPE.value)
            return PaymentProvider(provider_name)
        except Exception as e:
            print(f"!!! CIRCUIT BREAKER: LLMDecisionStrategy failed: {e}. Falling back to DeterministicLeastCostStrategy.")
            fallback = DeterministicLeastCostStrategy()
            return fallback.decide(payment_in, providers)

class PlannerRoutingStrategy(RoutingDecisionStrategy):
    """
    A sophisticated strategy that uses a Planner to generate and execute 
    a multi-agent routing plan.
    """
    def __init__(self, objective: str = "balanced", model: str = "openai:gpt-4o"):
        if not AISUITE_AVAILABLE:
            raise ImportError("aisuite is not installed. Please install it to use PlannerRoutingStrategy.")
        self.objective = objective
        self.model = model
        self.planner = RoutingPlanner(model=model)
        self.client = aisuite.Client()

    def decide(self, payment_in: PaymentCreate, providers: List[ResolvedProvider]) -> PaymentProvider:
        try:
            # 1. Prepare enriched context
            bin_metadata = getattr(payment_in, "bin_metadata", None)
            interchange_fees = getattr(payment_in, "interchange_fees", []) or []
            provider_health = getattr(payment_in, "provider_health", {}) or {}

            context = {
                "payment": payment_in.model_dump(),
                "providers": [p.model_dump() for p in providers],
                "bin_metadata": bin_metadata.model_dump() if hasattr(bin_metadata, "model_dump") else bin_metadata,
                "interchange_fees": [f.model_dump() if hasattr(f, "model_dump") else f for f in interchange_fees],
                "provider_health": provider_health
            }

            # 2. Generate Plan
            plan = self.planner.generate_plan(self.objective, context)
            print(f"Generated Plan: {json.dumps(plan, indent=2)}")

            # 3. Execute Core Plan (Specialists)
            results = self.planner.execute_plan(plan, context)

            # 4. Preliminary Decision Synthesis
            synthesis_prompt = """
            You are the Routing Supervisor. 
            Objective: {objective}
            Transaction: {payment_json}
            
            --- AGENT EVIDENCE ---
            {results_json}
            
            --- INSTRUCTION ---
            Based on the technical evidence, propose the best provider.
            Return ONLY a JSON object: {{"best_provider": "...", "reasoning": "..."}}
            """.format(
                objective=self.objective,
                payment_json=json.dumps(context['payment'], default=str),
                results_json=json.dumps(results, default=str)
            )

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": synthesis_prompt}],
                response_format={"type": "json_object"}
            )

            proposal = json.loads(completion.choices[0].message.content or "{}")
            
            # 5. SELF-CORRECTION: Critic Review
            context["proposed_decision"] = proposal
            context["agent_evidence"] = results
            
            critic_results = self.planner.execute_plan([{"agent": "Critic", "reason": "Self-Correction Safety Review"}], context)
            critic_feedback = critic_results.get("Critic", {})
            
            final_provider_name = proposal.get("best_provider")
            if not critic_feedback.get("is_valid", True) and critic_feedback.get("recommended_override"):
                print(f"CRITIC OVERRIDE: {final_provider_name} -> {critic_feedback.get('recommended_override')}")
                print(f"Reason: {critic_feedback.get('feedback')}")
                final_provider_name = critic_feedback.get("recommended_override")

            print(f"Final Decision via Planner: {final_provider_name}")
            return PaymentProvider(final_provider_name)
        except Exception as e:
            print(f"!!! CIRCUIT BREAKER: PlannerRoutingStrategy failed: {e}. Falling back to DeterministicLeastCostStrategy.")
            fallback = DeterministicLeastCostStrategy()
            return fallback.decide(payment_in, providers)
