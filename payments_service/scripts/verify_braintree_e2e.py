import os
from dotenv import load_dotenv
from payments_service.app.processors.adapters.braintree_adapter import BraintreeProcessor
from payments_service.app.processors.models import InternalChargeRequest

def verify_braintree_e2e():
    load_dotenv()
    
    print("--- Starting Braintree E2E Verification ---")
    
    mid = os.getenv("BRAINTREE_MERCHANT_ID")
    pub = os.getenv("BRAINTREE_PUBLIC_KEY")
    priv = os.getenv("BRAINTREE_PRIVATE_KEY")
    env = os.getenv("BRAINTREE_ENVIRONMENT", "sandbox")

    def mask(s):
        if not s: return "None"
        # Removing any accidental whitespace to be safe
        s_clean = s.strip()
        return f"'{s_clean[:4]}...{s_clean[-4:]}' (len: {len(s)})"

    print(f"Merchant ID: {mask(mid)}")
    print(f"Public Key:  {mask(pub)}")
    print(f"Private Key: {mask(priv)}")
    print(f"Environment: '{env}'")
    
    # 1. Initialize Processor
    processor = BraintreeProcessor(
        merchant_id=mid.strip() if mid else None,
        public_key=pub.strip() if pub else None,
        private_key=priv.strip() if priv else None,
        environment=env.strip() if env else "sandbox"
    )
    
    # 2. Process Charge
    request = InternalChargeRequest(
        amount=25.0,
        currency="USD",
        payment_method_token="fake-valid-nonce",
        merchant_id="merchant_123",
        customer_id="cust_123",
        description="Braintree E2E Test Diagnostic"
    )
    
    print(f"Executing Charge: {request.amount} {request.currency}...")
    charge_resp = processor.process_charge(request)
    
    if charge_resp.status == "success":
        print(f"✅ Charge Successful! Transaction ID: {charge_resp.processor_transaction_id}")
    else:
        print(f"❌ Charge Failed: {charge_resp.error_message}")
        print(f"Raw Response: {charge_resp.raw_response}")
        return

    # 3. Process Refund
    tx_id = charge_resp.processor_transaction_id
    print(f"Executing Refund for Transaction: {tx_id}...")
    refund_resp = processor.refund(tx_id)
    
    if refund_resp.status == "success":
        print(f"✅ Refund Successful! Refund ID: {refund_resp.processor_transaction_id}")
    else:
        print(f"❌ Refund Failed: {refund_resp.error_message}")

if __name__ == "__main__":
    verify_braintree_e2e()
