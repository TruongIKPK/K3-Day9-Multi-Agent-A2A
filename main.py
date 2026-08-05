"""
Main CLI Entrypoint for Multi-Agent E-commerce Dispute Resolution
"""

import sys
import argparse
from services.dispute_service import DisputeService
from services.export_service import package_output_zip
from core.logger import get_logger

logger = get_logger("Main")


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent E-commerce Dispute Resolution CLI")
    parser.add_argument("--mode", choices=["all", "single", "zip"], default="all", help="Mode of execution")
    parser.add_argument("--case_id", type=str, help="Case ID for single mode (e.g., EC_001)")
    args = parser.parse_args()

    service = DisputeService()

    if args.mode == "all":
        logger.info("Executing batch dispute processing for all cases...")
        results = service.process_all_cases()
        logger.info(f"Processed {len(results)} cases successfully.")
        package_output_zip()
    elif args.mode == "single":
        if not args.case_id:
            logger.error("--case_id is required when mode is single.")
            sys.exit(1)
        file_path = service.input_dir / f"{args.case_id}.json"
        if not file_path.exists():
            logger.error(f"Input file not found: {file_path}")
            sys.exit(1)
        service.process_case_file(file_path)
    elif args.mode == "zip":
        package_output_zip()


if __name__ == "__main__":
    main()
