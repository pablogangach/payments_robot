# Routing Data Model Brainstorming

To make intelligent routing decisions, we need to move from hardcoded logic to a data-driven approach. The core idea is to query a "Performance Store" using a "Payment Context" to retrieve "Performance Metrics" for each candidate processor.

## 1. The Core Metrics (The "Value")
Based on your requirements, we need to track three key dimensions for each potential route:

1.  **Success Rate (Reliability)**
    *   *Definition*: Ratio of approved transactions to total attempts.
    *   *Usage*: Filter out providers below a reliability threshold or penalize them in scoring.
2.  **Cost / Scheme Fees (Efficiency)**
    *   *Definition*: Total estimated cost of the transaction (Fixed Fee + Variable % + FX markup + Scheme Fees).
    *   *Usage*: The primary factor for "Least Cost Routing".
3.  **Fraud Rate (Risk)**
    *   *Definition*: Ratio of chargebacks/fraud blocks to total transactions.
    *   *Usage*: Avoid providers where we have high fraud ratios to prevent mid identification flags.

## 2. The Dimensions (The "Key")
We can't just have one global success rate. It varies significantly based on context. We should model this as a hierarchical lookup.

Key Dimensions to slice data by:
*   **Payment Method**: `Credit Card` vs `Bank Transfer` vs `Digital Wallet`.
*   **Network (Scheme)**: `Visa`, `Mastercard`, `Amex`.
*   **Card Type**: `Debit` vs `Credit` (Debit is often cheaper).
*   **Segment/Region**: `Domestic` (US-to-US) vs `Cross-Border` (US-to-EU).
*   **Currency**: `USD`, `EUR`.

## 3. Proposed Data Entities

### A. `RoutingDimension`
Represents the "context" bucket.
```json
{
  "network": "VISA",
  "card_type": "CREDIT",
  "region": "domestic",
  "country": "US",
  "currency": "USD"
}
```

### B. `ProviderPerformance`
Represents the actual metrics for a specific Provider within a Dimension.
```json
{
  "provider_id": "stripe",
  "data_window": "30d", // e.g., rolling 30 days stats
  "metrics": {
    "auth_rate": 0.985,      // 98.5% success
    "fraud_rate": 0.001,     // 0.1% fraud
    "avg_latency_ms": 450,
    "cost_structure": {
      "interchange_plus_basis_points": 10, // Provider markup
      "fixed_fee": 0.30
    }
  }
}
```

## 4. Routing Strategy (The "Driver")
The "best" route is subjective. We will allow the request (or customer config) to specify a strategy.

**Strategies:**
*   `LOWEST_COST`: Strictly optimizes for the cheapest transaction. Good for low-margin merchants.
*   `HIGHEST_SUCCESS_RATE`: Optimizes for approval probability. Good for high-ticket or crucial subscriptions.
*   `HYBRID` (Default): Uses a weighted score.
    *   *Formula Idea*: `Score = (Weight_Cost * Normalized_Cost) + (Weight_Reliability * (1 - Auth_Rate))`
    *   Finds the "sweet spot" (e.g., Stripe is 0.1% more expensive but has 5% better uptime -> Choose Stripe).

## 5. Network Tokens Impact
Network tokens (EMV Payment Tokens) significantly change the game and must be modeled.

**Impacts:**
1.  **Success Rate**: Generally ~2-4% higher auth rates than raw PANs.
    *   *Model*: We need separate performance rows or a "lift" modifier for Tokenized vs PAN transactions.
2.  **Cost**: Often lower interchange fees or lower scheme fees for fully authenticated tokens.
3.  **Fraud**: Reduced fraud risk.

**Data Implication**:
Our `RoutingDimension` needs a flag: `is_network_tokenized: bool`.
Or, we can have a `TokenizationUplift` entity that stores the expected improvement for a given network/region.

## 6. Logical Flow in Preprocessing
1.  **Extract Context**: Convert the incoming `PaymentMethod` + `Customer` + `Product` into a `RoutingDimension` vector.
    *   *Check*: Is this card eligible for Network Tokenization? If yes, should we simulate the "Tokenized" scores?
2.  **Lookup Candidates**: Query the `PerformanceStore`.
3.  **Apply Strategy**:
    *   If `LOWEST_COST`: Sort by predicted fee.
    *   If `HIGHEST_SUCCESS`: Sort by `auth_rate`.
    *   If `HYBRID`: Calculate composite score.
4.  **Select**: Return best route.
