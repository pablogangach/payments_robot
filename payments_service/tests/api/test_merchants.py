from fastapi.testclient import TestClient
from fastapi import FastAPI
from payments_service.app.api import payments, merchants
import json

app = FastAPI(title="Payments Service")

# Include the payments router with a prefix
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(merchants.router, tags=["merchants"])

client = TestClient(app)

def test_create_merchant_success():
    """
    Scenario: Successfully onboarding a new merchant.
    Input: Valid name, email, country, currency.
    Output: 201 Created with merchant ID and status 'active'.
    """
    payload = {
        "name": "Globo Gym",
        "email": "white.goodman@globogym.com",
        "mcc": "7997", # Membership Clubs
        "country": "US",
        "currency": "USD",
        "tax_id": "12-3456789",
        "banking_info": {
            "account_number": "1234567890",
            "routing_number": "021000021"
        }
    }

    response = client.post("/merchants", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["id"] is not None
    assert data["status"] == "active"
    assert data["api_key"] is not None # We should return a key for them to use

def test_create_merchant_validation_error():
    """
    Scenario: Failing to create merchant due to invalid data.
    Input: Missing name.
    Output: 422 Unprocessable Entity.
    """
    payload = {
        "email": "incomplete@example.com"
        # Missing name and other fields
    }

    response = client.post("/merchants", json=payload)

    assert response.status_code == 422

def test_get_merchant_success():
    """
    Scenario: Retrieving a merchant by ID.
    Pre-req: Create a merchant.
    """
    # 1. Create
    create_payload = {
        "name": "Average Joes",
        "email": "peter@averagejoes.com",
        "mcc": "7997",
        "country": "US",
        "currency": "USD",
        "tax_id": "88-8888888",
        "banking_info": {
            "account_number": "9876543210",
            "routing_number": "123456789"
        }
    }
    create_resp = client.post("/merchants", json=create_payload)
    print(f"create_resp: {create_resp.json()}")
    merchant_id = create_resp.json()["id"]

    # 2. Get
    response = client.get(f"/merchants/{merchant_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == merchant_id
    assert data["name"] == "Average Joes"

def test_get_merchant_not_found():
    """
    Scenario: Trying to get a non-existent merchant.
    """
    response = client.get("/merchants/non_existent_id")
    assert response.status_code == 404

def test_create_merchant_duplicate_tax_id():
    """
    Scenario: Prevent registering two merchants with the same Tax ID (EIN).
    """
    payload_1 = {
        "name": "Gym A",
        "email": "owner@example.com",
        "mcc": "7997",
        "country": "US",
        "currency": "USD",
        "tax_id": "99-9999999"
    }
    client.post("/merchants", json=payload_1)

    # Retry with same Tax ID, different email/name
    payload_2 = payload_1.copy()
    payload_2["name"] = "Gym B"
    payload_2["email"] = "other@example.com"
    
    response = client.post("/merchants", json=payload_2)
    assert response.status_code == 409 # Conflict

def test_create_merchant_same_email_allowed():
    """
    Scenario: Allow same email for different businesses (different Tax IDs).
    """
    email = "serial_entrepreneur@example.com"
    
    # Business 1
    client.post("/merchants", json={
        "name": "My Gym",
        "email": email,
        "mcc": "7997",
        "country": "US",
        "currency": "USD",
        "tax_id": "11-1111111"
    })

    # Business 2 (Same Email, Different Tax ID)
    response = client.post("/merchants", json={
        "name": "My Salon",
        "email": email,
        "mcc": "7230",
        "country": "US",
        "currency": "USD",
        "tax_id": "22-2222222"
    })
    
    assert response.status_code == 201
    assert response.json()["name"] == "My Salon"

def test_create_merchant_invalid_data():
    """
    Scenario: Validate data formats (invalid email, unsupported currency).
    """
    payload = {
        "name": "Bad Data Gym",
        "email": "not-an-email",
        "mcc": "7997",
        "country": "ZZ", # Invalid Country
        "currency": "XYZ" # Invalid Currency
    }
    response = client.post("/merchants", json=payload)
    assert response.status_code == 422

