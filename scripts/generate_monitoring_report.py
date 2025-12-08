#!/usr/bin/env python3
"""
Generate Evidently monitoring report for VibeCheck.

This script generates data quality and drift reports for embeddings and recommendations.
"""

import sys
from pathlib import Path

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from vibecheck.monitoring import EvidentlyMonitor, create_sample_recommendations_data
from vibecheck.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Generate monitoring reports."""
    logger.info("Generating Evidently monitoring reports")

    # Initialize monitor
    monitor = EvidentlyMonitor()

    # Check if embeddings exist
    embeddings_path = Path("data/embeddings/vibe_embeddings.npy")
    meta_ids_path = Path("data/restaurants_info/meta_ids.npy")

    if not embeddings_path.exists():
        logger.warning(f"Embeddings not found at {embeddings_path}")
        logger.info("Please run embedding generation first:")
        logger.info("  python scripts/generate_embeddings.py")
        sys.exit(1)

    if not meta_ids_path.exists():
        logger.warning(f"Meta IDs not found at {meta_ids_path}")
        logger.info("Please run embedding generation first:")
        logger.info("  python scripts/generate_embeddings.py")
        sys.exit(1)

    try:
        # Load embeddings
        logger.info("Loading embeddings...")
        embeddings = np.load(embeddings_path)
        meta_ids = np.load(meta_ids_path, allow_pickle=True)

        logger.info(f"Loaded {len(embeddings)} embeddings")

        # Create sample recommendations data for monitoring
        # In production, this would come from actual recommendation logs
        logger.info("Creating sample recommendations data...")
        sample_recs = create_sample_recommendations_data(
            query_ids=['query_1'] * min(10, len(meta_ids)),
            restaurant_ids=meta_ids[:min(10, len(meta_ids))].tolist(),
            similarity_scores=np.random.uniform(0.5, 1.0, min(10, len(meta_ids))).tolist(),
        )

        # Generate dashboard
        logger.info("Generating monitoring dashboard...")
        dashboard_paths = monitor.generate_monitoring_dashboard(
            embeddings=embeddings,
            ids=meta_ids.tolist(),
            recommendations=sample_recs,
        )

        logger.info("Monitoring reports generated successfully!")
        logger.info("\nGenerated reports:")
        for report_type, path in dashboard_paths.items():
            logger.info(f"  {report_type}: {path}")

        logger.info("\nOpen these HTML files in your browser to view the reports.")

    except Exception as e:
        logger.error(f"Failed to generate monitoring reports: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
