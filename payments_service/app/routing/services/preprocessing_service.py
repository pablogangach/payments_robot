from payments_service.app.routing.models.preprocessing import (
    PaymentContext, 
    PaymentRoute, 
    Customer, 
    PaymentMethodDetails, 
    Product, 
    BillingType
)
from payments_service.app.core.models.payment import PaymentProvider

class PreprocessingService:
    """
    Service to handle pre-processing of payments, such as preparing routes for recurring payments.
    Responsible for using data to determine the best route.
    """
    def __init__(self, performance_repository: 'RoutingPerformanceRepository'):
        self.performance_repository = performance_repository

    def preprocess_recurrent_payment(
        self, 
        customer: Customer, 
        payment_method: PaymentMethodDetails, 
        product: Product, 
        billing_type: BillingType
    ) -> PaymentRoute:
        """
        Determines the routing for a recurrent payment ahead of time.
        """
        
        context = PaymentContext(
            payment_method=payment_method,
            customer=customer,
            product=product,
            billing_type=billing_type
        )

        return self._determine_route(context)

    def _determine_route(self, context: PaymentContext) -> PaymentRoute:
        """
        Internal logic to determine the best payment route based on the context.
        """
        from payments_service.app.routing.models.routing_data import RoutingDimension
        
        # 1. Build Dimension from Context
        # TODO: Map real card details (bin lookup) to network/type. Hardcoded for now.
        dimension = RoutingDimension(
            payment_method_type=context.payment_method.type,
            payment_form="card_on_file", # Placeholder mapping
            network="visa", # Placeholder mapping
            card_type="credit", # Placeholder mapping
            region="domestic", # Placeholder mapping
            currency="USD"
        )

        # 2. Get Candidates via Repository
        candidates = self.performance_repository.find_by_dimension(dimension)
        
        if not candidates:
             # Fallback if no data found
            return PaymentRoute(
                processor=PaymentProvider.STRIPE,
                routing_reason="Default Fallback: No performance data found"
            )

        # 3. Select Best (Simple Lowest Cost implementation for now)
        # TODO: Implement full Hybrid strategy
        best_candidate = min(candidates, key=lambda c: c.metrics.cost_structure.fixed_fee)

        return PaymentRoute(
            processor=best_candidate.provider,
            routing_reason=f"Selected based on lowest fixed fee: {best_candidate.metrics.cost_structure.fixed_fee}"
        )
