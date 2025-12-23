# Future Considerations & Backlog

This document captures topics, features, and complexities that we have identified but decided to defer to future iterations.

## 1. Account Updater Impact
*   **Context**: Specialized services from schemes (Visa/MC) or processors (Stripe/Adyen) that automatically update card details (expiry, new PAN) when cards are reissued.
*   **Impact on Routing**:
    *   *Staleness*: If we route based on old bin data, we might choose the wrong processor.
    *   *Cost*: Some processors charge for AU hits.
    *   *Success*: Using AU dramatically increases recurrent payment success. We need to model which processors offer this "for free" or effectively.

## 2. Dynamic Interchange & Scheme Fees
*   **Context**: Currently, we are modeling "Cost" as a possibly static or historical average. Payout fees are complex (Interchange ++).
*   **Requirement**: Build a real-time engine that looks up the exact Interchange Rate for a specific card type (e.g., "Visa Infinite Rewards") to calculate the precise margin.

## 3. Smart Fallbacks (Cascading)
*   **Context**: If the "Best" route declines the transaction (e.g., "Do Not Honor" or technical failure).
*   **Requirement**: The system should return an ordered list of routes (Primary, Secondary, Tertiary) so the payment orchestrator can retry intelligently without re-querying.

## 4. A/B Testing Framework
*   **Context**: How do we know "Hybrid Strategy" weights are correct?
*   **Requirement**: Ability to split traffic (e.g., 90% optimized, 10% random or control) to gather unbiased data on processor performance.

## 5. Regional Compliance & SCA
*   **Context**: PSD2/SCA in Europe requires 3DS.
*   **Impact**: Some routes handle 3DS better (frictionless flow). We need to factor "3DS Success Rate" into the model, not just "Auth Rate".

## 6. Real-time FX Optimization
*   **Context**: Cross-border payments involve currency conversion.
*   **Requirement**: Compare processor FX rates vs. market mid-market rates to find the hidden cost in the spread.

## 7. External Data Sources & Provenance
*   **Context**: We will eventually ingest performance data from external sources (benchmarks, aggregators) in addition to our own internal historical data.
*   **Requirement**: The `RoutingDataService` needs to track the `Source` of the data (e.g., `INTERNAL_HISTORY` vs `EXTERNAL_BENCHMARK`).
*   **Impact**: We might weigh internal data higher than external data, or use external data only for cold-starts when we have no history for a specific route.

## 8. LLM Strategy Agent
*   **Context**: Instead of hardcoded strategies or simple weighted formulas, we want to use an LLM to determine the best execution plan.
*   **Goal**: Provide the LLM with the Payment Context (User, Product, etc.) and a set of Tools (Fee Lookup, Reliability History, Fraud Check).
*   **Mechanism**: The LLM analyzes the context and tools to decide the optimal strategy (e.g., "High value customer + Recurring -> Prioritize Reliability over Cost"). It then executes the necessary lookups and returns the final route.

## 9. Fine-Tuned LLM Strategy
*   **Context**: Generic LLMs (like GPT-4) might be overkill or too slow/expensive for real-time routing decisions.
*   **Goal**: Train or fine-tune a smaller model (e.g., Llama 3 8B) specifically on our historical payment data and routing outcomes.
*   **Benefit**: Lower latency, reduced cost, and higher accuracy for our specific domain compared to a general-purpose model.

## 10. API Key Management & Scopes
*   **Context**: As we expose public APIs (`/merchants`, `/charges`), security is paramount.
*   **Requirement**: Implement a robust API Key management system.
    *   **Rotation**: Allow merchants to roll keys without downtime.
    *   **Scopes**: Granular permissions (e.g., `pk_live_...` for client-side tokenization vs `sk_live_...` for server-side charges).
    *   **Rate Limiting**: Throttling based on key usage tier.

## 11. Strategic Pivot: Master Merchant (PayFac) Model
*   **Context**: Instead of connecting merchants to Stripe/Adyen (ISO Model), **WE** act as the Merchant of Record (MoR) and sub-license to our users.
*   **Pros**:
    *   **Instant Onboarding**: No redirecting to Stripe. We approve them instantly.
    *   **Revenue**: We control the `Buy Rate` vs `Sell Rate`. We keep the full spread.
    *   **UX**: Totally unified experience.
*   **Cons (The Danger Zone)**:
    *   **Risk & Liability**: We are liable for ALL chargebacks and fraud. If a merchant vanishes, we pay.
    *   **Compass Compliance**: Requires sophisticated Risk/Underwriting engines (KYC/AML) and Money Transmitter Licenses (MTL) in some jurisdictions.
    *   **MCC Risks**: Schemes (Visa/MC) dislike "aggregators" masking different business types under one MCC.
*   **Verdict**: High Risk / High Reward. Usually a Phase 3+ evolution after finding product-market fit.

## 12. Instant Payouts (Push-to-Card)
*   **Context**: Merchants want money *now*. Supporting payouts to Debit Cards (via Visa Direct/Mastercard Send) which can be linked to Apple Pay.
*   **Requirement**:
    *   **Inbound**: Collect Debit Card number (or Apple Pay Token) instead of just Routing/Account number for payouts.
    *   **Mechanism**: Use "Original Credit Transaction" (OCT) or "Push to Card" rails.
*   **Pros**: Funds appear in seconds (vs T+2 days for ACH).
*   **Cons**: Higher cost (Push-to-Card fees).

## 13. Financial Inclusion: Serving the Unbanked (Issuing)
*   **Context**: Supporting merchants or gig-workers who physically cannot get a traditional bank account.
*   **Solution**: **Card Issuing** (Banking-as-a-Service).
*   **Mechanism**:
    *   We issue them a virtual or physical Debit Card (branded "PaymentsRobot").
    *   We hold the funds in a Stored Value Account (Wallet) on our platform.
    *   They spend the funds using the card we issued.
*   **Strategic Synergies**:
    *   **Interchange Arbitrage**: We use our own `Least Cost Routing` to optimize how we fund these accounts, maximizing the interchange revenue we keep.
    *   **Scale-First Pricing**: By automating everything, we keep fees for the unbanked near-zero. We win by volume (millions of users) rather than high margins per user.
*   **Impact**: Turns us from just a processor into a Neo-Bank. Huge value unlock but heavy regulatory lift.

## 14. Merchant Dashboard & Management API
*   **Context**: Merchants need visibility and control over their business.
*   **Requirement**:
    *   **Management API**: Endpoints to update business details, add team members, and rotate API keys.
    *   **Dashboard UI**: A frontend (React/Next.js) consuming our APIs.
    *   **Features**:
        *   Live transaction feed.
        *   Dispute management center.
        *   Payout settings and history.
        *   Virtual Terminal for manual charges.
