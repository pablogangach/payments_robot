from typing import List
from payments_service.app.routing.models.fees import FeeStructure
from payments_service.app.core.models.payment import PaymentProvider


class FeeService:
    def __init__(self):
        # In a real application, this would come from a database.
        # This is our simulated fee data.
        self.fees: List[FeeStructure] = [
            # --- Stripe Fees ---
            FeeStructure(
                provider=PaymentProvider.STRIPE,
                region="domestic",
                fixed_fee=0.30,
                variable_fee_percent=2.9,
            ),
            FeeStructure(
                provider=PaymentProvider.STRIPE,
                region="international",
                fixed_fee=0.30,
                variable_fee_percent=3.9, # Higher fee for international cards
            ),
            # --- Internal/Local Provider Fees (Simulated) ---
            FeeStructure(
                provider=PaymentProvider.INTERNAL,
                region="domestic",
                card_type="debit",
                fixed_fee=0.25,
                variable_fee_percent=1.0, # Cheaper for domestic debit
            ),
            FeeStructure(
                provider=PaymentProvider.INTERNAL,
                fixed_fee=0.50, # Higher fixed fee but maybe lower variable
                variable_fee_percent=2.5,
            ),
        ]

    def get_all_fees(self) -> List[FeeStructure]:
        return self.fees