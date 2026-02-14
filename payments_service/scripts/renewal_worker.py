import time
import os
import signal
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from payments_service.app.core.repositories.subscription_repository import SubscriptionRepository
from payments_service.app.core.repositories.precalculated_route_repository import PrecalculatedRouteRepository
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.preprocessing.service import PreprocessingService, FeeService
from payments_service.app.core.api.dependencies import _initialize_strategy, intelligence_store
from payments_service.app.routing.preprocessing import RoutingService

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
RENEWAL_CHECK_INTERVAL_SECONDS = int(os.getenv("RENEWAL_CHECK_INTERVAL_SECONDS", "60"))
RENEWAL_LOOKAHEAD_DAYS = int(os.getenv("RENEWAL_LOOKAHEAD_DAYS", "7"))

class RenewalWorker:
    def __init__(self):
        if not DATABASE_URL:
            print("Error: DATABASE_URL not set.")
            sys.exit(1)
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        
        # Initialize Repositories
        sub_repo = SubscriptionRepository(self.db)
        precalc_repo = PrecalculatedRouteRepository(self.db)
        perf_repo = RoutingPerformanceRepository(intelligence_store)
        
        # Initialize Services
        routing_strategy = _initialize_strategy()
        routing_svc = RoutingService(
            fee_service=FeeService(),
            performance_repository=perf_repo,
            strategy=routing_strategy
        )
        
        self.preprocessing_service = PreprocessingService(
            performance_repository=perf_repo,
            subscription_repository=sub_repo,
            precalculated_route_repository=precalc_repo,
            routing_service=routing_svc
        )
        
        self.running = True
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        print("Stopping worker...")
        self.running = False

    def run(self):
        print(f"Starting Renewal Preprocessing Worker (Every {RENEWAL_CHECK_INTERVAL_SECONDS}s, Lookahead: {RENEWAL_LOOKAHEAD_DAYS} days)")
        while self.running:
            try:
                print(f"[{datetime.now(timezone.utc).isoformat()}] Running pre-calculation cycle...")
                self.preprocessing_service.precalculate_upcoming_renewals(lookahead_days=RENEWAL_LOOKAHEAD_DAYS)
            except Exception as e:
                print(f"Error in pre-calculation cycle: {e}")
            
            # Simple sleep between cycles
            for _ in range(RENEWAL_CHECK_INTERVAL_SECONDS):
                if not self.running:
                    break
                time.sleep(1)
        
        self.db.close()
        print("Worker stopped.")

if __name__ == "__main__":
    worker = RenewalWorker()
    worker.run()
