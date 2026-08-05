"""
Data Contracts and Pydantic Models for Multi-Agent E-commerce Dispute Resolution
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class CustomerRequest(BaseModel):
    language: str
    message: str
    claimed_order_id: str


class CaseInput(BaseModel):
    case_id: str
    opened_at: str
    customer_request: CustomerRequest
    policy_version: str = "EC_POLICY_V1"


class OrderContext(BaseModel):
    order_id: str
    customer_id: str
    order_status: str
    purchase_timestamp: Optional[str] = None
    approved_at: Optional[str] = None
    delivered_carrier_date: Optional[str] = None
    delivered_customer_date: Optional[str] = None
    estimated_delivery_date: Optional[str] = None
    item_ids: List[str] = Field(default_factory=list)
    seller_ids: List[str] = Field(default_factory=list)
    shipping_limit_dates: List[str] = Field(default_factory=list)
    item_prices: List[float] = Field(default_factory=list)
    freight_values: List[float] = Field(default_factory=list)
    item_total_brl: float = 0.0
    freight_total_brl: float = 0.0
    is_seller_late: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class PaymentContext(BaseModel):
    order_id: str
    payment_ids: List[str] = Field(default_factory=list)
    payment_types: List[str] = Field(default_factory=list)
    payment_installments: List[int] = Field(default_factory=list)
    payment_values: List[float] = Field(default_factory=list)
    payment_total_brl: float = 0.0
    payment_count: int = 0
    is_split_payment: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class DeliveryContext(BaseModel):
    order_id: str
    delivered_carrier_date: Optional[str] = None
    delivered_customer_date: Optional[str] = None
    estimated_delivery_date: Optional[str] = None
    is_delivered_after_estimate: bool = False
    is_carrier_received_after_limit: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class PolicyDecision(BaseModel):
    primary_issue: str
    case_status: Literal["action_required", "no_action"]
    confidence: float
    cause_code: str
    responsible_party_type: Optional[str] = None
    responsible_party_id: Optional[str] = None
    recommended_refund_brl: float
    resolution_actions: List[str]
    policy_evidence_id: str


class VerificationCheckResult(BaseModel):
    check_name: str
    passed: bool
    details: str


class VerificationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks: List[VerificationCheckResult] = Field(default_factory=list)


class RankedCause(BaseModel):
    cause_code: str
    rank: int = 1


class ResponsibleParty(BaseModel):
    party_type: str
    party_id: str


class Assessment(BaseModel):
    primary_issue: str
    case_status: Literal["action_required", "no_action"]
    confidence: float


class AffectedEntities(BaseModel):
    order_ids: List[str]
    item_ids: List[str]
    seller_ids: List[str]
    payment_ids: List[str]


class RootCauseAnalysis(BaseModel):
    ranked_causes: List[RankedCause]
    responsible_parties: List[ResponsibleParty]


class FinancialResolution(BaseModel):
    currency: str = "BRL"
    item_total_brl: float
    freight_total_brl: float
    payment_total_brl: float
    recommended_refund_brl: float


class FinalOutput(BaseModel):
    case_id: str
    assessment: Assessment
    affected_entities: AffectedEntities
    root_cause_analysis: RootCauseAnalysis
    evidence_ids: List[str]
    financial_resolution: FinancialResolution
    resolution_actions: List[str]


class TraceRecord(BaseModel):
    timestamp: str
    case_id: str
    agent: str
    input_summary: Dict[str, Any]
    output_summary: Dict[str, Any]
    latency_ms: float
    status: Literal["SUCCESS", "FAILED", "RETRY"]
    confidence: float
    handoff_to: Optional[str] = None
