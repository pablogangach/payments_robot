# Embedded Payments Strategy: The Vertical SaaS Engine

## 1. Core Mission
To be the **defacto payments infrastructure for Vertical SaaS platforms**.
We enable software companies (e.g., Gym Management, Salon Booking, Construction ERPs) to become Fintechs by offering the **simplest**, **fastest**, and **lowest-cost** payments in the market.

## 2. The Competitive Advantage (The "Why Us")
We win by obsessively optimizing three specific pillars:

### A. Lowest Fees (AI-Driven Least Cost Routing)
*   **Problem**: Competitors use static routing or charge flat high rates.
*   **Our Solution**: Real-time, AI-driven routing that selects the cheapest path for *every single transaction*.
*   **Enabler**: The `PreprocessingService` and `RoutingDataManager` we are building.
*   **Goal**: Save merchants 10-30 bps compared to Stripe/Adyen standard blending.

### B. Simplest Integration (Developer Experience)
*   **Problem**: Legacy APIs are complex, SOAP-based, or widely inconsistent.
*   **Our Solution**: A "Three-Line Code" drop-in SDK.
    *   Entity-Centric API: `Charge(Customer, Amount)` - we handle the rest.
    *   Instant Onboarding: Automated KYC/KYB via API.
*   **Goal**: Time-to-Hello-World < 5 minutes.

### C. Fastest Processing (Performance)
*   **Problem**: Legacy rails are slow; batch processing delays funds.
*   **Our Solution**: Direct integrations and smart pathing to average <500ms latency.
*   **Goal**: Real-time authorization and faster payouts (T+0 options).

### D. Tablestakes (Non-Negotiables)
*   **Reliability**: Smart Fallbacks (cascading) to ensure 99.999% uptime.
*   **Compliance**: **PCI DSS Level 1 Service Provider** certification. This is mandatory since we own the Vault. Also GDPR/CCPA.

## 3. Master Plan & Artifact Index
To keep track of our ongoing architectural plans, here is the index of our technical strategy documents:

*   **[Routing Data Model](./routing_data_model.md)**: The data architecture for storing fees, success rates, and provider metrics. This powers our "Lowest Fees" pillar.
*   **[Future Considerations Backlog](./future_considerations.md)**: Advanced features like Account Updater, Fine-Tuned LLMs, and Dynamic Interchange.
*   **[Implementation Plan (Repository Refactor)](./implementation_plan.md)**: (Completed) The architecture refactor to separate reading (Preprocessing) from writing (Ingestion).

## 4. Prioritization Roadmap

### Phase 1: The Foundation (Current)
*   Build the `PreprocessingService` and `RoutingDataService` (Done).
*   Implement simple Least Cost Routing (In Progress).

### Phase 2: The "Simple Integration" API
*   Design public-facing REST API for `Merchants`, `Customers`, and `Payments`.
*   Abstract the complexity of the underlying routing.

### Phase 3: The AI Brain
*   Inject the [Fine-Tuned LLM Strategy](./future_considerations.md#9-fine-tuned-llm-strategy) into the routing engine.
*   Move from static rules to dynamic, context-aware optimizations.

## 5. Security Strategy: The Vault (Buy then Build)
*   **The Problem**: Building a PCI Level 1 Vault from scratch takes 6-12 months and slows down TTM.
*   **The Decision**: **Use a Tokenization Vendor (Proxy) Initially.**
    *   *Vendors*: VGS (Very Good Security), Spreedly, or Basis Theory.
*   **Mechanism**:
    1.  **Inbound**: Data goes to Vendor -> They return a token -> We store the token.
    2.  **Outbound**: We send the token + destination to Vendor -> They reveal PAN and send to Processor (Stripe/Adyen).
*   **Long-Term**: Once volume justifies the cost/effort, we will build our own Vault or acquire the capability to eliminate vendor fees.
*   **Benefit**: Launches us months earlier while still keeping Merchants out of PCI scope.

## 6. Settlement & Payouts Engine
*   **The Question**: If we route $50 via Stripe and $50 via Adyen, how does the merchant get their $100?
*   **The Challenge**: "Least Cost Routing" fragments funds across processors.
*   **Phase 1 Strategy: Unified Reporting, Separate Deposits**
    *   Processors settle directly to the Merchant's bank account (we manage the banking details during onboarding).
    *   *Result*: Merchant sees two deposits (Stripe: $50, Adyen: $50).
    *   *Our Job*: Provide a **Unified Reconciliation Dashboard** so they understand the total equals $100.
*   **Phase 2 Strategy: Unified Ledger (Master Payout)**
    *   We sit in the flow of funds (or use a partner like Modern Treasury).
    *   We aggregate the funds and send a **single deposit** ("PaymentsRobot Payout: $100").
    *   *Note*: Requires higher compliance (Money Transmission) or a banking partner.
