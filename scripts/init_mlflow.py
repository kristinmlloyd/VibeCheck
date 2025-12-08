#!/usr/bin/env python3
"""
Initialize MLFlow tracking for VibeCheck.

This script sets up MLFlow experiments and validates the configuration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from vibecheck.mlflow_config import init_mlflow
from vibecheck.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Initialize MLFlow tracking."""
    logger.info("Initializing MLFlow for VibeCheck")

    try:
        # Initialize MLFlow with default settings
        init_mlflow()

        logger.info("MLFlow initialization complete!")
        logger.info("You can now start the MLFlow UI with:")
        logger.info("  mlflow ui --port 5000")
        logger.info("")
        logger.info("Or use docker-compose:")
        logger.info("  docker-compose -f docker-compose.mlflow.yml up -d")

    except Exception as e:
        logger.error(f"Failed to initialize MLFlow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
