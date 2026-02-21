import json
from abc import ABC, abstractmethod
from typing import List, Any, Dict
import aisuite
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from .models import ProviderPerformance

class BaseAgent(ABC):
    def __init__(self, model: str = "openai:gpt-4o"):
        self.client = aisuite.Client()
        self.model = model

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

class CostAnalystAgent(BaseAgent):
    """
    Agent specialized in analyzing fee structures and recommending the cheapest provider.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        providers = context.get("providers", [])
        payment = context.get("payment", {})
        
        prompt = """
        You are a Cost Analyst Agent for a payment system.
        Analyze the following resolved provider data and payment details to recommend the cheapest provider.
        Each provider record contains a reconciled cost structure (fixed_fee and variable_fee_percent).
        
        PROVIDERS (Resolved): {providers_json}
        PAYMENT: {payment_json}
        
        Return a JSON object: {{"analysis": "...", "recommended_provider": "...", "confidence": 0.0-1.0}}
        """.format(
            providers_json=json.dumps(providers, default=str),
            payment_json=json.dumps(payment, default=str)
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content or "{}")

class PerformanceAnalystAgent(BaseAgent):
    """
    Agent specialized in analyzing authorization rates and latency.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        providers = context.get("providers", [])
        
        prompt = """
        You are a Performance Analyst Agent for a payment system.
        Analyze the following resolved provider data and recommend the most reliable provider.
        
        PROVIDERS (Resolved): {providers_json}
        
        Return a JSON object: {{"analysis": "...", "recommended_provider": "...", "confidence": 0.0-1.0}}
        """.format(
            providers_json=json.dumps(providers, default=str)
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content or "{}")

class NetworkIntelligenceAgent(BaseAgent):
    """
    Agent specialized in analyzing card network metadata and interchange fee implications.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        bin_data = context.get("bin_metadata")
        interchange_fees = context.get("interchange_fees", [])
        payment = context.get("payment", {})
        
        prompt = """
        You are a Network Intelligence Agent. 
        Analyze the card metadata and interchange rules to identify cost optimization opportunities.
        
        BIN METADATA: {bin_json}
        INTERCHANGE RULES: {fees_json}
        PAYMENT: {payment_json}
        
        Consider:
        1. Is this a debit card? (Usually lower interchange).
        2. Is this domestic or international?
        3. Which network (Visa/MC/Amex) has the best rate for this category?
        
        Return a JSON object: {{"analysis": "...", "preferred_networks": [...], "routing_advice": "..."}}
        """.format(
            bin_json=json.dumps(bin_data, default=str),
            fees_json=json.dumps(interchange_fees, default=str),
            payment_json=json.dumps(payment, default=str)
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content or "{}")

class HealthSentinelAgent(BaseAgent):
    """
    Agent specialized in assessing provider health and blocking risky routes.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        health_data = context.get("provider_health", {})
        
        prompt = """
        You are a Health Sentinel Agent.
        Assess the operational status of payment providers.
        
        HEALTH STATUS: {health_json}
        
        Identify any providers that are DOWN or exhibiting degraded performance.
        
        Return a JSON object: {{"analysis": "...", "unhealthy_providers": [...], "critical_alerts": [...]}}
        """.format(
            health_json=json.dumps(health_data, default=str)
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content or "{}")

class CriticAgent(BaseAgent):
    """
    Agent specialized in reviewing a proposed routing decision against hard constraints.
    """
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        proposed_decision = context.get("proposed_decision")
        agent_evidence = context.get("agent_evidence", {})
        health_data = context.get("provider_health", {})
        
        prompt = """
        You are a Routing Critic Agent.
        Your job is to review the proposed routing decision and ensure it is safe and logical.
        
        PROPOSED DECISION: {decision_json}
        AGENT EVIDENCE: {evidence_json}
        PROVIDER HEALTH: {health_json}
        
        CRITICAL RULES:
        1. Never route to a provider that is marked as DOWN.
        2. If the proposed provider has significantly lower confidence in evidence, flag it.
        
        Return a JSON object: {{"is_valid": true/false, "feedback": "...", "recommended_override": "..."}}
        """.format(
            decision_json=json.dumps(proposed_decision, default=str),
            evidence_json=json.dumps(agent_evidence, default=str),
            health_json=json.dumps(health_data, default=str)
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content or "{}")
