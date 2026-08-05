"""Unit tests for domain extraction agents"""

import pytest
from core.models import CaseInput, CustomerRequest
from utils.csv_loader import OlistCSVLoader
from agents.order_agent import OrderAgent
from agents.payment_agent import PaymentAgent


def test_order_agent_execution():
    loader = OlistCSVLoader()
    agent = OrderAgent(loader)
    case_in = CaseInput(
        case_id="EC_001",
        opened_at="2018-10-18T00:00:00-03:00",
        customer_request=CustomerRequest(
            language="vi",
            message="Test message",
            claimed_order_id="e4884d2591e08afc61642611170b1b38"
        )
    )
    res = agent.run_with_retry(case_in)
    assert res.order_id == "e4884d2591e08afc61642611170b1b38"
    assert len(res.evidence_ids) > 0
