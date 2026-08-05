# Task Allocation & Ownership Matrix (4 Team Members)

Project: Multi-Agent E-commerce Dispute Resolution (Olist Dataset)
Team Members: Nguyễn Khánh Toàn (Toàn), DTruong, Lê Nguyễn Phi Trường (Trường), Thi.

---

## 1. Summary Matrix

| Member | Main Role | Module Ownership | Core Files | Deliverable Artifact | Verification Command | Key Metric |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Toàn** (Nguyễn Khánh Toàn) | System Architect & Lead | Orchestration & Core Models | `main.py`<br>`core/config.py`<br>`core/models.py`<br>`core/trace.py`<br>`agents/coordinator_agent.py` | `architecture.md`<br>`metadata.json`<br>`trace.jsonl` | `python main.py --mode all` | 100% Trace completeness, Workflow latency < 100ms/case |
| **DTruong** | Data Extraction Lead | CSV Loading & Data Extraction Agents | `utils/csv_loader.py`<br>`utils/join_helper.py`<br>`agents/order_agent.py`<br>`agents/payment_agent.py`<br>`agents/delivery_agent.py` | `OrderContext`<br>`PaymentContext`<br>`DeliveryContext` models & extractor unit tests | `pytest tests/test_domain_agents.py` | 100% CSV Join accuracy, Extractor latency < 50ms |
| **Trường** (Lê Nguyễn Phi Trường) | Business Policy Lead | Policy Rules Engine & Evidence Bus | `agents/policy_agent.py`<br>`utils/evidence.py`<br>`utils/money.py`<br>`prompts/policy_prompts.py` | `PolicyDecision` engine & Evidence Builder unit tests | `pytest tests/test_policy_agent.py` | 100% EC_POLICY_V1 Rule accuracy, Refund calculation precision (0.10 BRL) |
| **Thi** | QA & Verification Lead | Verifier Agent & Output Packaging | `agents/verifier_agent.py`<br>`utils/validation.py`<br>`services/export_service.py`<br>`tests/test_verifier.py` | `50 Output JSONs in output/`<br>`output.zip`<br>Verifier Test Suite | `pytest tests/test_verifier.py` | 0 Hard gate failures across 50 cases, 100% JSON Schema compliance |

---

## 2. Detailed Member Breakdown

### Member 1: Toàn (Nguyễn Khánh Toàn - System Architect & Tech Lead)
- **Ownership**: Core domain schemas, system configuration, tracer engine, CLI entrypoint, Coordinator agent.
- **Files Owned**: `main.py`, `core/config.py`, `core/models.py`, `core/trace.py`, `core/logger.py`, `agents/coordinator_agent.py`, `agents/base_agent.py`.
- **Input**: `input/EC_*.json` case files.
- **Output**: Workflow orchestration context, `trace.jsonl`, `architecture.md`, `metadata.json`.
- **Dependency**: Uses output contexts from Domain Agents, Policy Agent, and Verifier Agent.
- **Verification Command**:
  ```bash
  python main.py --mode all
  ```
- **Technical Decision**: Used Pydantic V2 models for strict type contracts and async-ready tracer to prevent disk I/O bottlenecks during trace logging.
- **Blocker Handled**: Inconsistent timestamps across Olist orders handled by isolating ISO format parsing to string comparisons without timezone mutation.
- **Checklist**:
  - [x] Create Pydantic data schemas in `core/models.py`.
  - [x] Build `Tracer` class in `core/trace.py` for logging `trace.jsonl`.
  - [x] Construct `CoordinatorAgent` in `agents/coordinator_agent.py`.

---

### Member 2: DTruong (Data Extraction & Context Lead)
- **Ownership**: Olist dataset CSV loading, relational join helper, Order Agent, Payment Agent, Delivery Agent.
- **Files Owned**: `utils/csv_loader.py`, `utils/join_helper.py`, `agents/order_agent.py`, `agents/payment_agent.py`, `agents/delivery_agent.py`, `tests/test_domain_agents.py`, `tests/test_csv_loader.py`.
- **Input**: `claimed_order_id` from `CaseInput` and Olist CSV tables in `data/`.
- **Output**: `OrderContext`, `PaymentContext`, `DeliveryContext`.
- **Dependency**: Depends on `core/models.py` and `core/config.py`.
- **Verification Command**:
  ```bash
  pytest tests/test_domain_agents.py tests/test_csv_loader.py
  ```
