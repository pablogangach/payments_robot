from payments_service.app.routing.ingestion.data_generator import DataGenerator
from payments_service.app.routing.ingestion.service import DataIngestor
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.decisioning.strategies import StaticAggregationStrategy
from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore

def main():
    # 1. Setup
    store = InMemoryKeyValueStore()
    repo = RoutingPerformanceRepository(store)
    strategy = StaticAggregationStrategy()
    ingestor = DataIngestor(repo, strategy)
    generator = DataGenerator()

    # 2. Generate
    print("Generating 1000 dummy transaction records...")
    records = generator.generate_batch(1000)
    
    # 3. Ingest and Analyze
    # Since ingest_from_provider expects a DataProvider, we'll wrap our records
    class MockDataProvider:
        def fetch_data(self):
            return records

    print("Ingesting and analyzing records...")
    ingestor.ingest_from_provider(MockDataProvider())

    # 4. Verify
    all_perf = repo.get_all()
    print(f"Generated performance metrics for {len(all_perf)} unique dimensions.")
    
    # Sample output
    if all_perf:
        sample = all_perf[0]
        print(f"\nSample Metric:")
        print(f"Provider: {sample.provider.value}")
        print(f"Dimension: {sample.dimension.model_dump_json()}")
        print(f"Auth Rate: {sample.metrics.auth_rate:.2%}")
        print(f"Avg Latency: {sample.metrics.avg_latency_ms}ms")

if __name__ == "__main__":
    main()
