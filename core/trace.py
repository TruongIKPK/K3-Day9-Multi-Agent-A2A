"""
Tracer Service for Multi-Agent E-commerce Dispute Resolution
Gathers and appends structured execution logs to trace.jsonl
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.config import TRACE_FILE_PATH
from core.models import TraceRecord


class Tracer:
    def __init__(self, trace_file_path=TRACE_FILE_PATH):
        self.trace_file_path = trace_file_path

    def clear(self):
        """Clears the trace file for fresh runs."""
        if self.trace_file_path.exists():
            self.trace_file_path.unlink()

    def record(
        self,
        case_id: str,
        agent: str,
        input_summary: Dict[str, Any],
        output_summary: Dict[str, Any],
        latency_ms: float,
        status: str = "SUCCESS",
        confidence: float = 1.0,
        handoff_to: Optional[str] = None
    ) -> TraceRecord:
        record = TraceRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            case_id=case_id,
            agent=agent,
            input_summary=input_summary,
            output_summary=output_summary,
            latency_ms=round(latency_ms, 2),
            status=status,
            confidence=confidence,
            handoff_to=handoff_to
        )
        with open(self.trace_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.model_dump(), ensure_ascii=False) + "\n")
        return record
