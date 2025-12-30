from fastapi.testclient import TestClient
from fastapi import FastAPI
from payments_service.app.core.api import payments, merchants, customers
import json

app = FastAPI(title="Payments Service")

# Include the payments router with a prefix
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(merchants.router, tags=["merchants"])
app.include_router(customers.router, tags=["customers"])

client = TestClient(app)

def test_create_customer_success():
    """
    Scenario: Successfully register a customer under a merchant.
    Prerequisite: A valid merchant exists.
    """
    # 1. Create Merchant
    merchant_payload = {
        "name": "Gym A",
        "email": "gym_a@example.com",
        "mcc": "7997",
        "country": "US",
        "currency": "USD",
        "tax_id": "99-1234567",
        "banking_info": {"account_number": "111", "routing_number": "222"}
    }
    m_resp = client.post("/merchants", json=merchant_payload)
    assert m_resp.status_code == 201
    merchant_id = m_resp.json()["id"]

    # 2. Create Customer
    customer_payload = {
        "merchant_id": merchant_id,
        "name": "Globo Member",
        "email": "member@example.com",
        "payment_method_token": "tok_visa_4242"
    }
    response = client.post("/customers", json=customer_payload)
    
    # Assertions
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Globo Member"
    assert data["merchant_id"] == merchant_id
    assert "id" in data

def test_create_customer_invalid_merchant():
    """
    Scenario: Fail to create customer with non-existent merchant_id.
    """
    customer_payload = {
        "merchant_id": "non-existent-id",
        "name": "Lost Member",
        "email": "lost@example.com",
        "payment_method_token": "tok_visa_4242"
    }
    response = client.post("/customers", json=customer_payload)
    
    assert response.status_code == 404 # Should fail reference check

def test_get_customer_success():
    """
    Scenario: Retrieve customer by ID.
    """
    # 1. Setup Merchant & Customer
    m_resp = client.post("/merchants", json={
        "name": "Gym B", "email": "gym_b@example.com", "mcc": "7997", "country": "US", "currency": "USD", "tax_id": "88-7654321", "banking_info": {"account_number": "1", "routing_number": "2"}
    })
    merchant_id = m_resp.json()["id"]
    
    c_resp = client.post("/customers", json={
        "merchant_id": merchant_id, "name": "Tony Perkis", "email": "tony@heavyweights.com", "payment_method_token": "tok_amex_1234"
    })
    customer_id = c_resp.json()["id"]

    # 2. Get Customer
    response = client.get(f"/customers/{customer_id}")
    
    assert response.status_code == 200
    assert response.json()["name"] == "Tony Perkis"
