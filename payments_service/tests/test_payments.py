import pytest
from fastapi.testclient import TestClient
from payments_service.app.main import app
from payments_service.app.core.models.payment import PaymentProvider
from payments_service.app.core.api.dependencies import get_payment_service, store, merchant_repo, customer_repo
from payments_service.app.core.models.merchant import Merchant
from payments_service.app.core.models.customer import Customer
from unittest.mock import patch

@pytest.fixture
def client():
    """
    Provides a test client for the FastAPI application.
    Clears the in-memory store before each test.
    """
    # Clear the underlying store
    store._data.clear()
    
    # Pre-populate a merchant and customer for testing
    m = Merchant(
        id="m1", 
        name="Test Merchant", 
        tax_id="TAX123",
        email="merchant@example.com",
        mcc="5411",
        country="US",
        currency="USD"
    )
    merchant_repo.save(m)
    c = Customer(id="c1", merchant_id="m1", name="Test Customer", email="test@example.com", payment_method_token="tok_visa")
    customer_repo.save(c)
    
    with TestClient(app) as c:
        yield c

def test_create_charge(client: TestClient):
    """
    Tests creating a new charge.
    """
    charge_data = {
        "amount": 100.50, 
        "currency": "USD", 
        "merchant_id": "m1",
        "customer_id": "c1",
        "description": "Test charge"
    }
    response = client.post("/api/v1/payments/charges", json=charge_data)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == charge_data["amount"]
    assert data["currency"] == charge_data["currency"]
    assert data["status"] in ["completed", "failed"] # Real processors return success/fail
    assert "id" in data

def test_get_charge(client: TestClient):
    """
    Tests retrieving a specific charge by its ID.
    """
    charge_data = {
        "amount": 200.0, 
        "currency": "USD", 
        "merchant_id": "m1",
        "customer_id": "c1"
    }
    create_response = client.post("/api/v1/payments/charges", json=charge_data)
    charge_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/payments/charges/{charge_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == charge_id

def test_charge_not_found(client: TestClient):
    """
    Tests retrieving a non-existent charge.
    """
    response = client.get("/api/v1/payments/charges/non-existent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Charge not found"

def test_create_charge_invalid_merchant(client: TestClient):
    """
    Tests creating a charge for a non-existent merchant.
    """
    charge_data = {
        "amount": 100.0, 
        "currency": "USD", 
        "merchant_id": "missing_merchant",
        "customer_id": "c1"
    }
    response = client.post("/api/v1/payments/charges", json=charge_data)
    assert response.status_code == 404
    assert "Merchant" in response.json()["detail"]