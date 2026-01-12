from typing import List, Dict
from collections import defaultdict
from ..ingestion.models import RawTransactionRecord
from .models import (
    ProviderPerformance, 
    RoutingDimension, 
    PerformanceMetrics,
    CostStructure
)
from .interfaces import IntelligenceStrategy

class StaticAggregationStrategy(IntelligenceStrategy):
    """
    A simple strategy that aggregates transaction records by dimension and provider
    to calculate basic performance metrics (averages).
    """

    def analyze(self, records: List[RawTransactionRecord]) -> List[ProviderPerformance]:
        # 1. Group by (Provider, RoutingDimension)
        grouped_data = defaultdict(list)
        
        for record in records:
            dim = RoutingDimension(
                payment_method_type="credit_card", # Simplification
                payment_form=record.payment_form,
                network=record.network,
                card_type=record.card_type,
                region=record.region,
                currency=record.currency
            )
            grouped_data[(record.provider, dim)].append(record)

        results = []
        
        # 2. Calculate metrics for each group
        for (provider, dim), provider_records in grouped_data.items():
            total_count = len(provider_records)
            success_count = sum(1 for r in provider_records if r.status == "succeeded")
            total_latency = sum(r.latency_ms for r in provider_records)
            
            auth_rate = success_count / total_count if total_count > 0 else 0.0
            avg_latency = int(total_latency / total_count) if total_count > 0 else 0
            
            # Simple static cost mapping for demonstration
            # In a real system, this would come from the record's actual cost or a fee engine
            metrics = PerformanceMetrics(
                auth_rate=auth_rate,
                fraud_rate=0.01, # Placeholder
                avg_latency_ms=avg_latency,
                cost_structure=CostStructure(
                    variable_fee_percent=2.9, # Placeholder
                    fixed_fee=0.30           # Placeholder
                )
            )
            
            results.append(ProviderPerformance(
                provider=provider,
                dimension=dim,
                metrics=metrics,
                data_window="batch"
            ))
            
        return results
