import sys
import os
import random
import time
import json
import redis
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append("/Users/pabloganga/src/projects/payments_robot")

from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.decisioning.models import (
    RoutingDimension, 
    ProviderPerformance, 
    PerformanceMetrics, 
    CostStructure, 
    ResolvedProvider
)
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.decisioning.strategies import StaticAggregationStrategy
from payments_service.app.routing.decisioning.decision_strategies import (
    PlannerRoutingStrategy, 
    DeterministicLeastCostStrategy,
    LLMDecisionStrategy
)
from payments_service.app.routing.preprocessing.service import RoutingService, FeeService
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore
from payments_service.app.routing.ingestion.data_generator import DataGenerator
from payments_service.app.routing.ingestion.service import DataIngestor

class StressSimulator:
    def __init__(self, use_llm: bool = False, concurrency: int = 5):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.store = InMemoryKeyValueStore()
        self.repo = RoutingPerformanceRepository(self.store)
        self.fee_service = FeeService()
        
        # Select strategy
        if use_llm:
            print("Using PlannerRoutingStrategy (LLM-based)")
            self.strategy = PlannerRoutingStrategy(objective="balanced")
        else:
            print("Using DeterministicLeastCostStrategy")
            self.strategy = DeterministicLeastCostStrategy()
            
        self.routing_service = RoutingService(
            fee_service=self.fee_service,
            performance_repository=self.repo,
            redis_client=self.redis_client,
            strategy=self.strategy
        )
        
        self.generator = DataGenerator()
        self.concurrency = concurrency
        self.results = []

    def seed_initial_data(self):
        """Pre-populate the repository with some 'historical' performance data."""
        print("Seeding initial performance data...")
        ingestor = DataIngestor(self.repo, StaticAggregationStrategy())
        records = self.generator.generate_batch(500)
        
        class MockDataProvider:
            def fetch_data(self): return records
            
        ingestor.ingest_from_provider(MockDataProvider())
        print(f"Seeded {len(self.repo.get_all())} performance records.")

    def simulate_outage(self, provider: PaymentProvider, duration_sec: int):
        """Sets a provider to 'down' in Redis for a specific duration."""
        print(f"!!! DISRUPTOR: Simulating outage for {provider.value} for {duration_sec}s")
        self.redis_client.set(f"provider_health:{provider.value.lower()}", "down")
        time.sleep(duration_sec)
        self.redis_client.set(f"provider_health:{provider.value.lower()}", "up")
        print(f"!!! DISRUPTOR: {provider.value} is back UP")

    def run_transaction(self, tx_id: int):
        """Simulates a single payment routing request."""
        # Randomly vary the payment details
        payment = PaymentCreate(
            amount=round(random.uniform(10.0, 500.0), 2),
            currency=random.choice(["USD", "EUR", "GBP"]),
            merchant_id=f"m_{random.randint(1, 10)}",
            customer_id=f"c_{random.randint(1, 100)}",
            description=f"Stress Test Transaction {tx_id}"
        )
        
        # Attach a dummy bin for network metadata
        payment.payment_method = type('obj', (object,), {
            'bin': random.choice(["411111", "511111", "341111"])
        })

        start_time = time.time()
        try:
            decision = self.routing_service.find_best_route(payment)
            latency = (time.time() - start_time) * 1000
            
            result = {
                "tx_id": tx_id,
                "provider": decision.value,
                "latency_ms": latency,
                "status": "success"
            }
        except Exception as e:
            result = {
                "tx_id": tx_id,
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000,
                "status": "failed"
            }
        
        self.results.append(result)
        return result

    def execute_burst(self, count: int):
        """Runs a burst of transactions in parallel."""
        print(f"Executing burst of {count} transactions with concurrency {self.concurrency}...")
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            executor.map(self.run_transaction, range(count))

    def print_report(self):
        """Prints a summary of the stress test results."""
        successes = [r for r in self.results if r["status"] == "success"]
        failures = [r for r in self.results if r["status"] == "failed"]
        
        if not successes:
            print("No successful transactions to report.")
            return

        avg_latency = sum(r["latency_ms"] for r in successes) / len(successes)
        max_latency = max(r["latency_ms"] for r in successes)
        
        provider_counts = {}
        for r in successes:
            p = r["provider"]
            provider_counts[p] = provider_counts.get(p, 0) + 1

        print("\n" + "="*40)
        print("STRESS TEST REPORT")
        print("="*40)
        print(f"Total Transactions: {len(self.results)}")
        print(f"Success Rate: {len(successes)/len(self.results):.2%}")
        print(f"Avg Latency: {avg_latency:.2f}ms")
        print(f"Max Latency: {max_latency:.2f}ms")
        print("\nProvider Distribution:")
        for p, count in provider_counts.items():
            print(f"  - {p}: {count} ({count/len(successes):.2%})")
        print("="*40)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simulate production traffic and outages.")
    parser.add_argument("--llm", action="store_true", help="Use LLM-based routing strategy.")
    parser.add_argument("--fail-llm", action="store_true", help="Simulate a failure in the LLM service.")
    parser.add_argument("--burst", type=int, default=10, help="Number of transactions in the burst.")
    parser.add_argument("--outage", action="store_true", help="Simulate a provider outage during the test.")
    
    args = parser.parse_args()

    if args.fail_llm:
        print("!!! TEST MODE: Simulating LLM failures via monkey-patching")
        import aisuite
        class MockCompletions:
            def create(self, *args, **kwargs):
                raise Exception("LLM Service Unavailable (Simulated)")
        class MockChat:
            def __init__(self): self.completions = MockCompletions()
        class MockClient:
            def __init__(self): self.chat = MockChat()
        aisuite.Client = MockClient
    
    sim = StressSimulator(use_llm=args.llm, concurrency=5)
    sim.seed_initial_data()
    
    if args.outage:
        # Run a small burst, kill a provider, run another burst
        sim.execute_burst(5)
        # Start outage in background or just wait? Let's just do it sequentially for clarity in this script
        sim.simulate_outage(PaymentProvider.ADYEN, 2)
        sim.execute_burst(args.burst)
    else:
        sim.execute_burst(args.burst)
        
    sim.print_report()
