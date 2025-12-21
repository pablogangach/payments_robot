import uuid
from typing import Dict, List
from datetime import datetime, timezone
from app.models.payment import Payment, PaymentCreate, PaymentStatus, PaymentProvider
from app.models.fees import FeeStructure

import aisuite
import json
import requests
import os

from app.services.fee_service import FeeService
from app.services.routing_service import RoutingService

class PaymentService:
    def __init__(self, in_memory: bool = False):
        """
        Initializes the PaymentService.

        Args:
            in_memory: If True, uses an in-memory dictionary for storage.
                       This is useful for testing.
        """
        self.db: Dict[str, Payment] = {} if in_memory else db
        self.routing_service = RoutingService(fee_service=FeeService())
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")

    def create_payment(self, payment_create: PaymentCreate) -> Payment:
        now = datetime.now(timezone.utc)
        payment_id = str(uuid.uuid4())

        # *** AI Smart Routing Decision ***
        # The client no longer specifies the provider. The service decides.
        chosen_provider = self.routing_service.find_best_route(payment_create)
        payment_create.provider = chosen_provider

        if chosen_provider == PaymentProvider.STRIPE:
            # Create a PaymentIntent with the Stripe API
            response = requests.post(
                "https://api.stripe.com/v1/payment_intents",
                headers={"Authorization": f"Bearer {self.stripe_api_key}"},
                data={
                    "amount": int(payment_create.amount * 100),
                    "currency": payment_create.currency,
                    "description": payment_create.description,
                },
            )
            print(response.json())
            response.raise_for_status()
            intent = response.json()
            payment = Payment(
                id=payment_id,
                **payment_create.model_dump(exclude={"provider"}),
                status=PaymentStatus.PENDING,
                created_at=now,
                updated_at=now,
                provider=PaymentProvider.STRIPE,
                provider_payment_id=intent.get("id")
            )
            print(f"payment: {payment}")
        else: # Default to INTERNAL (LLM) flow
            client = aisuite.Client()
            completion = client.chat.completions.create(
                model="openai:gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in formatting data. You will be given a JSON object and you will add a `createdAt` field with a random date. You will only return the `createdAt` field in a JSON object."},
                    {"role": "user", "content": f"Here is the data: {payment_create.model_dump_json()}"}
                ],
                response_format={"type": "json_object"}
            )
            llm_response = completion.choices[0].message.content or "{}"
            output = json.loads(llm_response)
            created_at = output.get("createdAt", now)
            payment = Payment(
                id=payment_id, **payment_create.model_dump(), status=PaymentStatus.PENDING, created_at=created_at, updated_at=created_at
            )

        self.db[payment_id] = payment
        return payment

    def get_payment(self, payment_id: str) -> Payment | None:
        return self.db.get(payment_id)

    def get_all_payments(self) -> List[Payment]:
        return list(self.db.values())

    def authorize_payment(self, payment_id: str) -> Payment | None:
        payment = self.get_payment(payment_id)
        if payment and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.AUTHORIZED
            payment.updated_at = datetime.now(timezone.utc)
            return payment
        return None

    def settle_payment(self, payment_id: str) -> Payment | None:
        payment = self.get_payment(payment_id)
        if payment and payment.status == PaymentStatus.AUTHORIZED:
            payment.status = PaymentStatus.COMPLETED
            payment.updated_at = datetime.now(timezone.utc)
            return payment
        return None

    def cancel_payment(self, payment_id: str) -> Payment | None:
        payment = self.get_payment(payment_id)
        if payment and payment.status in [PaymentStatus.PENDING, PaymentStatus.AUTHORIZED]:
            payment.status = PaymentStatus.CANCELLED
            payment.updated_at = datetime.now(timezone.utc)
            return payment
        return None


# Global in-memory database for the main application
db: Dict[str, Payment] = {} # type: ignore

def get_payment_service():
    return PaymentService()
