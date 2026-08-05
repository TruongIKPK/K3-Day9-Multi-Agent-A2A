"""Unit tests for Verifier Agent and OutputValidator"""

import zipfile

from agents.verifier_agent import VerifierAgent
from core.models import (
    CaseInput,
    CustomerRequest,
    FinalOutput,
    OrderContext,
    PaymentContext,
    PolicyDecision,
)
from services.dispute_service import DisputeService
from utils.validation import OutputValidator


def _build_valid_case_input(case_id: str = "EC_001") -> CaseInput:
    return CaseInput(
        case_id=case_id,
        opened_at="2023-01-01T00:00:00Z",
        customer_request=CustomerRequest(
            language="pt",
            message="pedido entregue com problema",
            claimed_order_id="ord_1",
        ),
    )


def _build_valid_verifier_input(case_id: str = "EC_001"):
    case_input = _build_valid_case_input(case_id)
    order_ctx = OrderContext(
        order_id="ord_1",
        customer_id="cus_1",
        order_status="canceled",
        item_ids=["ord_1:1"],
        seller_ids=["seller_1"],
        item_total_brl=100.0,
        freight_total_brl=15.0,
        evidence_ids=["order:ord_1"],
    )
    payment_ctx = PaymentContext(
        order_id="ord_1",
        payment_ids=["pay_1"],
        payment_values=[115.0],
        payment_total_brl=115.0,
        payment_count=1,
        evidence_ids=["payment:pay_1"],
    )
    policy_decision = PolicyDecision(
        primary_issue="canceled_order_paid",
        case_status="action_required",
        confidence=0.95,
        cause_code="ORDER_CANCELED_AFTER_PAYMENT",
        responsible_party_type="platform",
        responsible_party_id="platform",
        recommended_refund_brl=115.0,
        resolution_actions=["issue_full_refund"],
        policy_evidence_id="policy:ec_policy_v1:EC_001",
    )
    return case_input, order_ctx, payment_ctx, policy_decision


def test_output_validator_bounds():
    final_output = VerifierAgent().execute(_build_valid_verifier_input())
    v_res = OutputValidator.validate(final_output)
    assert v_res.is_valid is True


def test_process_all_cases_packages_output_zip(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    case_file = input_dir / "EC_001.json"
    case_file.write_text(
        """{
  "case_id": "EC_001",
  "opened_at": "2023-01-01T00:00:00Z",
  "customer_request": {
    "language": "pt",
    "message": "pedido entregue com problema",
    "claimed_order_id": "ord_1"
  }
}""",
        encoding="utf-8",
    )

    service = DisputeService(input_dir=input_dir, output_dir=output_dir)

    def fake_run_with_retry(case_input):
        _, order_ctx, payment_ctx, policy_decision = _build_valid_verifier_input(case_input.case_id)
        return VerifierAgent().execute((case_input, order_ctx, payment_ctx, policy_decision))

    service.coordinator.run_with_retry = fake_run_with_retry

    results = service.process_all_cases()

    assert len(results) == 1
    assert (output_dir / "EC_001.json").exists()

    zip_path = tmp_path / "output.zip"
    assert zip_path.exists()

    with zipfile.ZipFile(zip_path, "r") as archive:
        assert archive.namelist() == ["EC_001.json"]
