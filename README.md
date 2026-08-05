# Multi-Agent E-commerce Dispute Resolution (Olist Dataset)

System design and implementation for automated dispute resolution across 50 customer support cases on Olist Brazilian E-Commerce dataset using Clean Architecture and Multi-Agent principles.

---

## 1. System Overview & Architecture

The architecture decouples data ingestion, domain extraction, business policy evaluation, and output verification across 6 specialized agents:

- **Coordinator Agent**: Receives cases and manages sequential domain handoffs.
- **Order Agent**: Queries `olist_orders_dataset.csv` and `olist_order_items_dataset.csv`.
- **Payment Agent**: Queries `olist_order_payments_dataset.csv` and calculates total payments.
- **Delivery Agent**: Evaluates delivery vs estimated dates and seller handoff limits.
- **Policy Agent**: Evaluates `EC_POLICY_V1` rules and determines refunds and actions.
- **Verifier Agent**: Validates schema constraints, entity bounds, evidence syntax, and writes output files.

---

## 2. Installation & Setup

### Prerequisites
- Python 3.9+
- Virtual environment (recommended)

### Installation
```bash
# Clone the workspace
git clone https://github.com/TruongIKPK/K3-Day9-Multi-Agent-A2A.git
cd K3-Day9-Multi-Agent-A2A

# Install required packages
pip install pandas pydantic pytest
```

---

## 3. Running the Pipeline

### Batch Process All 50 Cases & Auto-Zip
```bash
python main.py --mode all
```

### Process Single Case for Debugging
```bash
python main.py --mode single --case_id EC_001
```

### Repackage Output Folder to ZIP
```bash
python main.py --mode zip
```

---

## 4. Running Verification Tests

```bash
# Run unit and schema verification tests
pytest tests/
```

---

## 5. Directory Structure

```text
.
├── agents/
│   ├── base_agent.py
│   ├── coordinator_agent.py
│   ├── delivery_agent.py
│   ├── order_agent.py
│   ├── payment_agent.py
│   ├── policy_agent.py
│   └── verifier_agent.py
├── core/
│   ├── config.py
│   ├── logger.py
│   ├── models.py
│   └── trace.py
├── data/                    # 9 Olist CSV dataset files
├── input/                   # EC_001.json -> EC_050.json
├── output/                  # Generated JSON outputs
├── prompts/                 # System prompt templates
├── services/
│   ├── dispute_service.py
│   └── export_service.py
├── tests/                   # Pytest suite
├── utils/
│   ├── csv_loader.py
│   ├── evidence.py
│   ├── join_helper.py
│   ├── money.py
│   └── validation.py
├── architecture.md          # Multi-agent architecture specification
├── main.py                  # CLI entrypoint
├── metadata.json            # Model and system execution metadata
├── trace.jsonl              # Runtime trace execution log
└── README.md
```
