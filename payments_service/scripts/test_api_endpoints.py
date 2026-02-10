import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, path, data=None):
    print(f"\n--- Testing {name} ({method} {path}) ---")
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return response.json()
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def main():
    # 1. Root
    test_endpoint("Root", "GET", "/")

    # 2. Onboard Merchant
    merchant_id = f"test_merchant_{uuid.uuid4().hex[:6]}"
    merchant_data = {
        "id": merchant_id,
        "name": "Acme Corp",
        "email": f"contact@{merchant_id}.com",
        "mcc": "5411",
        "country": "US",
        "currency": "USD",
        "tax_id": "99-8887776",
        "banking_info": {"routing_number": "123", "account_number": "456"}
    }
    merchant = test_endpoint("Create Merchant", "POST", "/merchants", merchant_data)
    if merchant:
        actual_merchant_id = merchant['id']
        test_endpoint("Get Merchant", "GET", f"/merchants/{actual_merchant_id}")

    # 3. Create Customer
    customer_id = f"test_cust_{uuid.uuid4().hex[:6]}"
    customer_data = {
        "merchant_id": actual_merchant_id if merchant else "default_merchant",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "payment_method_token": "tok_visa_4242"
    }
    customer = test_endpoint("Create Customer", "POST", "/customers", customer_data)
    if customer:
        actual_customer_id = customer['id']
        test_endpoint("Get Customer", "GET", f"/customers/{actual_customer_id}")

    # 4. Create Charge
    charge_data = {
        "merchant_id": actual_merchant_id if merchant else "default_merchant",
        "customer_id": actual_customer_id if customer else "cust_123",
        "amount": 50.0,
        "currency": "USD",
        "description": "Test API Charge"
    }
    charge = test_endpoint("Create Charge", "POST", "/api/v1/payments/charge", charge_data)
    
    # 5. Get Recent Charges
    test_endpoint("List Recent Charges", "GET", "/api/v1/payments/recent")

    # 6. Get Specific Charge
    if charge:
        test_endpoint("Get Specific Charge", "GET", f"/api/v1/payments/charges/{charge['id']}")

if __name__ == "__main__":
    main()
