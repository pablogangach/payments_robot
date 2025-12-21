import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.payment import Payment, PaymentCreate
from app.api.payments import get_payment_service
from app.services.payment_service import PaymentService, db


@pytest.fixture
def client():
    """
    Provides a test client for the FastAPI application,
    overriding the payment_service dependency with an in-memory version.
    """
    in_memory_service = PaymentService(in_memory=True)
    db.clear()
    app.dependency_overrides[get_payment_service] = lambda: in_memory_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_payment(client: TestClient):
    """
    Tests creating a new payment.
    """
    payment_data = {"amount": 100.50, "currency": "USD", "description": "Test payment"}
    response = client.post("/api/v1/payments", json=payment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == payment_data["amount"]
    assert data["currency"] == payment_data["currency"]
    assert data["description"] == payment_data["description"]
    assert "id" in data and "created_at" in data


def test_get_payment(client: TestClient):
    """
    Tests retrieving a specific payment by its ID.
    """
    payment_data = {"amount": 200.0, "currency": "EUR", "description": "Another test"}
    create_response = client.post("/api/v1/payments", json=payment_data)
    payment_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/payments/{payment_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == payment_id
    assert data["amount"] == payment_data["amount"]


def test_get_payment_not_found(client: TestClient):
    """
    Tests retrieving a non-existent payment, expecting a 404 error.
    """
    response = client.get("/api/v1/payments/non-existent-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Payment not found"}


def test_get_all_payments(client: TestClient):
    """
    Tests retrieving all payments.
    """
    # Create two new payments
    client.post("/api/v1/payments", json={"amount": 50, "currency": "GBP", "description": "First"}) # type: ignore
    client.post("/api/v1/payments", json={"amount": 75, "currency": "JPY", "description": "Second"}) # type: ignore

    response = client.get("/api/v1/payments")
    assert response.status_code == 200
    payments = response.json()
    assert len(payments) == 2
    assert payments[0]["amount"] == 50
    assert payments[1]["amount"] == 75


def test_full_payment_flow(client: TestClient):
    """
    Tests the full authorize and settle flow.
    """
    # 1. Create Payment
    payment_data = {"amount": 100.0, "currency": "USD", "description": "E2E Test"}
    response = client.post("/api/v1/payments", json=payment_data)
    assert response.status_code == 201
    payment = response.json()
    payment_id = payment["id"]
    assert payment["status"] == "pending"
    created_at = payment["created_at"]
    updated_at = payment["updated_at"]
    assert created_at == updated_at

    # 2. Authorize Payment
    response = client.post(f"/api/v1/payments/{payment_id}/authorize")
    assert response.status_code == 200
    payment = response.json()
    assert payment["status"] == "authorized"
    assert payment["updated_at"] > updated_at
    # Keep track of the last update time
    updated_at = payment["updated_at"]

    # 3. Settle Payment
    response = client.post(f"/api/v1/payments/{payment_id}/settle")
    assert response.status_code == 200
    payment = response.json()
    assert payment["status"] == "completed"
    assert payment["updated_at"] > updated_at


def test_cancel_pending_payment(client: TestClient):
    """
    Tests cancelling a payment that is still pending.
    """
    payment_data = {"amount": 25.0, "currency": "JPY"}
    response = client.post("/api/v1/payments", json=payment_data)
    assert response.status_code == 201
    payment_id = response.json()["id"]

    # Cancel the pending payment
    response = client.post(f"/api/v1/payments/{payment_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_authorized_payment(client: TestClient):
    """
    Tests cancelling an authorized payment.
    """
    payment_data = {"amount": 50.0, "currency": "EUR", "description": "Cancel Test"}
    response = client.post("/api/v1/payments", json=payment_data)
    payment_id = response.json()["id"]

    # Authorize
    response = client.post(f"/api/v1/payments/{payment_id}/authorize")
    assert response.status_code == 200
    assert response.json()["status"] == "authorized"

    # Cancel
    response = client.post(f"/api/v1/payments/{payment_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_create_stripe_payment(client: TestClient, monkeypatch):
    """
    Tests creating a payment with the actual Stripe API.
    Forces the routing service to select Stripe as the provider.
    """
    from unittest.mock import MagicMock, patch
    from app.models.payment import PaymentProvider

    payment_data = {"amount": 150.75, "currency": "USD", "description": "Stripe test payment"}

    # Mock the routing service to force Stripe provider selection
    with patch("app.services.payment_service.RoutingService.find_best_route") as mock_route:
        mock_route.return_value = PaymentProvider.STRIPE
        response = client.post("/api/v1/payments", json=payment_data)

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == payment_data["amount"]
    assert data["currency"] == payment_data["currency"]
    assert data["description"] == payment_data["description"]
    assert data["provider"] == "stripe"
    assert "provider_payment_id" in data  # Stripe returns a real payment intent ID
    assert data["provider_payment_id"].startswith("pi_")  # Stripe PaymentIntent IDs start with "pi_"
    assert data["status"] == "pending"


def test_invalid_state_transitions(client: TestClient):
    """
    Tests that invalid state transitions are rejected.
    """
    payment_data = {"amount": 500.0, "currency": "GBP"}
    response = client.post("/api/v1/payments", json=payment_data)
    payment_id = response.json()["id"]

    # 1. Try to settle a pending payment (should fail)
    response = client.post(f"/api/v1/payments/{payment_id}/settle")
    assert response.status_code == 400

    # 2. Authorize the payment, then try to authorize it again (should fail)
    client.post(f"/api/v1/payments/{payment_id}/authorize")
    response = client.post(f"/api/v1/payments/{payment_id}/authorize")
    assert response.status_code == 400