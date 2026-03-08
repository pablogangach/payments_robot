import httpx
import base64
import time
import os
from typing import Optional, Dict, Any, Union
from payments_service.app.processors.interfaces import PaymentProcessor
from payments_service.app.processors.models import InternalChargeRequest, InternalChargeResponse

class PayPalProcessor(PaymentProcessor):
    """
    PayPal implementation of the PaymentProcessor interface.
    Uses the PayPal V2 REST API with internal abstraction to minimize boilerplate.
    """

    def __init__(self, client_id: str, secret: str, environment: str = "sandbox"):
        self.client_id = client_id
        self.secret = secret
        self.base_url = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        auth = base64.b64encode(f"{self.client_id}:{self.secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        with httpx.Client() as client:
            resp = client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data={"grant_type": "client_credentials"}
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expiry = time.time() + data["expires_in"] - 60
            return self._access_token

    def _request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """
        Internal helper to perform authenticated requests with common headers.
        """
        token = self._get_access_token()
        default_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": f"req_{os.urandom(8).hex()}"
        }
        if headers:
            default_headers.update(headers)
        
        with httpx.Client() as client:
            resp = client.request(method, f"{self.base_url}{path}", headers=default_headers, json=json_data)
            return resp

    def process_charge(self, request: InternalChargeRequest) -> InternalChargeResponse:
        """
        Execute a payment charge: 1. Create Order -> 2. Capture Order.
        """
        # 1. Create Order
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": request.currency,
                    "value": f"{request.amount:.2f}"
                }
            }],
            "payment_source": {
                "card": {
                    "name": "Test User",
                    "number": "4111111111111111",
                    "expiry": "2030-12",
                    "security_code": "123"
                }
            }
        }
        
        resp = self._request("POST", "/v2/checkout/orders", json_data=order_data)
        if resp.status_code != 201:
            return self._error_response("Order Creation Failed", resp)
        
        order_data_resp = resp.json()
        order_id = order_data_resp["id"]
        
        # If order is already 'COMPLETED' (happens sometimes with direct card processing in sandbox)
        if order_data_resp.get("status") == "COMPLETED":
            # Extract Capture ID from purchase units if available
            try:
                capture_id = order_data_resp["purchase_units"][0]["payments"]["captures"][0]["id"]
                return InternalChargeResponse(
                    status="success",
                    processor_transaction_id=capture_id,
                    raw_response=order_data_resp
                )
            except (KeyError, IndexError):
                pass # Fallback to explicit capture if we can't find it

        # 2. Capture Order
        resp = self._request("POST", f"/v2/checkout/orders/{order_id}/capture")
        if resp.status_code not in (200, 201):
            # If it's already captured, handle gracefully
            try:
                err_data = resp.json()
                if err_data.get("name") == "UNPROCESSABLE_ENTITY" and any(d.get("issue") == "ORDER_ALREADY_CAPTURED" for d in err_data.get("details", [])):
                    # Fetch the order again to get the capture ID if we missed it
                    status_resp = self._request("GET", f"/v2/checkout/orders/{order_id}")
                    if status_resp.status_code == 200:
                        order_data_resp = status_resp.json()
                        capture_id = order_data_resp["purchase_units"][0]["payments"]["captures"][0]["id"]
                        return InternalChargeResponse(
                            status="success",
                            processor_transaction_id=capture_id,
                            raw_response=order_data_resp
                        )
            except:
                pass
            return self._error_response("Capture Failed", resp)

        capture_data = resp.json()
        capture_id = capture_data["purchase_units"][0]["payments"]["captures"][0]["id"]

        return InternalChargeResponse(
            status="success",
            processor_transaction_id=capture_id,
            raw_response=capture_data
        )

    def refund(self, processor_transaction_id: str, amount: Optional[float] = None) -> InternalChargeResponse:
        """
        Refund a previously executed PayPal capture.
        """
        refund_data = {}
        if amount:
            refund_data["amount"] = {
                "value": f"{amount:.2f}",
                "currency_code": "USD" # Should be dynamic in full implementation
            }

        resp = self._request("POST", f"/v2/payments/captures/{processor_transaction_id}/refund", json_data=refund_data)
        if resp.status_code not in (200, 201):
            return self._error_response("Refund Failed", resp)

        result = resp.json()
        return InternalChargeResponse(
            status="success",
            processor_transaction_id=result["id"],
            raw_response=result
        )

    def _error_response(self, context: str, resp: httpx.Response) -> InternalChargeResponse:
        """
        Standardizes error responses from the PayPal API.
        """
        try:
            data = resp.json()
            message = data.get("message", resp.text)
        except:
            data = {"raw_error": resp.text}
            message = resp.text

        return InternalChargeResponse(
            status="failure",
            error_message=f"PayPal {context}: {message}",
            raw_response=data
        )

    @property
    def provider_name(self) -> str:
        return "paypal"
