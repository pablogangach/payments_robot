from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timezone
from payments_service.app.core.models.payment import Payment, PaymentStatus
from payments_service.app.routing.ingestion.models import RawTransactionRecord

class FeedbackStore(ABC):
    """
    Interface for temporary storage of payment feedback records before ingestion.
    """
    @abstractmethod
    def add_record(self, record: RawTransactionRecord):
        pass

    @abstractmethod
    def get_all_records(self) -> List[RawTransactionRecord]:
        pass

    @abstractmethod
    def clear(self):
        pass

class InMemoryFeedbackStore(FeedbackStore):
    def __init__(self):
        self._records: List[RawTransactionRecord] = []

    def add_record(self, record: RawTransactionRecord):
        self._records.append(record)

    def get_all_records(self) -> List[RawTransactionRecord]:
        return list(self._records)

    def clear(self):
        self._records = []

class FeedbackCollector(ABC):
    """
    Interface for capturing payment results and converting them to canonical records.
    """
    @abstractmethod
    def collect(self, payment: Payment):
        pass

class LocalFeedbackCollector(FeedbackCollector):
    def __init__(self, store: FeedbackStore):
        self.store = store

    def collect(self, payment: Payment):
        """
        Maps a Payment record to a RawTransactionRecord and stores it.
        """
        # Map status to canonical ingestion status
        canonical_status = "succeeded" if payment.status == PaymentStatus.COMPLETED else "failed"
        
        # In a real system, latency_ms would be captured during execution.
        # Here we use a default or placeholder if not available.
        latency = 250 # Placeholder latency
        
        record = RawTransactionRecord(
            provider=payment.provider,
            payment_form="card_on_file", # Assumption from Payment record
            processing_type="standard",
            amount=payment.amount,
            currency=payment.currency,
            status=canonical_status,
            error_code=None if canonical_status == "succeeded" else "processor_error",
            latency_ms=latency,
            bin="000000", # Placeholder
            card_type="credit", # Placeholder
            network="visa",   # Placeholder
            region="domestic", # Placeholder
            timestamp=payment.updated_at or datetime.now(timezone.utc)
        )
        
        self.store.add_record(record)
