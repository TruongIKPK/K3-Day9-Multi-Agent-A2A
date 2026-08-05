"""
Policy Agent
Evaluates business rules against collected contexts (Order, Payment, Delivery).
Does NOT read CSV files directly.
"""

from typing import Tuple
from agents.base_agent import BaseAgent
from core.config import (
    CONFIDENCE_DEFAULT,
    RC_SELLER_HANDOFF_AFTER_LIMIT,
    RC_CARRIER_DELIVERED_AFTER_ESTIMATE,
    RC_ORDER_CANCELED_AFTER_PAYMENT,
    RC_ORDER_UNAVAILABLE_AFTER_PAYMENT,
    RC_MULTIPLE_PAYMENTS_RECONCILED,
    RC_DELIVERY_WITHIN_ESTIMATE,
    ISSUE_CANCELED_ORDER_PAID,
    ISSUE_UNAVAILABLE_ORDER_PAID,
    ISSUE_LATE_DELIVERY_SELLER,
    ISSUE_LATE_DELIVERY_LOGISTICS,
    ISSUE_VALID_SPLIT_PAYMENT,
    ISSUE_UNSUPPORTED_LATE_CLAIM,
    PARTY_PLATFORM,
    PARTY_SELLER,
    PARTY_LOGISTICS
)
from core.models import OrderContext, PaymentContext, DeliveryContext, PolicyDecision
from utils.money import is_within_split_tolerance, format_brl
from utils.evidence import EvidenceBuilder


class PolicyAgent(BaseAgent):
    def __init__(self, tracer=None):
        super().__init__("PolicyAgent", tracer=tracer)

    def execute(self, inputs: Tuple[OrderContext, PaymentContext, DeliveryContext]) -> PolicyDecision:
        order_ctx, payment_ctx, delivery_ctx = inputs

        order_status = order_ctx.order_status.lower()
        payment_total = payment_ctx.payment_total_brl
        item_total = order_ctx.item_total_brl
        freight_total = order_ctx.freight_total_brl

        # Rule 1: Canceled Order Paid
        if order_status == "canceled" and payment_total > 0:
            cause = RC_ORDER_CANCELED_AFTER_PAYMENT
            return PolicyDecision(
                primary_issue=ISSUE_CANCELED_ORDER_PAID,
                case_status="action_required",
                confidence=CONFIDENCE_DEFAULT,
                cause_code=cause,
                responsible_party_type=PARTY_PLATFORM,
                responsible_party_id="OLIST_PLATFORM",
                recommended_refund_brl=format_brl(payment_total),
                resolution_actions=["issue_full_refund"],
                policy_evidence_id=EvidenceBuilder.build_policy_evidence(cause)
            )

        # Rule 2: Unavailable Order Paid
        if order_status == "unavailable" and payment_total > 0:
            cause = RC_ORDER_UNAVAILABLE_AFTER_PAYMENT
            return PolicyDecision(
                primary_issue=ISSUE_UNAVAILABLE_ORDER_PAID,
                case_status="action_required",
                confidence=CONFIDENCE_DEFAULT,
                cause_code=cause,
                responsible_party_type=PARTY_PLATFORM,
                responsible_party_id="OLIST_PLATFORM",
                recommended_refund_brl=format_brl(payment_total),
                resolution_actions=["issue_full_refund"],
                policy_evidence_id=EvidenceBuilder.build_policy_evidence(cause)
            )

        # Rule 3 & 4: Late Delivery Rules
        if delivery_ctx.is_delivered_after_estimate:
            if delivery_ctx.is_carrier_received_after_limit:
                cause = RC_SELLER_HANDOFF_AFTER_LIMIT
                seller_id = order_ctx.seller_ids[0] if order_ctx.seller_ids else "UNKNOWN_SELLER"
                return PolicyDecision(
                    primary_issue=ISSUE_LATE_DELIVERY_SELLER,
                    case_status="action_required",
                    confidence=CONFIDENCE_DEFAULT,
                    cause_code=cause,
                    responsible_party_type=PARTY_SELLER,
                    responsible_party_id=seller_id,
                    recommended_refund_brl=format_brl(freight_total),
                    resolution_actions=["refund_freight"],
                    policy_evidence_id=EvidenceBuilder.build_policy_evidence(cause)
                )
            else:
                cause = RC_CARRIER_DELIVERED_AFTER_ESTIMATE
                return PolicyDecision(
                    primary_issue=ISSUE_LATE_DELIVERY_LOGISTICS,
                    case_status="action_required",
                    confidence=CONFIDENCE_DEFAULT,
                    cause_code=cause,
                    responsible_party_type=PARTY_LOGISTICS,
                    responsible_party_id="LOGISTICS_PROVIDER",
                    recommended_refund_brl=format_brl(freight_total),
                    resolution_actions=["refund_freight"],
                    policy_evidence_id=EvidenceBuilder.build_policy_evidence(cause)
                )

        # Rule 5: Valid Split Payment
        if payment_ctx.is_split_payment and is_within_split_tolerance(payment_total, item_total, freight_total):
            cause = RC_MULTIPLE_PAYMENTS_RECONCILED
            return PolicyDecision(
                primary_issue=ISSUE_VALID_SPLIT_PAYMENT,
                case_status="no_action",
                confidence=CONFIDENCE_DEFAULT,
                cause_code=cause,
                responsible_party_type=None,
                responsible_party_id=None,
                recommended_refund_brl=0.0,
                resolution_actions=["explain_valid_split_payment"],
                policy_evidence_id=EvidenceBuilder.build_policy_evidence(cause)
            )

        # Rule 6: Unsupported Late Claim (Default fallback if delivered within estimate)
        cause = RC_DELIVERY_WITHIN_ESTIMATE
        return PolicyDecision(
            primary_issue=ISSUE_UNSUPPORTED_LATE_CLAIM,
            case_status="no_action",
            confidence=CONFIDENCE_DEFAULT,
            cause_code=cause,
            responsible_party_type=None,
            responsible_party_id=None,
            recommended_refund_brl=0.0,
            resolution_actions=["reject_late_refund"],
            policy_evidence_id=EvidenceBuilder.build_policy_evidence(cause)
        )
