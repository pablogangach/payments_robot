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
        fees = context.get("fees", [])
        performance = context.get("performance", [])
        payment = context.get("payment", {})
        
        prompt = """
        You are a Cost Analyst Agent for a payment system.
        Analyze the following fees, provider performance (which contains specific cost structures), and payment details to recommend the cheapest provider.
        
        FEES (Static): {fees_json}
        PERFORMANCE (Dynamic Metrics with Costs): {perf_json}
        PAYMENT: {payment_json}
        
        Return a JSON object: {{"analysis": "...", "recommended_provider": "...", "confidence": 0.0-1.0}}
        """.format(
            fees_json=json.dumps(fees, default=str),
            perf_json=json.dumps(performance, default=str),
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
        performance = context.get("performance", [])
        
        prompt = """
        You are a Performance Analyst Agent for a payment system.
        Analyze the following provider performance data and recommend the most reliable provider.
        
        PERFORMANCE: {perf_json}
        
        Return a JSON object: {{"analysis": "...", "recommended_provider": "...", "confidence": 0.0-1.0}}
        """.format(
            perf_json=json.dumps(performance, default=str)
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content or "{}")
