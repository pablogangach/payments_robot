import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from payments_service.app.routing.preprocessing.service import PreprocessingService
from payments_service.app.core.models.subscription import Subscription
from payments_service.app.core.models.payment import PaymentProvider

def test_precalculate_upcoming_renewals_logic():
    # Setup Mocks
    mock_perf_repo = MagicMock()
    mock_sub_repo = MagicMock()
    mock_precalc_repo = MagicMock()
    mock_routing_svc = MagicMock()
    
    svc = PreprocessingService(
        performance_repository=mock_perf_repo,
        subscription_repository=mock_sub_repo,
        precalculated_route_repository=mock_precalc_repo,
        routing_service=mock_routing_svc
    )
    
    now = datetime.now(timezone.utc)
    sub = Subscription(
        id="sub1",
        customer_id="c1",
        merchant_id="m1",
        amount=50.0,
        currency="USD",
        next_renewal_at=now + timedelta(days=3)
    )
    
    mock_sub_repo.find_upcoming_renewals.return_value = [sub]
    mock_routing_svc.find_best_route.return_value = PaymentProvider.ADYEN
    
    # Execute
    svc.precalculate_upcoming_renewals(lookahead_days=7)
    
    # Verify
    mock_sub_repo.find_upcoming_renewals.assert_called_once()
    mock_routing_svc.find_best_route.assert_called_once()
    mock_precalc_repo.save.assert_called_once()
    
    # Check save payload
    args, _ = mock_precalc_repo.save.call_args
    route_in = args[0]
    assert route_in.subscription_id == "sub1"
    assert route_in.provider == PaymentProvider.ADYEN
    assert route_in.expires_at > sub.next_renewal_at
