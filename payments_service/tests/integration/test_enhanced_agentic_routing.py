import pytest
import json
from unittest.mock import MagicMock, patch
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.decisioning.models import ResolvedProvider
from payments_service.app.routing.decisioning.decision_strategies import PlannerRoutingStrategy
from payments_service.app.core.models.metadata import CardBIN, InterchangeFee
from payments_service.tests.factories import create_mock

@patch("aisuite.Client")
def test_enhanced_agentic_routing_flow(mock_aisuite_client):
    """
    Scenario: 
    - Transaction: Debit card (Visa).
    - Providers: Stripe ($0.10), Adyen ($0.05).
    - Health: Adyen is DOWN.
    - Expectation: Planner might propose Adyen (cheapest), but Critic should override to Stripe (healthy).
    """
    
    # 1. Setup Mock AI Responses
    mock_client_instance = mock_aisuite_client.return_value
    
    # Mock Planner (Generate Plan)
    mock_plan_resp = MagicMock()
    mock_plan_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "plan": [
            {"agent": "NetworkIntelligence", "reason": "Analyze card type for cost"},
            {"agent": "HealthSentinel", "reason": "Check if providers are up"},
            {"agent": "CostAnalyst", "reason": "Final cost comparison"}
        ]
    })))]
    
    # Mock Network Agent
    mock_network_resp = MagicMock()
    mock_network_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "analysis": "This is a US Debit card, Adyen usually has better regional rates.",
        "preferred_networks": ["visa"],
        "routing_advice": "Prioritize Adyen for domestic debit."
    })))]
    
    # Mock Health Sentinel
    mock_health_resp = MagicMock()
    mock_health_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "analysis": "Adyen is reported as DOWN in Redis.",
        "unhealthy_providers": ["adyen"],
        "critical_alerts": ["ADYEN_DOWN"]
    })))]
    
    # Mock Cost Analyst
    mock_cost_resp = MagicMock()
    mock_cost_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "analysis": "Adyen is $0.05, Stripe is $0.10. Adyen is cheaper.",
        "recommended_provider": "adyen",
        "confidence": 0.9
    })))]
    
    # Mock Supervisor (Synthesis)
    mock_supervisor_resp = MagicMock()
    mock_supervisor_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "best_provider": "adyen",
        "reasoning": "Adyen is significantly cheaper for this debit transaction."
    })))]
    
    # Mock Critic Agent (Override!)
    mock_critic_resp = MagicMock()
    mock_critic_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "is_valid": False,
        "feedback": "Cannot route to Adyen because it is DOWN.",
        "recommended_override": "stripe"
    })))]
    
    # Sequence of returns for create()
    mock_client_instance.chat.completions.create.side_effect = [
        mock_plan_resp,       # 1. Planner
        mock_network_resp,    # 2. Network Intelligence
        mock_health_resp,     # 3. Health Sentinel
        mock_cost_resp,       # 4. Cost Analyst
        mock_supervisor_resp,  # 5. Supervisor Proposal
        mock_critic_resp      # 6. Critic Review
    ]
    
    # 2. Setup Test Data
    strategy = PlannerRoutingStrategy(objective="lowest_cost")
    
    payment_in = create_mock(PaymentCreate, amount=100.0)
    payment_in.bin_metadata = create_mock(CardBIN, type="debit", brand="Visa", country="United States")
    payment_in.provider_health = {"stripe": "up", "adyen": "down"}
    
    providers = [
        create_mock(ResolvedProvider, provider=PaymentProvider.STRIPE, fixed_fee=0.1),
        create_mock(ResolvedProvider, provider=PaymentProvider.ADYEN, fixed_fee=0.05)
    ]
    
    # 3. Execute
    best_provider = strategy.decide(payment_in, providers)
    
    # 4. Assertions
    assert best_provider == PaymentProvider.STRIPE # Critic override worked
    assert mock_client_instance.chat.completions.create.call_count == 6
    print("Enhanced Agentic Routing flow verified!")

if __name__ == "__main__":
    test_enhanced_agentic_routing_flow()
