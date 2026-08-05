"""
Validation Utility for Verifier Agent
Validates schemas, financial totals, bounds, and evidence IDs.
"""

from typing import List, Dict, Any
from core.config import (
    MAX_ENTITIES_PER_SET,
    MAX_EVIDENCE_IDS,
    MAX_ROOT_CAUSES,
    MAX_RESPONSIBLE_PARTIES,
    MAX_RESOLUTION_ACTIONS
)
from core.models import FinalOutput, VerificationResult, VerificationCheckResult


class OutputValidator:
    @staticmethod
    def validate(output: FinalOutput) -> VerificationResult:
        errors: List[str] = []
        warnings: List[str] = []
        checks: List[VerificationCheckResult] = []

        # 1. Bounds Validation
        entities = output.affected_entities
        b_order = len(entities.order_ids) <= MAX_ENTITIES_PER_SET
        b_item = len(entities.item_ids) <= MAX_ENTITIES_PER_SET
        b_seller = len(entities.seller_ids) <= MAX_ENTITIES_PER_SET
        b_payment = len(entities.payment_ids) <= MAX_ENTITIES_PER_SET
        b_ev = len(output.evidence_ids) <= MAX_EVIDENCE_IDS
        b_rc = len(output.root_cause_analysis.ranked_causes) <= MAX_ROOT_CAUSES
        b_rp = len(output.root_cause_analysis.responsible_parties) <= MAX_RESPONSIBLE_PARTIES
        b_act = len(output.resolution_actions) <= MAX_RESOLUTION_ACTIONS

        bounds_passed = all([b_order, b_item, b_seller, b_payment, b_ev, b_rc, b_rp, b_act])
        if not bounds_passed:
            errors.append("Entity or Evidence count exceeded maximum threshold bounds.")
        checks.append(VerificationCheckResult(
            check_name="entity_bounds",
            passed=bounds_passed,
            details=f"orders={len(entities.order_ids)}, evidence={len(output.evidence_ids)}"
        ))

        # 2. Confidence Validation [0.0, 1.0]
        conf_passed = 0.0 <= output.assessment.confidence <= 1.0
        if not conf_passed:
            errors.append(f"Confidence score {output.assessment.confidence} out of range [0.0, 1.0].")
        checks.append(VerificationCheckResult(
            check_name="confidence_range",
            passed=conf_passed,
            details=f"confidence={output.assessment.confidence}"
        ))

        # 3. Evidence ID Syntax Validation
        valid_prefixes = ("order:", "item:", "payment:", "seller:", "policy:")
        invalid_evidence = [e for e in output.evidence_ids if not e.startswith(valid_prefixes)]
        ev_syntax_passed = len(invalid_evidence) == 0
        if not ev_syntax_passed:
            errors.append(f"Invalid evidence IDs found: {invalid_evidence}")
        checks.append(VerificationCheckResult(
            check_name="evidence_syntax",
            passed=ev_syntax_passed,
            details=f"invalid_count={len(invalid_evidence)}"
        ))

        # 4. Financial Status Consistency
        fin = output.financial_resolution
        if output.assessment.case_status == "no_action":
            status_fin_passed = (fin.recommended_refund_brl == 0.0)
            if not status_fin_passed:
                errors.append("case_status is no_action but recommended_refund_brl > 0.0")
        else:
            status_fin_passed = (fin.recommended_refund_brl >= 0.0)
        checks.append(VerificationCheckResult(
            check_name="financial_status_consistency",
            passed=status_fin_passed,
            details=f"refund={fin.recommended_refund_brl}, status={output.assessment.case_status}"
        ))

        is_valid = len(errors) == 0
        return VerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            checks=checks
        )
