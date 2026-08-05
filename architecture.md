# Multi-Agent E-Commerce Dispute Resolution System Architecture

## 1. System Architecture Diagram

```mermaid
graph TD
    UserCase[Input Case JSON: EC_xxx.json] --> Coordinator[Coordinator Agent]
    
    subgraph Domain_Extraction_Layer[Domain Data Agents (No LLM / Pure Data extraction)]
        Coordinator -->|1. Extract Order Context| OrderAgent[Order Agent]
        Coordinator -->|2. Extract Payment Context| PaymentAgent[Payment Agent]
        OrderAgent -->|3. Pass Order Timeline| DeliveryAgent[Delivery Agent]
    end

    subgraph Business_Policy_Layer[Policy Rules Engine (Policy Agent)]
        OrderAgent -->|Order Context| PolicyAgent[Policy Agent]
        PaymentAgent -->|Payment Context| PolicyAgent
        DeliveryAgent -->|Delivery Context| PolicyAgent
    end

    subgraph Verification_Layer[Schema & Verification (Verifier Agent)]
        PolicyAgent -->|Policy Decision| VerifierAgent[Verifier Agent]
        Coordinator -->|Case Input| VerifierAgent
        VerifierAgent -->|Output Validation| AuditCheck{Passed Bounds & Rules?}
    end

    AuditCheck -->|YES| FinalJSON[Output JSON: EC_xxx.json]
    AuditCheck -->|NO| RetryHandler[Trigger Retry / Error Logging]

    subgraph Trace_System[Trace & Audit Trail]
        Coordinator -.->|Log Action| TraceJSONL[trace.jsonl]
        OrderAgent -.->|Log Action| TraceJSONL
        PaymentAgent -.->|Log Action| TraceJSONL
        DeliveryAgent -.->|Log Action| TraceJSONL
        PolicyAgent -.->|Log Action| TraceJSONL
        VerifierAgent -.->|Log Action| TraceJSONL
    end
```

---

## 2. Multi-Agent Design Table

| Agent Name | Primary Responsibility | Allowed Data | Forbidden Data | Input Contract | Output Contract | Handoff Target | Dependency | Retry Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Coordinator Agent** | Case ingestion & workflow orchestration | `CaseInput` JSON metadata | Olist CSV files, Policy business logic | `CaseInput` | `FinalOutput` | `OrderAgent`, `PaymentAgent` | All domain agents | Exponential Backoff (3 attempts) |
| **Order Agent** | Query order status, items, seller IDs, shipping limit dates | `olist_orders_dataset.csv`, `olist_order_items_dataset.csv` | Payment tables, customer geolocation | `CaseInput` | `OrderContext` | `DeliveryAgent`, `PolicyAgent` | `OlistCSVLoader`, `OlistJoinHelper` | Immediate Retry (2 attempts) |
| **Payment Agent** | Reconcile payment rows, sequence, installments, payment totals | `olist_order_payments_dataset.csv` | Order items, delivery timestamps, sellers | `CaseInput` | `PaymentContext` | `PolicyAgent` | `OlistCSVLoader` | Immediate Retry (2 attempts) |
| **Delivery Agent** | Compare actual vs estimated delivery timestamps & seller handoff limits | `OrderContext` timeline data | CSV files, Payment rows | `OrderContext` | `DeliveryContext` | `PolicyAgent` | `OrderAgent` | Immediate Retry (2 attempts) |
| **Policy Agent** | Evaluate EC_POLICY_V1 dispute logic & assign primary issue & refund | `OrderContext`, `PaymentContext`, `DeliveryContext` | CSV files, raw database files | `Tuple[OrderContext, PaymentContext, DeliveryContext]` | `PolicyDecision` | `VerifierAgent` | Domain Contexts | Rule Fallback to `unsupported_late_claim` |
| **Verifier Agent** | Verify output schema, financial totals, evidence syntax & bounds | `CaseInput`, Domain Contexts, `PolicyDecision` | None | `Tuple[CaseInput, OrderContext, PaymentContext, PolicyDecision]` | `FinalOutput` | File System (`output/*.json`) | `OutputValidator` | Fail Fast & Raise Exception |

---

## 3. Data Access & Boundary Matrix

| Agent | `orders.csv` | `order_items.csv` | `order_payments.csv` | Policy Rules | Financial Math | Write `output/` | Write `trace.jsonl` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coordinator Agent** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Order Agent** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Payment Agent** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Delivery Agent** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Policy Agent** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Verifier Agent** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 4. End-to-End Workflow Steps

1. **Case Ingestion**: `CoordinatorAgent` receives `EC_xxx.json` containing `claimed_order_id`.
2. **Order Domain Extraction**: `OrderAgent` loads order metadata and item rows, building `OrderContext`.
3. **Payment Domain Extraction**: `PaymentAgent` loads payment rows, summing total payment value into `PaymentContext`.
4. **Delivery Timeline Analysis**: `DeliveryAgent` processes timestamps from `OrderContext` to determine delivery delay and seller handoff delay into `DeliveryContext`.
5. **Policy Decision Engine**: `PolicyAgent` receives all 3 contexts and evaluates the strict priority rule table (Canceled Paid -> Unavailable Paid -> Late Delivery Seller -> Late Delivery Logistics -> Valid Split Payment -> Unsupported Late Claim), generating `PolicyDecision`.
6. **Output Verification**: `VerifierAgent` compiles `FinalOutput`, validates all entity count bounds ($\le 5$), evidence IDs ($\le 10$), confidence scores ($[0.0, 1.0]$), and writes verified output to `output/EC_xxx.json`.
7. **Trace Logging**: Every agent step logs latency, input/output summaries, and status to `trace.jsonl`.
