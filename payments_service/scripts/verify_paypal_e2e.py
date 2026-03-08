import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.append("/Users/pabloganga/src/projects/payments_robot")

from payments_service.app.core.models.payment import PaymentCreate, PaymentProvider, PaymentStatus
from payments_service.app.core.models.merchant import Merchant
from payments_service.app.core.models.customer import Customer
from payments_service.app.core.services.payment_service import PaymentService
from payments_service.app.core.repositories.payment_repository import PaymentRepository
from payments_service.app.core.repositories.merchant_repository import MerchantRepository
from payments_service.app.core.repositories.customer_repository import CustomerRepository
from payments_service.app.core.repositories.datastore import InMemoryRelationalStore
from payments_service.app.routing.preprocessing.service import RoutingService, FeeService
from payments_service.app.routing.decisioning.repository import RoutingPerformanceRepository
from payments_service.app.routing.decisioning.decision_strategies import FixedProviderStrategy
from payments_service.app.processors.registry import ProcessorRegistry
from payments_service.app.processors.adapters.paypal_adapter import PayPalProcessor

def verify_paypal_e2e():
    load_dotenv()
    print("--- STARTING PAYPAL E2E SANITY CHECK ---")
    
    # 1. Setup Infrastructure (In-Memory)
    payment_store = InMemoryRelationalStore()
    payment_repo = PaymentRepository(payment_store)
    
    merchant_store = InMemoryRelationalStore()
    merchant_repo = MerchantRepository(merchant_store)
    
    customer_store = InMemoryRelationalStore()
    customer_repo = CustomerRepository(customer_store)
    
    # Seed Merchant and Customer
    merchant_repo.save(Merchant(
        id="m_paypal_test", 
        name="PayPal Test Merchant", 
        email="merchant@example.com",
        mcc="5411",
        country="US",
        currency="USD",
        tax_id="12-3456789",
        api_key="test_key"
    ))
    customer_repo.save(Customer(
        id="c_paypal_test", 
        merchant_id="m_paypal_test",
        email="test@example.com", 
        payment_method_token="pm_card_visa" # PayPal adapter will use this for simulation in sandbox
    ))
    
    # 2. Setup Routing (Force PayPal)
    from payments_service.app.core.repositories.datastore import InMemoryKeyValueStore
    perf_kv_store = InMemoryKeyValueStore()
    perf_repo = RoutingPerformanceRepository(perf_kv_store)
    
    fee_service = FeeService()
    # FORCE PAYPAL
    strategy = FixedProviderStrategy(provider=PaymentProvider.PAYPAL)
    routing_service = RoutingService(fee_service=fee_service, performance_repository=perf_repo, strategy=strategy)
    
    # 3. Setup Processors
    processor_registry = ProcessorRegistry()
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    if not client_id or not secret:
        print("Error: PAYPAL_CLIENT_ID or PAYPAL_SECRET not found in .env")
        return
    
    processor_registry.register(PaymentProvider.PAYPAL, PayPalProcessor(client_id=client_id, secret=secret))
    
    # 4. Initialize Payment Service
    payment_service = PaymentService(
        payment_repo=payment_repo,
        merchant_repo=merchant_repo,
        customer_repo=customer_repo,
        routing_service=routing_service,
        processor_registry=processor_registry
    )
    
    # 5. EXECUTE CHARGE
    print("\n[STEP 1] Creating Charge (Forced to PayPal)...")
    charge_in = PaymentCreate(
        merchant_id="m_paypal_test",
        customer_id="c_paypal_test",
        amount=15.0,
        currency="USD",
        description="PayPal E2E Sanity Check"
    )
    
    payment = payment_service.create_charge(charge_in)
    print(f"Charge Result: Status={payment.status}, ProviderID={payment.provider_payment_id}")
    
    if payment.status != PaymentStatus.COMPLETED:
        # Check if we have an error message in the context or if we can get it from the service
        print(f"FAILURE: Charge was not completed. Final Status: {payment.status}")
        # Note: In a real app we'd check the payment.routing_decision or similar for logs
        return

    # 6. EXECUTE REFUND
    print(f"\n[STEP 2] Refunding Payment {payment.id}...")
    refunded_payment = payment_service.refund_payment(payment.id)
    print(f"Refund Result: Status={refunded_payment.status}")
    
    if refunded_payment.status == PaymentStatus.REFUNDED:
        print("\n--- E2E PAYPAL SANITY CHECK PASSED! ---")
    else:
        print("\n--- E2E PAYPAL SANITY CHECK FAILED! ---")

if __name__ == "__main__":
    try:
        verify_paypal_e2e()
    except Exception as e:
        print(f"Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
