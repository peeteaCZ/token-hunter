"""
Entry-point script.
Usage:
    python scripts/run_pipeline.py
    # or, from project root:
    uv run scripts/run_pipeline.py
"""

from __future__ import annotations

import sys
import os

# Allow imports from the project root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import configure_logging, get_logger
from core.pipeline import Pipeline
from ingestion.file_sources import build_default_sources
from storage.evidence import EvidenceStorage

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    logger.info("token_hunter starting")

    sources = build_default_sources()

    pipeline = Pipeline(
        sources=sources,
        evidence_storage=EvidenceStorage("data/evidence.jsonl"),
    )
    stats = pipeline.run()

    logger.info("done  stats=%s", stats)


if __name__ == "__main__":
    main()
