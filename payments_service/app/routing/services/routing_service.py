import json
from typing import List
import aisuite
from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider
from payments_service.app.routing.models.fees import FeeStructure
from payments_service.app.routing.services.fee_service import FeeService


class RoutingService:
    def __init__(self, fee_service: FeeService):
        self.fee_service = fee_service
        self.client = aisuite.Client()

    def find_best_route(self, payment_create: PaymentCreate) -> PaymentProvider:
        """
        Uses an LLM to determine the best payment provider based on cost.
        """
        # If a provider is explicitly passed in the request, use it.
        # This is useful for testing or forcing a specific provider.
        if payment_create.provider:
            print(f"Forcing provider '{payment_create.provider.value}' as per request.")
            return payment_create.provider

        all_fees = self.fee_service.get_all_fees()
        fees_json = json.dumps([fee.model_dump() for fee in all_fees])
        payment_json = payment_create.model_dump_json()

        prompt = f"""
        You are an expert in payment processing, specializing in Least Cost Routing.
        Your task is to find the most cost-effective payment provider for a given transaction.

        Here is the list of available fee structures from our providers:
        {fees_json}

        Here is the incoming payment request:
        {payment_json}

        Analyze the fee structures and the payment details. Calculate the total fee for each provider.
        The fee is calculated as: (amount * (variable_fee_percent / 100)) + fixed_fee.
        Consider the most specific rule that applies (e.g., a 'domestic' rule is better than a 'default' one for a domestic payment).

        Based on your analysis, which provider offers the lowest total fee for this transaction?

        Return ONLY the provider's name in a JSON object, like this:
        {{"best_provider": "stripe"}}
        """

        completion = self.client.chat.completions.create(
            model="openai:gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that follows instructions precisely."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        response_data = json.loads(completion.choices[0].message.content or "{}")
        provider_name = response_data.get("best_provider", PaymentProvider.INTERNAL.value)
        print(f"AI Routing Decision: Chose '{provider_name}' for payment of {payment_create.amount} {payment_create.currency}")
        return PaymentProvider(provider_name)