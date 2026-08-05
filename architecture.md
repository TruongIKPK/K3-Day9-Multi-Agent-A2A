# Multi-Agent E-Commerce Dispute Resolution System Architecture

> All sections below are expressed as Mermaid diagrams instead of plain tables/lists, so the whole spec renders visually in any Mermaid-aware viewer (GitHub, GitLab, mermaid.live, etc.).

## 1. System Architecture Diagram

```mermaid
graph TD
    UserCase[Input Case JSON: EC_xxx.json] --> Coordinator[Coordinator Agent]

    subgraph Domain_Extraction_Layer[Domain Data Agents - No LLM / Pure Data extraction]
        Coordinator -->|1. Extract Order Context| OrderAgent[Order Agent]
        Coordinator -->|2. Extract Payment Context| PaymentAgent[Payment Agent]
        OrderAgent -->|3. Pass Order Timeline| DeliveryAgent[Delivery Agent]
    end

    subgraph Business_Policy_Layer[Policy Rules Engine - Policy Agent]
        OrderAgent -->|Order Context| PolicyAgent[Policy Agent]
        PaymentAgent -->|Payment Context| PolicyAgent
        DeliveryAgent -->|Delivery Context| PolicyAgent
    end

    subgraph Verification_Layer[Schema and Verification - Verifier Agent]
        PolicyAgent -->|Policy Decision| VerifierAgent[Verifier Agent]
        Coordinator -->|Case Input| VerifierAgent
        VerifierAgent -->|Output Validation| AuditCheck{Passed Bounds and Rules?}
    end

    AuditCheck -->|YES| FinalJSON[Output JSON: EC_xxx.json]
    AuditCheck -->|NO| RetryHandler[Trigger Retry / Error Logging]

    subgraph Trace_System[Trace and Audit Trail]
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

```mermaid
flowchart TD
    subgraph Agents["Agent Contracts — Role · Allowed/Forbidden Data · Input to Output · Retry Strategy"]
        Coordinator["<b>Coordinator Agent</b><br/>Role: Case ingestion and workflow orchestration<br/>Allowed: CaseInput JSON metadata<br/>Forbidden: Olist CSV files, Policy business logic<br/>Contract: CaseInput to FinalOutput<br/>Retry: Exponential Backoff (3 attempts)"]
        OrderAgent["<b>Order Agent</b><br/>Role: Query order status, items, seller IDs, shipping limit dates<br/>Allowed: olist_orders_dataset.csv, olist_order_items_dataset.csv<br/>Forbidden: Payment tables, customer geolocation<br/>Contract: CaseInput to OrderContext<br/>Retry: Immediate Retry (2 attempts)"]
        PaymentAgent["<b>Payment Agent</b><br/>Role: Reconcile payment rows, sequence, installments, payment totals<br/>Allowed: olist_order_payments_dataset.csv<br/>Forbidden: Order items, delivery timestamps, sellers<br/>Contract: CaseInput to PaymentContext<br/>Retry: Immediate Retry (2 attempts)"]
        DeliveryAgent["<b>Delivery Agent</b><br/>Role: Compare actual vs estimated delivery timestamps and seller handoff limits<br/>Allowed: OrderContext timeline data<br/>Forbidden: CSV files, Payment rows<br/>Contract: OrderContext to DeliveryContext<br/>Retry: Immediate Retry (2 attempts)"]
        PolicyAgent["<b>Policy Agent</b><br/>Role: Evaluate EC_POLICY_V1 dispute logic, assign primary issue and refund<br/>Allowed: OrderContext, PaymentContext, DeliveryContext<br/>Forbidden: CSV files, raw database files<br/>Contract: Tuple(OrderContext, PaymentContext, DeliveryContext) to PolicyDecision<br/>Retry: Rule fallback to unsupported_late_claim"]
        VerifierAgent["<b>Verifier Agent</b><br/>Role: Verify output schema, financial totals, evidence syntax and bounds<br/>Allowed: CaseInput, Domain Contexts, PolicyDecision<br/>Forbidden: none<br/>Contract: Tuple(CaseInput, OrderContext, PaymentContext, PolicyDecision) to FinalOutput<br/>Retry: Fail fast and raise exception"]
    end

    OlistCSVLoader(["OlistCSVLoader"])
    OlistJoinHelper(["OlistJoinHelper"])
    OutputValidator(["OutputValidator"])
    OutputFS[["File System<br/>output/*.json"]]

    %% Handoff Target (solid)
    Coordinator -->|handoff| OrderAgent
    Coordinator -->|handoff| PaymentAgent
    OrderAgent -->|handoff| DeliveryAgent
    OrderAgent -->|handoff| PolicyAgent
    PaymentAgent -->|handoff| PolicyAgent
    DeliveryAgent -->|handoff| PolicyAgent
    PolicyAgent -->|handoff| VerifierAgent
    VerifierAgent -->|handoff| OutputFS

    %% Dependency (dashed)
    Coordinator -.->|depends on| OrderAgent
    Coordinator -.->|depends on| PaymentAgent
    Coordinator -.->|depends on| DeliveryAgent
    Coordinator -.->|depends on| PolicyAgent
    Coordinator -.->|depends on| VerifierAgent
    OrderAgent -.->|depends on| OlistCSVLoader
    OrderAgent -.->|depends on| OlistJoinHelper
    PaymentAgent -.->|depends on| OlistCSVLoader
    DeliveryAgent -.->|depends on| OrderAgent
    PolicyAgent -.->|depends on| OrderAgent
    PolicyAgent -.->|depends on| PaymentAgent
    PolicyAgent -.->|depends on| DeliveryAgent
    VerifierAgent -.->|depends on| OutputValidator
