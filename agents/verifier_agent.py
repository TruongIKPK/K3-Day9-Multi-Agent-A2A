"""
Verifier Agent
Assembles FinalOutput schema, runs strict OutputValidator checks, and logs warnings/errors.
"""

from typing import Tuple
from agents.base_agent import BaseAgent
from core.models import (
    CaseInput, OrderContext, PaymentContext, PolicyDecision,
    FinalOutput, Assessment, AffectedEntities, RootCauseAnalysis,
    RankedCause, ResponsibleParty, FinancialResolution
)
from utils.validation import OutputValidator
from utils.evidence import EvidenceBuilder


class VerifierAgent(BaseAgent):
    def __init__(self, tracer=None):
        super().__init__("VerifierAgent", tracer=tracer)

    def execute(self, inputs: Tuple[CaseInput, OrderContext, PaymentContext, PolicyDecision]) -> FinalOutput:
        case_input, order_ctx, payment_ctx, policy_decision = inputs

        # Build evidence list combining domain evidence and policy evidence
        all_evidence = []
        all_evidence.extend(order_ctx.evidence_ids)
        all_evidence.extend(payment_ctx.evidence_ids)
        all_evidence.append(policy_decision.policy_evidence_id)
        sanitized_evidence = EvidenceBuilder.sanitize_evidence_list(all_evidence, max_limit=10)

        # Build Responsible Parties list
        responsible_parties = []
        if policy_decision.responsible_party_type and policy_decision.responsible_party_id:
            responsible_parties.append(
                ResponsibleParty(
                    party_type=policy_decision.responsible_party_type,
                    party_id=policy_decision.responsible_party_id
                )
            )

        final_output = FinalOutput(
            case_id=case_input.case_id,
            assessment=Assessment(
                primary_issue=policy_decision.primary_issue,
                case_status=policy_decision.case_status,
                confidence=policy_decision.confidence
            ),
            affected_entities=AffectedEntities(
                order_ids=[order_ctx.order_id] if order_ctx.order_id else [],
                item_ids=order_ctx.item_ids[:5],
                seller_ids=order_ctx.seller_ids[:5],
                payment_ids=payment_ctx.payment_ids[:5]
            ),
            root_cause_analysis=RootCauseAnalysis(
                ranked_causes=[RankedCause(cause_code=policy_decision.cause_code, rank=1)],
                responsible_parties=responsible_parties[:3]
            ),
            evidence_ids=sanitized_evidence,
            financial_resolution=FinancialResolution(
                currency="BRL",
                item_total_brl=order_ctx.item_total_brl,
                freight_total_brl=order_ctx.freight_total_brl,
                payment_total_brl=payment_ctx.payment_total_brl,
                recommended_refund_brl=policy_decision.recommended_refund_brl
            ),
            resolution_actions=policy_decision.resolution_actions[:5]
        )

        # Run Verification
        v_result = OutputValidator.validate(final_output)
        if not v_result.is_valid:
            self.logger.error(f"Verification FAILED for case {case_input.case_id}: {v_result.errors}")
            raise ValueError(f"Verifier rejected output schema for case {case_input.case_id}: {v_result.errors}")

        self.logger.info(f"Verification PASSED for case {case_input.case_id}.")
        return final_output
