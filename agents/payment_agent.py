"""
Payment Agent
Responsible for analyzing order payment rows and checking payment values.
Does NOT decide refund eligibility.
"""

from agents.base_agent import BaseAgent
from core.models import CaseInput, PaymentContext
from utils.csv_loader import OlistCSVLoader
from utils.join_helper import OlistJoinHelper
from utils.evidence import EvidenceBuilder


class PaymentAgent(BaseAgent):
    def __init__(self, loader: OlistCSVLoader, tracer=None):
        super().__init__("PaymentAgent", tracer=tracer)
        self.join_helper = OlistJoinHelper(loader)

    def execute(self, case_input: CaseInput) -> PaymentContext:
        order_id = case_input.customer_request.claimed_order_id
        details = self.join_helper.fetch_order_details(order_id)
        payments = details["payments"]

        payment_ids = []
        types = []
        installments = []
        values = []
        total_payment = 0.0
        evidence_ids = []

        for p in payments:
            seq = p["payment_sequential"]
            pval = float(p["payment_value"])

            pid = f"{order_id}:{seq}"
            payment_ids.append(pid)
            types.append(p["payment_type"])
            installments.append(int(p["payment_installments"]))
            values.append(pval)
            total_payment += pval

            evidence_ids.append(EvidenceBuilder.build_payment_evidence(order_id, seq))

        return PaymentContext(
            order_id=order_id,
            payment_ids=payment_ids,
            payment_types=types,
            payment_installments=installments,
            payment_values=values,
            payment_total_brl=round(total_payment, 2),
            payment_count=len(payments),
            is_split_payment=(len(payments) > 1),
            evidence_ids=EvidenceBuilder.sanitize_evidence_list(evidence_ids)
        )
