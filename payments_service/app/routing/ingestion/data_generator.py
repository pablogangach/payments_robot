import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from payments_service.app.core.models.payment import PaymentProvider
from .models import RawTransactionRecord

class DataGenerator:
    """
    Utility to generate realistic dummy transaction data for testing and analysis.
    """

    DEFAULT_CONFIGS = {
        PaymentProvider.STRIPE: {
            "success_rate": 0.95,
            "avg_latency": 250,
            "latency_stddev": 50,
        },
        PaymentProvider.ADYEN: {
            "success_rate": 0.93,
            "avg_latency": 300,
            "latency_stddev": 70,
        },
        PaymentProvider.BRAINTREE: {
            "success_rate": 0.90,
            "avg_latency": 400,
            "latency_stddev": 100,
        },
        PaymentProvider.INTERNAL: {
            "success_rate": 0.85,
            "avg_latency": 150,
            "latency_stddev": 30,
        }
    }

    NETWORKS = ["visa", "mastercard", "amex", "discover"]
    REGIONS = ["domestic", "international"]
    CURRENCIES = ["USD", "EUR", "GBP"]
    PAYMENT_FORMS = ["card_on_file", "apple_pay", "google_pay"]

    def __init__(self, configs: Optional[Dict[PaymentProvider, Dict[str, float]]] = None):
        self.configs = configs or self.DEFAULT_CONFIGS

    def generate_record(
        self, 
        provider: Optional[PaymentProvider] = None,
        timestamp: Optional[datetime] = None
    ) -> RawTransactionRecord:
        if not provider:
            provider = random.choice(list(PaymentProvider))
        
        config = self.configs.get(provider, self.DEFAULT_CONFIGS[PaymentProvider.STRIPE])
        
        # Decide status based on success rate
        status = "succeeded" if random.random() < config["success_rate"] else "failed"
        
        # Generate latency with some randomness
        latency = int(random.gauss(config["avg_latency"], config["latency_stddev"]))
        latency = max(50, latency) # Ensure it's positive
        
        # Randomize other fields
        network = random.choice(self.NETWORKS)
        region = random.choice(self.REGIONS)
        currency = random.choice(self.CURRENCIES)
        payment_form = random.choice(self.PAYMENT_FORMS)
        
        # Dummy BIN
        bin_val = "".join([str(random.randint(0, 9)) for _ in range(6)])
        
        amount = round(random.uniform(5.0, 500.0), 2)
        
        if not timestamp:
            # Within last 30 days
            days_ago = random.randint(0, 30)
            seconds_ago = random.randint(0, 86400)
            timestamp = datetime.now() - timedelta(days=days_ago, seconds=seconds_ago)

        return RawTransactionRecord(
            provider=provider,
            payment_form=payment_form,
            processing_type="network_token" if random.random() > 0.5 else "signature",
            amount=amount,
            currency=currency,
            status=status,
            error_code=None if status == "succeeded" else "card_declined",
            latency_ms=latency,
            bin=bin_val,
            card_type="credit" if random.random() > 0.2 else "debit",
            network=network,
            region=region,
            timestamp=timestamp
        )

    def generate_batch(self, count: int, days_window: int = 30) -> List[RawTransactionRecord]:
        records = []
        now = datetime.now()
        for _ in range(count):
            # Distribute across window
            delta = timedelta(
                days=random.randint(0, days_window - 1),
                seconds=random.randint(0, 86400)
            )
            ts = now - delta
            records.append(self.generate_record(timestamp=ts))
        
        # Sort by timestamp
        records.sort(key=lambda x: x.timestamp)
        return records

if __name__ == "__main__":
    # Quick test
    gen = DataGenerator()
    batch = gen.generate_batch(5)
    for r in batch:
        print(f"[{r.timestamp}] {r.provider.value}: {r.status} in {r.latency_ms}ms ({r.network} - {r.region})")
