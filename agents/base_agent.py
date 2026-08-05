"""
Abstract Base Agent Definition
Implements common logging, tracing, retry mechanisms, and contract enforcement.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from core.logger import get_logger
from core.trace import Tracer


class BaseAgent(ABC):
    def __init__(self, name: str, tracer: Optional[Tracer] = None):
        self.name = name
        self.logger = get_logger(name)
        self.tracer = tracer or Tracer()

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """Executes agent logic for domain processing."""
        pass

    def run_with_retry(self, input_data: Any, max_retries: int = 2) -> Any:
        """Standard wrapper with retry strategy and execution timing."""
        start_time = time.perf_counter()
        attempt = 0
        last_exception = None

        while attempt <= max_retries:
            try:
                attempt += 1
                self.logger.info(f"Executing {self.name} (Attempt {attempt})...")
                result = self.execute(input_data)
                latency_ms = (time.perf_counter() - start_time) * 1000

                self.tracer.record(
                    case_id=getattr(input_data, "case_id", getattr(input_data, "order_id", "UNKNOWN")),
                    agent=self.name,
                    input_summary={"attempt": attempt},
                    output_summary={"result_type": type(result).__name__},
                    latency_ms=latency_ms,
                    status="SUCCESS",
                    confidence=getattr(result, "confidence", 1.0)
                )
                return result
            except Exception as e:
                self.logger.warning(f"Error in {self.name} attempt {attempt}: {str(e)}")
                last_exception = e

        latency_ms = (time.perf_counter() - start_time) * 1000
        self.tracer.record(
            case_id=getattr(input_data, "case_id", "UNKNOWN"),
            agent=self.name,
            input_summary={"max_retries": max_retries},
            output_summary={"error": str(last_exception)},
            latency_ms=latency_ms,
            status="FAILED",
            confidence=0.0
        )
        raise last_exception
