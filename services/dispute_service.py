"""
Dispute Processing Pipeline Service
"""

import json
from pathlib import Path
from typing import List
from core.config import INPUT_PATH, OUTPUT_PATH
from core.models import CaseInput, FinalOutput
from core.trace import Tracer
from core.logger import get_logger
from agents.coordinator_agent import CoordinatorAgent
from utils.csv_loader import OlistCSVLoader

logger = get_logger("DisputeService")


class DisputeService:
    def __init__(self, input_dir: Path = INPUT_PATH, output_dir: Path = OUTPUT_PATH):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tracer = Tracer()
        self.loader = OlistCSVLoader()
        self.coordinator = CoordinatorAgent(self.loader, tracer=self.tracer)

    def process_case_file(self, file_path: Path) -> FinalOutput:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        case_input = CaseInput(**data)
        final_output = self.coordinator.run_with_retry(case_input)

        out_path = self.output_dir / f"{case_input.case_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_output.model_dump(), f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully saved output for {case_input.case_id} -> {out_path}")
        return final_output

    def process_all_cases(self) -> List[FinalOutput]:
        self.tracer.clear()
        json_files = sorted(list(self.input_dir.glob("EC_*.json")))
        results = []
        for file_path in json_files:
            try:
                res = self.process_case_file(file_path)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed processing case file {file_path.name}: {str(e)}")
        return results
