"""
Export and Packaging Utility
Zips 50 output JSON files into output.zip for submission.
"""

import zipfile
from pathlib import Path
from core.config import OUTPUT_PATH, BASE_DIR
from core.logger import get_logger

logger = get_logger("ExportService")


def package_output_zip(output_dir: Path = OUTPUT_PATH, zip_path: Path = BASE_DIR / "output.zip") -> Path:
    json_files = sorted(list(output_dir.glob("EC_*.json")))
    if len(json_files) != 50:
        logger.warning(f"Expected 50 files in output, found {len(json_files)}.")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in json_files:
            zipf.write(file, arcname=file.name)

    logger.info(f"Successfully packaged {len(json_files)} JSON files into {zip_path}")
    return zip_path
