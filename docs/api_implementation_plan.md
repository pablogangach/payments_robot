# Implementation Plan - Embedded Payments API

## Goal
Implement the core "Vertical SaaS" REST APIs to enable Merchant Onboarding, Customer Management, and Payment Processing.

## API Design

### 1. Merchant API (`/merchants`)
*   **Purpose**: Onboard the sub-merchant (the gym, the salon).
*   **Endpoints**:
    *   `POST /merchants`
        *   Input: `name`, `email`, `mcc` (category code), `country`, `currency`.
        *   **[NEW]** `banking_info` (account/routing numbers), `tax_id` (EIN/SSN). 
        *   Output: `Merchant` object with `id` and `status` (active/pending).
    *   `GET /merchants/{merchant_id}`

### 2. Customer API (`/customers`)
*   **Purpose**: Register the end-user (the gym member) who will be charged.
*   **Endpoints**:
    *   `POST /customers`
        *   Input: `merchant_id`, `email`, `name`, `payment_method_token` (from Vault).
        *   Output: `Customer` object.
    *   `GET /customers/{customer_id}`

### 3. Payment API (`/payments`)
*   **Purpose**: Execute a charge against a Customer.
*   **Endpoints**:
    *   `POST /charges`
        *   Input: `merchant_id`, `customer_id`, `amount`, `currency`, `description`.
        *   Logic:
            1.  Retrieve Merchant & Customer.
            2.  Call `PreprocessingService` to determine route.
            3.  Execute charge (Mock Processor for now).
    *   `GET /charges/{charge_id}`

## Execution Strategy: Vertical Slices (TDD)
We will build one domain at a time, starting with the Test, then the implementation layers.

### Phase 1: Merchants Vertical
1.  **Test**: Write `tests/api/test_merchants.py` (fail first).
2.  **Model**: Create `Merchant` model in `app/models/merchant.py`.
3.  **Repo**: Implement `MerchantRepository`.
4.  **Service**: Implement `MerchantService`.
5.  **API**: Create `POST /merchants` endpoint in `app/api/merchants.py`.
6.  **Verify**: Ensure tests pass.

### Phase 2: Customers Vertical
1.  **Test**: Write `tests/api/test_customers.py`.
2.  **Model**: Create `Customer` model (linking to Merchant).
3.  **Repo**: Implement `CustomerRepository`.
4.  **Service**: Implement `CustomerService`.
5.  **API**: Create `POST /customers` endpoint.
6.  **Verify**: Ensure tests pass.

### Phase 3: Charges Vertical (The Aggregator)
1.  **Test**: Write `tests/api/test_charges.py`.
2.  **Model**: Update `Payment` model to link `merchant_id` and `customer_id`.
3.  **Service**: Update `PaymentService` to coordinate:
    *   Fetch Merchant/Customer.
    *   Call `PreprocessingService` (Routing).
    *   Execute Charge.
4.  **API**: Create `POST /charges` endpoint.
5.  **Verify**: Full flow test.
