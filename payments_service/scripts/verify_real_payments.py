import sys
import os
import argparse
from dotenv import load_dotenv

# Add project root to path
sys.path.append("/Users/pabloganga/src/projects/payments_robot")

from payments_service.app.processors.adapters.stripe_adapter import StripeProcessor
from payments_service.app.processors.models.gateway import InternalChargeRequest, ProcessorStatus

def verify_stripe(amount: float, token: str):
    load_dotenv()
    print(f"--- Verifying Stripe Sandbox (Amount: {amount}, Token: {token}) ---")
    
    api_key = os.getenv("STRIPE_API_KEY")
    if not api_key:
        print("Warning: STRIPE_API_KEY not found in .env. Falling back to simulation mode.")
    
    processor = StripeProcessor(api_key=api_key)
    
    request = InternalChargeRequest(
        amount=amount,
        currency="USD",
        payment_method_token=token,
        merchant_id="test_merchant",
        customer_id="test_customer",
        description="Real Integration Verification Test"
    )
    
    response = processor.process_charge(request)
    
    if response.status == ProcessorStatus.SUCCESS:
        print(f"SUCCESS! Transaction ID: {response.processor_transaction_id}")
        # print(f"Raw Response: {response.raw_response}")
    else:
        print(f"FAILED: {response.error_code} - {response.error_message}")
        if response.raw_response:
             print(f"Error Details: {response.raw_response}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify real payment processor integration.")
    parser.add_argument("--provider", type=str, default="stripe", help="Provider to test (e.g. stripe)")
    parser.add_argument("--amount", type=float, default=1.0, help="Amount to charge")
    parser.add_argument("--token", type=str, default="tok_visa", help="Stripe test token (e.g. tok_visa, tok_chargeDeclined)")
    
    args = parser.parse_args()
    
    if args.provider == "stripe":
        verify_stripe(args.amount, args.token)
    else:
        print(f"Provider '{args.provider}' not yet supported in this verification script.")