```

*Solid arrows = handoff target (who receives this agent's output next). Dashed arrows = dependency (what this agent needs before it can run — either an upstream agent's context or a helper module).*

---

## 3. Data Access & Boundary Matrix

```mermaid
flowchart LR
    subgraph Agents["Agents"]
        Coordinator[Coordinator Agent]
        OrderAgent[Order Agent]
        PaymentAgent[Payment Agent]
        DeliveryAgent[Delivery Agent]
        PolicyAgent[Policy Agent]
        VerifierAgent[Verifier Agent]
    end

    subgraph Resources["Data & Outputs"]
        Orders[("orders.csv")]
        Items[("order_items.csv")]
        Payments[("order_payments.csv")]
        Rules["Policy Rules"]
        Math["Financial Math"]
        OutputDir[["Write output/"]]
        TraceFile[["Write trace.jsonl"]]
    end

    OrderAgent -->|read| Orders
    OrderAgent -->|read| Items
    PaymentAgent -->|read| Payments
    PolicyAgent -->|apply| Rules
    PolicyAgent -->|compute| Math

    VerifierAgent -.->|write| OutputDir

    Coordinator -.->|write| TraceFile
    OrderAgent -.->|write| TraceFile
    PaymentAgent -.->|write| TraceFile
    DeliveryAgent -.->|write| TraceFile
    PolicyAgent -.->|write| TraceFile
    VerifierAgent -.->|write| TraceFile
```

*Only permitted (✅) accesses from the original boundary matrix are drawn — the absence of an edge between an agent and a resource means that access is forbidden (❌). `DeliveryAgent` has no edge into `Resources` besides trace logging: it computes purely over `OrderContext` passed in-memory from `OrderAgent`, never touching a CSV file directly.*

---

## 4. End-to-End Workflow Steps

```mermaid
sequenceDiagram
    participant Input as input/EC_xxx.json
    participant Coord as CoordinatorAgent
    participant Order as OrderAgent
    participant Payment as PaymentAgent
    participant Delivery as DeliveryAgent
    participant Policy as PolicyAgent
    participant Verifier as VerifierAgent
    participant Trace as trace.jsonl
    participant Output as output/EC_xxx.json

    Input->>Coord: CaseInput (claimed_order_id)

    Coord->>Order: 1. Order Domain Extraction
    Order-->>Coord: OrderContext
    Order-->>Trace: append TraceRecord

    Coord->>Payment: 2. Payment Domain Extraction
    Payment-->>Coord: PaymentContext
    Payment-->>Trace: append TraceRecord

    Coord->>Delivery: 3. Delivery Timeline Analysis (uses OrderContext)
    Delivery-->>Coord: DeliveryContext
    Delivery-->>Trace: append TraceRecord

    Coord->>Policy: 4. Policy Decision Engine
    Note right of Policy: Priority order — canceled-paid > unavailable-paid ><br/>late-delivery-seller > late-delivery-logistics ><br/>valid-split-payment > unsupported-late-claim
    Policy-->>Coord: PolicyDecision
    Policy-->>Trace: append TraceRecord

    Coord->>Verifier: 5. Output Verification
    Verifier->>Verifier: check entity/evidence bounds, confidence range
    alt Passed bounds and rules
        Verifier->>Output: 6. write output/EC_xxx.json
    else Failed validation
        Verifier--xCoord: raise ValueError (retry / error logging)
    end
    Verifier-->>Trace: append TraceRecord

    Coord-->>Trace: append TraceRecord (latency, status)
```

*Step 7 (Trace Logging) from the original list is not a separate final step — every agent (including the Coordinator itself) appends its own `TraceRecord` to `trace.jsonl` immediately after it runs, whether it succeeds or fails.*
