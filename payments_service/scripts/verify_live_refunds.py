import sys
import os
import argparse
from dotenv import load_dotenv

# Add project root to path
sys.path.append("/Users/pabloganga/src/projects/payments_robot")

from payments_service.app.processors.adapters.stripe_adapter import StripeProcessor
from payments_service.app.processors.models.gateway import InternalChargeRequest, ProcessorStatus

def verify_refund(transaction_id: str, amount: float = None):
    load_dotenv()
    print(f"--- Verifying Stripe Refund (ID: {transaction_id}, Amount: {amount if amount else 'Full'}) ---")
    
    api_key = os.getenv("STRIPE_API_KEY")
    if not api_key:
        print("Error: STRIPE_API_KEY not found in .env. Cannot perform live refund.")
        return
    
    processor = StripeProcessor(api_key=api_key)
    
    # In a real scenario, we might want to fetch the original charge first, 
    # but for a simple verification, we can try to refund directly.
    response = processor.refund(processor_transaction_id=transaction_id, amount=amount)
    
    if response.status == ProcessorStatus.SUCCESS:
        print(f"SUCCESS! Refund ID: {response.processor_transaction_id}")
    else:
        print(f"FAILED: {response.error_code} - {response.error_message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify live refund flow.")
    parser.add_argument("transaction_id", type=str, help="Stripe PaymentIntent ID to refund (e.g. pi_...)")
    parser.add_argument("--amount", type=float, help="Partial amount to refund (optional)")
    
    args = parser.parse_args()
    verify_refund(args.transaction_id, args.amount)
