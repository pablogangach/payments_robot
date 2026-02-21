import json
from typing import List, Dict, Any, Type
import aisuite
from .specialists import (
    BaseAgent, 
    CostAnalystAgent, 
    PerformanceAnalystAgent,
    NetworkIntelligenceAgent,
    HealthSentinelAgent,
    CriticAgent
)

class Capability:
    def __init__(self, name: str, description: str, agent_class: Type[BaseAgent]):
        self.name = name
        self.description = description
        self.agent_class = agent_class

class RoutingPlanner:
    def __init__(self, model: str = "openai:gpt-4o"):
        self.client = aisuite.Client()
        self.model = model
        self.capabilities: Dict[str, Capability] = {}
        self._register_default_capabilities()

    def _register_default_capabilities(self):
        self.register_capability(Capability(
            name="CostAnalyst",
            description="Analyzes fee structures to find the cheapest provider.",
            agent_class=CostAnalystAgent
        ))
        self.register_capability(Capability(
            name="PerformanceAnalyst",
            description="Analyzes auth rates and latency to find the most reliable provider.",
            agent_class=PerformanceAnalystAgent
        ))
        self.register_capability(Capability(
            name="NetworkIntelligence",
            description="Analyzes BIN metadata and interchange fees for network-specific optimizations.",
            agent_class=NetworkIntelligenceAgent
        ))
        self.register_capability(Capability(
            name="HealthSentinel",
            description="Assesses real-time provider health status from Redis.",
            agent_class=HealthSentinelAgent
        ))
        self.register_capability(Capability(
            name="Critic",
            description="Reviews proposed decisions against hard safety rules and health status.",
            agent_class=CriticAgent
        ))

    def register_capability(self, capability: Capability):
        self.capabilities[capability.name] = capability

    def generate_plan(self, objective: str, transaction_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        capabilities_desc = "\n".join([f"- {c.name}: {c.description}" for c in self.capabilities.values()])
        
        prompt = """
        You are a Routing Planner for a payment engine.
        Objective: {objective}
        Transaction: {transaction_json}
        
        Available Capabilities:
        {capabilities_desc}
        
        Generate a step-by-step execution plan to reach the routing decision.
        Return a JSON object with a 'plan' key containing a list of steps.
        Each step must have: 'agent' (name of the capability) and 'reason'.
        
        Example:
        {{
            "plan": [
                {{"agent": "CostAnalyst", "reason": "Determine cheapest options first"}},
                {{"agent": "PerformanceAnalyst", "reason": "Check reliability of the cheapest options"}}
            ]
        }}
        """.format(
            objective=objective,
            transaction_json=json.dumps(transaction_context, default=str),
            capabilities_desc=capabilities_desc
        )
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content or '{"plan": []}')
        return data.get("plan", [])

    def execute_plan(self, plan: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for step in plan:
            agent_name = step.get("agent")
            if agent_name in self.capabilities:
                agent = self.capabilities[agent_name].agent_class(model=self.model)
                print(f"Executing Agent: {agent_name} for {step.get('reason')}")
                results[agent_name] = agent.run(context)
        return results
