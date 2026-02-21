from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from .models import RawTransactionRecord
from payments_service.app.core.models.payment import PaymentProvider

class BaseTransactionParser(ABC):
    """
    Abstract base class for vendor-specific transaction parsers.
    """
    @abstractmethod
    def parse(self, row: Dict[str, Any]) -> RawTransactionRecord:
        """
        Transforms a raw row (usually from CSV) into a canonical RawTransactionRecord.
        """
        pass

class StripeCsvParser(BaseTransactionParser):
    """
    Parses Stripe's balance transaction report CSV.
    """
    def parse(self, row: Dict[str, Any]) -> RawTransactionRecord:
        # Core fields mapping
        core_mapping = {
            "amount": float(row["amount"]),
            "currency": row["currency"].upper(),
            "status": "succeeded" if row["status"] == "available" else "failed",
            "latency_ms": 0,
            "bin": "000000",
            "card_type": "credit",
            "network": row["card_brand"].lower(),
            "region": "domestic" if row["card_country"] == "US" else "international",
            "timestamp": datetime.strptime(row["created"], "%Y-%m-%d %H:%M:%S")
        }
        
        # Captured unmapped fields as extra_fields
        mapped_keys = {"amount", "currency", "status", "card_brand", "card_country", "created"}
        extra = {k: v for k, v in row.items() if k not in mapped_keys}

        return RawTransactionRecord(
            provider=PaymentProvider.STRIPE,
            payment_form="card_on_file",
            processing_type="signature",
            extra_fields=extra,
            **core_mapping
        )

class AdyenCsvParser(BaseTransactionParser):
    """
    Parses Adyen's Payment Accounting Report CSV.
    """
    def parse(self, row: Dict[str, Any]) -> RawTransactionRecord:
        # Core fields mapping
        core_mapping = {
            "amount": float(row["Gross Debit"]),
            "currency": row["Currency"].upper(),
            "status": "succeeded" if row["Type"] == "Settled" else "failed",
            "latency_ms": 0,
            "bin": "000000",
            "card_type": "credit",
            "network": row["Payment Method"].lower(),
            "region": "domestic",
            "timestamp": datetime.strptime(row["Creation Date"], "%Y-%m-%d %H:%M:%S")
        }

        # Captured unmapped fields as extra_fields
        mapped_keys = {"Gross Debit", "Currency", "Type", "Payment Method", "Creation Date", "Status", "Merchant Reference", "PSP Reference"}
        extra = {k: v for k, v in row.items() if k not in mapped_keys}

        return RawTransactionRecord(
            provider=PaymentProvider.ADYEN,
            payment_form="card_on_file",
            processing_type="signature",
            extra_fields=extra,
            **core_mapping
        )