- **Technical Decision**: Implemented in-memory LRU lazy caching for pandas DataFrames to prevent reloading 62MB CSV files on every case execution.
- **Blocker Handled**: Handled multi-item orders with multiple shipping limit dates by extracting the latest `shipping_limit_date` for seller handoff delay determination.
- **Checklist**:
  - [x] Create `OlistCSVLoader` in `utils/csv_loader.py`.
  - [x] Implement relational table joining in `utils/join_helper.py`.
  - [x] Build `OrderAgent`, `PaymentAgent`, and `DeliveryAgent`.

---

### Member 3: Trường (Lê Nguyễn Phi Trường - Policy & Rules Lead)
- **Ownership**: EC_POLICY_V1 Business Rules Engine, monetary calculations, evidence builder, system prompt templates.
- **Files Owned**: `agents/policy_agent.py`, `utils/money.py`, `utils/evidence.py`, `prompts/policy_prompts.py`, `tests/test_policy_agent.py`, `tests/test_evidence.py`.
- **Input**: `(OrderContext, PaymentContext, DeliveryContext)` tuple from Domain Agents.
- **Output**: `PolicyDecision` object containing `primary_issue`, `recommended_refund_brl`, `cause_code`, `responsible_party`, and `policy_evidence_id`.
- **Dependency**: Depends on domain contexts produced by DTruong.
- **Verification Command**:
  ```bash
  pytest tests/test_policy_agent.py tests/test_evidence.py
  ```
- **Technical Decision**: Built deterministic python rule evaluation before passing to local LLM prompts to guarantee 100% compliance on 6 dispute primary issues.
- **Blocker Handled**: Handled floating point rounding issues in Brazilian Real (BRL) using `Decimal(quantize)` with 0.10 BRL tolerance for split payments.
- **Checklist**:
  - [x] Implement exact rule priority tree in `PolicyAgent`.
  - [x] Build Decimal-based money utility in `utils/money.py`.
  - [x] Construct Evidence Builder in `utils/evidence.py`.

---

### Member 4: Thi (QA & Verifier Lead)
- **Ownership**: Verifier Agent, Output Validator, export packaging service, test suite, and golden case verification.
- **Files Owned**: `agents/verifier_agent.py`, `utils/validation.py`, `services/export_service.py`, `services/dispute_service.py`, `tests/test_verifier.py`, `tests/test_golden_cases.py`.
- **Input**: `(CaseInput, OrderContext, PaymentContext, PolicyDecision)` tuple.
- **Output**: Validated `FinalOutput` written to `output/EC_*.json` and packaged `output.zip`.
- **Dependency**: Depends on outputs from Coordinator and Policy Agent.
- **Verification Command**:
  ```bash
  pytest tests/test_verifier.py tests/test_golden_cases.py
  ```
- **Technical Decision**: Implemented fail-fast verification rules with explicit checks for entity set bounds ($\le 5$), evidence count ($\le 10$), and refund-status alignment.
- **Blocker Handled**: Handled missing item rows in canceled/unavailable orders by setting default empty lists for items/sellers and $0.0$ totals while preserving order ID.
- **Checklist**:
  - [x] Build `OutputValidator` in `utils/validation.py`.
  - [x] Implement `VerifierAgent` in `agents/verifier_agent.py`.
  - [x] Build `ExportService` in `services/export_service.py`.

---

## 3. Git Branch & Merge Strategy

### Branch Structure
- `main`: Production-ready branch. Only clean, tested code is merged here.
- `feature/coordinator-core`: Owned by **Toàn**
- `feature/domain-extractors`: Owned by **DTruong**
- `feature/policy-engine`: Owned by **Trường**
- `feature/verifier-qa`: Owned by **Thi**

### Commit Convention
```text
[<MODULE>] <type>: <short summary>

Examples:
[CORE] feat: implement Pydantic models for dispute context
[DOMAIN] feat: add OlistCSVLoader with DataFrame caching
[POLICY] fix: handle 0.10 BRL tolerance in split payment rule
[VERIFIER] test: add entity bounds validation unit tests
```

### Pull Request Checklist
1. All unit tests pass locally (`pytest tests/`).
2. No merge conflicts with `main`.
3. Code respects module boundaries (no CSV reading in PolicyAgent, no business rules in CoordinatorAgent).
4. No secret keys or `.env` files committed.
