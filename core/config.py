"""
Global Configuration for Multi-Agent E-commerce Dispute Resolution
System constants, paths, and business thresholds.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data"
INPUT_PATH = BASE_DIR / "input"
OUTPUT_PATH = BASE_DIR / "output"
TRACE_FILE_PATH = BASE_DIR / "trace.jsonl"
METADATA_FILE_PATH = BASE_DIR / "metadata.json"
ENV_FILE_PATH = BASE_DIR / ".env"

# Load .env if present
if ENV_FILE_PATH.exists():
    with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Environment Variables
APP_ENV = os.getenv("APP_ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "offline_rules")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Rules-Engine-Local-Orchestrator")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Business & Processing Constants
CONFIDENCE_DEFAULT = 0.95
REFUND_ROUND_DIGITS = 2
POLICY_VERSION = "EC_POLICY_V1"
SPLIT_PAYMENT_TOLERANCE_BRL = 0.10

# Validation Bounds
MAX_ENTITIES_PER_SET = 5
MAX_EVIDENCE_IDS = 10
MAX_ROOT_CAUSES = 3
MAX_RESPONSIBLE_PARTIES = 3
MAX_RESOLUTION_ACTIONS = 5

# Root Cause Codes
RC_SELLER_HANDOFF_AFTER_LIMIT = "SELLER_HANDOFF_AFTER_LIMIT"
RC_CARRIER_DELIVERED_AFTER_ESTIMATE = "CARRIER_DELIVERED_AFTER_ESTIMATE"
RC_ORDER_CANCELED_AFTER_PAYMENT = "ORDER_CANCELED_AFTER_PAYMENT"
RC_ORDER_UNAVAILABLE_AFTER_PAYMENT = "ORDER_UNAVAILABLE_AFTER_PAYMENT"
RC_MULTIPLE_PAYMENTS_RECONCILED = "MULTIPLE_PAYMENTS_RECONCILED"
RC_DELIVERY_WITHIN_ESTIMATE = "DELIVERY_WITHIN_ESTIMATE"

# Primary Issues
ISSUE_CANCELED_ORDER_PAID = "canceled_order_paid"
ISSUE_UNAVAILABLE_ORDER_PAID = "unavailable_order_paid"
ISSUE_LATE_DELIVERY_SELLER = "late_delivery_seller"
ISSUE_LATE_DELIVERY_LOGISTICS = "late_delivery_logistics"
ISSUE_VALID_SPLIT_PAYMENT = "valid_split_payment"
ISSUE_UNSUPPORTED_LATE_CLAIM = "unsupported_late_claim"

# Responsible Party Types
PARTY_PLATFORM = "platform"
PARTY_SELLER = "seller"
PARTY_LOGISTICS = "logistics_provider"
