"""
Coordinator Agent
Orchestrates multi-agent domain extraction, policy evaluation, and output verification.
Does NOT execute business rules or direct data querying.
"""

from agents.base_agent import BaseAgent
from agents.order_agent import OrderAgent
from agents.payment_agent import PaymentAgent
from agents.delivery_agent import DeliveryAgent
from agents.policy_agent import PolicyAgent
from agents.verifier_agent import VerifierAgent
from core.models import CaseInput, FinalOutput
from utils.csv_loader import OlistCSVLoader


class CoordinatorAgent(BaseAgent):
    def __init__(self, loader: OlistCSVLoader, tracer=None):
        super().__init__("CoordinatorAgent", tracer=tracer)
        self.order_agent = OrderAgent(loader, tracer=tracer)
        self.payment_agent = PaymentAgent(loader, tracer=tracer)
        self.delivery_agent = DeliveryAgent(tracer=tracer)
        self.policy_agent = PolicyAgent(tracer=tracer)
        self.verifier_agent = VerifierAgent(tracer=tracer)

    def execute(self, case_input: CaseInput) -> FinalOutput:
        self.logger.info(f"Coordinator processing Case ID: {case_input.case_id}")

        # Step 1: Extract domain contexts in parallel/sequence
        order_ctx = self.order_agent.run_with_retry(case_input)
        payment_ctx = self.payment_agent.run_with_retry(case_input)

        # Step 2: Extract delivery context using order context
        delivery_ctx = self.delivery_agent.run_with_retry(order_ctx)

        # Step 3: Evaluate policy decision
        policy_decision = self.policy_agent.run_with_retry((order_ctx, payment_ctx, delivery_ctx))

        # Step 4: Verify and assemble output
        final_output = self.verifier_agent.run_with_retry((case_input, order_ctx, payment_ctx, policy_decision))

        return final_output
