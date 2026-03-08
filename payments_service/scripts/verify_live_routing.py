import sys
import os
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append("/Users/pabloganga/src/projects/payments_robot")

from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.preprocessing.models import PaymentMethodDetails
from payments_service.app.routing.preprocessing.service import RoutingService, FeeService
from payments_service.app.routing.decisioning.decision_strategies import PlannerRoutingStrategy
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.decisioning.models import ProviderPerformance, RoutingDimension, PerformanceMetrics, CostStructure
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore
from payments_service.app.core.repositories.metadata_repository import CardBINRepository, InterchangeFeeRepository

def verify_live_routing():
    load_dotenv()
    print("--- STARTING LIVE AGENTIC ROUTING VERIFICATION ---")
    
    # 1. Setup Repositories
    from payments_service.app.core.repositories.datastore import InMemoryRelationalStore
    from payments_service.app.core.models.metadata import CardBIN, InterchangeFee
    
    bin_store = InMemoryRelationalStore()
    bin_repo = CardBINRepository(bin_store)
    # Seed common Visa Debit BIN
    bin_repo.save(CardBIN(bin="400022", brand="Visa", type="debit", category="classic", country="United States"))
    
    fee_store = InMemoryRelationalStore()
    fee_repo = InterchangeFeeRepository(fee_store)
    # Seed interchange fees
    fee_repo.save(InterchangeFee(network="visa", card_type="debit", card_category="classic", region="domestic", fee_percent=0.05, fee_fixed=0.21))
    fee_repo.save(InterchangeFee(network="visa", card_type="credit", card_category="classic", region="domestic", fee_percent=1.51, fee_fixed=0.10))
    
    # Mock Performance Data (since we don't have a real DB populated yet)
    perf_store = InMemoryKeyValueStore()
    perf_repo = RoutingPerformanceRepository(perf_store)
    
    # Seed some performance data to make the decision interesting
    # We'll say Stripe is super reliable but slightly more expensive for regulated debit
    # and a hypothetical "Internal" provider is cheaper for debit.
    
    dimension = RoutingDimension(payment_method_type="credit_card", region="domestic")
    
    perf1 = ProviderPerformance(
        provider=PaymentProvider.STRIPE,
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.99,
            fraud_rate=0.001,
            avg_latency_ms=150,
            cost_structure=CostStructure(fixed_fee=0.3, variable_fee_percent=2.9)
        ),
        data_window="live"
    )
    
    perf2 = ProviderPerformance(
        provider=PaymentProvider.ADYEN, # Using Adyen as a candidate
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.92,
            fraud_rate=0.005,
            avg_latency_ms=300,
            cost_structure=CostStructure(fixed_fee=0.2, variable_fee_percent=2.5)
        ),
        data_window="live"
    )
    
    perf3 = ProviderPerformance(
        provider=PaymentProvider.BRAINTREE,
        dimension=dimension,
        metrics=PerformanceMetrics(
            auth_rate=0.96,
            fraud_rate=0.002,
            avg_latency_ms=400,
            cost_structure=CostStructure(fixed_fee=0.49, variable_fee_percent=2.59)
        ),
        data_window="live"
    )
    
    perf_repo.save(perf1)
    perf_repo.save(perf2)
    perf_repo.save(perf3)
    
    # 2. Setup Routing Service
    fee_service = FeeService()
    # Use the sophisticated Planner Strategy
    strategy = PlannerRoutingStrategy(objective="least_cost")
    
    routing_service = RoutingService(
        fee_service=fee_service,
        performance_repository=perf_repo,
        bin_repository=bin_repo,
        fee_repository=fee_repo,
        strategy=strategy
    )
    
    # 3. Define Payment (Visa Debit - Regulated)
    # BIN 400022 is a common Visa Debit BIN
    payment_in = PaymentCreate(
        amount=50.0,
        currency="USD",
        merchant_id="m123",
        customer_id="c456",
        description="Complex Routing Test",
        payment_method=PaymentMethodDetails(
            type="credit_card",
            bin="400022",
            brand="Visa",
            last4="1111",
            exp_month=12,
            exp_year=2025
        )
    )
    
    # 4. Find Best Route
    print("\n[REQUESTING ROUTING DECISION...]")
    decision = routing_service.find_best_route(payment_in)
    
    print(f"\n--- FINAL DECISION: {decision.value} ---")

if __name__ == "__main__":
    try:
        verify_live_routing()
    except Exception as e:
        print(f"Error during live routing verification: {e}")
        import traceback
        traceback.print_exc()
