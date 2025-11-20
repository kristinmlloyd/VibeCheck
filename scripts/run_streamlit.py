"""Run the VibeCheck Streamlit app with proper environment settings."""

import os
import subprocess
import sys


def main():
    """Run Streamlit app with environment variables set."""
    # Set environment variables to avoid segfault on Mac
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"

    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"])


if __name__ == "__main__":
    main()
