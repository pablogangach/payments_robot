import sys
import os
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path="/Users/pabloganga/src/projects/payments_robot/payments_service/.env")

# Add project root to path
sys.path.append("/Users/pabloganga/src/projects/payments_robot")

from payments_service.app.routing.decisioning.decision_strategies import PlannerRoutingStrategy
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.decisioning.models import ProviderPerformance, RoutingDimension, PerformanceMetrics, CostStructure
from payments_service.app.routing.preprocessing.service import FeeStructure

def test_planner_routing():
    # 1. Setup Mock Data
    payment = PaymentCreate(
        amount=100.0,
        currency="USD",
        merchant_id="m1",
        customer_id="c1"
    )
    
    performance = [
        ProviderPerformance(
            provider=PaymentProvider.STRIPE,
            dimension=RoutingDimension(payment_method_type="credit_card", region="domestic"),
            metrics=PerformanceMetrics(auth_rate=0.98, fraud_rate=0.01, avg_latency_ms=200, cost_structure=CostStructure(fixed_fee=0.3, variable_fee_percent=2.9)),
            data_window="batch"
        ),
        ProviderPerformance(
            provider=PaymentProvider.INTERNAL,
            dimension=RoutingDimension(payment_method_type="credit_card", region="domestic"),
            metrics=PerformanceMetrics(auth_rate=0.95, fraud_rate=0.01, avg_latency_ms=150, cost_structure=CostStructure(fixed_fee=0.2, variable_fee_percent=1.0)),
            data_window="batch"
        )
    ]
    
    fees = [
        FeeStructure(provider=PaymentProvider.STRIPE, region="domestic", fixed_fee=0.3, variable_fee_percent=2.9),
        FeeStructure(provider=PaymentProvider.INTERNAL, region="domestic", fixed_fee=0.2, variable_fee_percent=1.0)
    ]

    # 2. Initialize Strategy (will use aisuite under the hood)
    # Note: Requires OPENAI_API_KEY or equivalent in environment
    strategy = PlannerRoutingStrategy(objective="least_cost")
    
    print("--- STARTING PLANNER ROUTING DECISION ---")
    decision = strategy.decide(payment, performance, fees)
    print(f"--- FINAL DECISION: {decision} ---")

if __name__ == "__main__":
    try:
        test_planner_routing()
    except Exception as e:
        print(f"Error during verification: {e}")
