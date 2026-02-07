from fastapi.testclient import TestClient
from payments_service.app.main import app

client = TestClient(app)

def test_create_charge_success():
    """
    Scenario: Successfully execute an end-to-end charge.
    1. Create Merchant.
    2. Create Customer for that Merchant.
    3. Execute Charge using Merchant ID and Customer ID.
    """
    # 1. Setup Merchant
    m_resp = client.post("/merchants", json={
        "name": "Super Gym",
        "email": "ops@supergym.com",
        "mcc": "7997",
        "country": "US",
        "currency": "USD",
        "tax_id": "11-2223334",
        "banking_info": {"account_number": "123", "routing_number": "456"}
    })
    merchant_id = m_resp.json()["id"]

    # 2. Setup Customer
    c_resp = client.post("/customers", json={
        "merchant_id": merchant_id,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "payment_method_token": "tok_visa_4242"
    })
    customer_id = c_resp.json()["id"]

    # 3. Execute Charge
    charge_payload = {
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "amount": 49.99,
        "currency": "USD",
        "description": "Monthly Membership"
    }
    response = client.post("/api/v1/payments/charges", json=charge_payload)

    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending" or data["status"] == "completed"
    assert data["amount"] == 49.99
    assert data["merchant_id"] == merchant_id
    assert data["customer_id"] == customer_id
    assert "routing_decision" in data # Verification that LCR ran
