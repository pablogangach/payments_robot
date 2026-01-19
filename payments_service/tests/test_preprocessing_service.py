import pytest
from payments_service.app.routing.preprocessing.service import PreprocessingService
from payments_service.app.routing.decisioning import RoutingPerformanceRepository, ProviderPerformance, PerformanceMetrics, CostStructure, RoutingDimension
from payments_service.app.routing.preprocessing.models import BillingType, Customer, PaymentMethodDetails, Product
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.core.repositories.datastore import InMemoryDataStore

def test_preprocess_recurrent_payment():
    """
    Scenario: A recurrent payment is scheduled.
    The service should select the best route based on performance data.
    """
    store = InMemoryDataStore()
    repo = RoutingPerformanceRepository(store)
    service = PreprocessingService(repo)
    
    # Setup some test data in repo
    dim = RoutingDimension(
        payment_method_type="credit_card",
        payment_form="card_on_file",
        network="visa",
        card_type="credit",
        region="domestic",
        currency="USD"
    )
    
    perf = ProviderPerformance(
        provider=PaymentProvider.INTERNAL,
        dimension=dim,
        metrics=PerformanceMetrics(
            auth_rate=0.99,
            fraud_rate=0.01,
            avg_latency_ms=200,
            cost_structure=CostStructure(variable_fee_percent=1.0, fixed_fee=0.10)
        )
    )
    repo.save(perf)
    
    customer = Customer(id="cust_123", locale="en_US")
    payment_method = PaymentMethodDetails(type="credit_card", last4="4242")
    product = Product(id="prod_123", name="Subscription Product")

    route = service.preprocess_recurrent_payment(
        customer=customer,
        payment_method=payment_method,
        product=product,
        billing_type=BillingType.MONTHLY
    )
    
    # Logic currently selects lowest fixed fee
    assert route.processor == PaymentProvider.INTERNAL
    assert "lowest fixed fee" in route.routing_reason
