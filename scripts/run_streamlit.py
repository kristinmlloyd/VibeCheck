"""Run the VibeCheck Streamlit app with proper environment settings."""

import logging
import os
import subprocess
import sys

# Set up basic logging for the script itself
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run Streamlit app with environment variables set."""
    logger.info("🚀 Starting VibeCheck application...")

    # Set environment variables to avoid segfault on Mac
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"

    logger.info("Environment variables set for Mac compatibility")
    logger.info("Running Streamlit app...")

    # Run streamlit
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"]
    )

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
