"""
Evidently monitoring for VibeCheck recommendation system.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report
from evidently.test_preset import DataDriftTestPreset, DataQualityTestPreset
from evidently.test_suite import TestSuite

from vibecheck.logging_config import get_logger

logger = get_logger(__name__)


class EvidentlyMonitor:
    """
    Monitor recommendation system performance using Evidently.

    Tracks:
    - Embedding distribution drift
    - Recommendation quality metrics
    - Data quality issues
    - Performance over time
    """

    def __init__(
        self,
        reports_dir: Path = Path("monitoring/reports"),
        tests_dir: Path = Path("monitoring/tests"),
    ):
        """Initialize Evidently monitor."""
        self.reports_dir = Path(reports_dir)
        self.tests_dir = Path(tests_dir)

        # Create directories
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Evidently monitor initialized")
        logger.info(f"Reports directory: {self.reports_dir}")
        logger.info(f"Tests directory: {self.tests_dir}")

    def create_embedding_drift_report(
        self,
        reference_embeddings: np.ndarray,
        current_embeddings: np.ndarray,
        reference_ids: list[str],
        current_ids: list[str],
        report_name: str | None = None,
    ) -> str:
        """
        Create a data drift report for embeddings.

        Args:
            reference_embeddings: Reference (baseline) embeddings
            current_embeddings: Current embeddings to compare
            reference_ids: IDs for reference embeddings
            current_ids: IDs for current embeddings
            report_name: Optional custom report name

        Returns:
            Path to the generated report
        """
        logger.info("Creating embedding drift report")

        # Convert to DataFrames
        ref_df = self._embeddings_to_dataframe(reference_embeddings, reference_ids)
        curr_df = self._embeddings_to_dataframe(current_embeddings, current_ids)

        # Create report
        report = Report(
            metrics=[
                DataDriftPreset(),
                DataQualityPreset(),
            ]
        )

        report.run(reference_data=ref_df, current_data=curr_df)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = report_name or f"embedding_drift_{timestamp}"
        report_path = self.reports_dir / f"{report_name}.html"

        report.save_html(str(report_path))
        logger.info(f"Report saved to: {report_path}")

        # Save JSON summary
        json_path = self.reports_dir / f"{report_name}.json"
        report.save_json(str(json_path))

        return str(report_path)

    def create_recommendation_quality_report(
        self,
        recommendations_data: pd.DataFrame,
        reference_data: pd.DataFrame | None = None,
        report_name: str | None = None,
    ) -> str:
        """
        Create a report for recommendation quality metrics.

        Args:
            recommendations_data: DataFrame with recommendation results
                Expected columns: query_id, restaurant_id, similarity_score, rank
            reference_data: Optional reference data for comparison
            report_name: Optional custom report name

        Returns:
            Path to the generated report
        """
        logger.info("Creating recommendation quality report")

        if reference_data is not None:
            report = Report(
                metrics=[
                    DataDriftPreset(),
                    DataQualityPreset(),
                ]
            )
            report.run(reference_data=reference_data, current_data=recommendations_data)
        else:
            report = Report(
                metrics=[
                    DataQualityPreset(),
                ]
            )
            report.run(reference_data=None, current_data=recommendations_data)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = report_name or f"recommendation_quality_{timestamp}"
        report_path = self.reports_dir / f"{report_name}.html"

        report.save_html(str(report_path))
        logger.info(f"Report saved to: {report_path}")

        return str(report_path)

    def run_data_quality_tests(
        self,
        data: pd.DataFrame,
        test_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Run data quality tests on the provided data.

        Args:
            data: DataFrame to test
            test_name: Optional custom test name

        Returns:
            Dictionary with test results
        """
        logger.info("Running data quality tests")

        test_suite = TestSuite(
            tests=[
                DataQualityTestPreset(),
            ]
        )

        test_suite.run(reference_data=None, current_data=data)

        # Save test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = test_name or f"data_quality_{timestamp}"
        test_path = self.tests_dir / f"{test_name}.html"

        test_suite.save_html(str(test_path))
        logger.info(f"Test results saved to: {test_path}")

        # Get test results as dict
        results = test_suite.as_dict()

        # Save JSON
        json_path = self.tests_dir / f"{test_name}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)

        return results

    def run_drift_tests(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        test_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Run data drift tests comparing reference and current data.

        Args:
            reference_data: Reference (baseline) data
            current_data: Current data to test
            test_name: Optional custom test name

        Returns:
            Dictionary with test results
        """
        logger.info("Running data drift tests")

        test_suite = TestSuite(
            tests=[
                DataDriftTestPreset(),
            ]
        )

        test_suite.run(reference_data=reference_data, current_data=current_data)

        # Save test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = test_name or f"data_drift_{timestamp}"
        test_path = self.tests_dir / f"{test_name}.html"

        test_suite.save_html(str(test_path))
        logger.info(f"Test results saved to: {test_path}")

        # Get test results as dict
        results = test_suite.as_dict()

        # Save JSON
        json_path = self.tests_dir / f"{test_name}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)

        return results

    def _embeddings_to_dataframe(
        self,
        embeddings: np.ndarray,
        ids: list[str],
    ) -> pd.DataFrame:
        """
        Convert embeddings array to DataFrame.

        Args:
            embeddings: Numpy array of embeddings
            ids: List of IDs

        Returns:
            DataFrame with embeddings as columns
        """
        # Create column names
        n_dims = embeddings.shape[1]
        columns = [f"dim_{i}" for i in range(n_dims)]

        # Create DataFrame
        df = pd.DataFrame(embeddings, columns=columns)
        df.insert(0, "id", ids)

        return df

    def generate_monitoring_dashboard(
        self,
        embeddings: np.ndarray,
        ids: list[str],
        recommendations: pd.DataFrame,
        dashboard_name: str | None = None,
    ) -> dict[str, str]:
        """
        Generate a comprehensive monitoring dashboard.

        Args:
            embeddings: Current embeddings
            ids: Embedding IDs
            recommendations: Recent recommendations data
            dashboard_name: Optional custom dashboard name

        Returns:
            Dictionary with paths to generated reports
        """
        logger.info("Generating monitoring dashboard")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dashboard_name = dashboard_name or f"dashboard_{timestamp}"

        # Convert embeddings to DataFrame
        embeddings_df = self._embeddings_to_dataframe(embeddings, ids)

        # Run data quality tests
        self.run_data_quality_tests(
            embeddings_df, test_name=f"{dashboard_name}_embeddings_quality"
        )

        # Create recommendation quality report
        rec_report = self.create_recommendation_quality_report(
            recommendations, report_name=f"{dashboard_name}_recommendations"
        )

        paths = {
            "embeddings_quality_test": str(
                self.tests_dir / f"{dashboard_name}_embeddings_quality.html"
            ),
            "recommendations_report": rec_report,
        }

        logger.info(f"Dashboard generated with {len(paths)} reports")
        return paths


def create_sample_recommendations_data(
    query_ids: list[str],
    restaurant_ids: list[str],
    similarity_scores: list[float],
) -> pd.DataFrame:
    """
    Helper function to create sample recommendations DataFrame.

    Args:
        query_ids: List of query IDs
        restaurant_ids: List of recommended restaurant IDs
        similarity_scores: List of similarity scores

    Returns:
        DataFrame with recommendations data
    """
    return pd.DataFrame(
        {
            "query_id": query_ids,
            "restaurant_id": restaurant_ids,
            "similarity_score": similarity_scores,
            "timestamp": datetime.now(),
        }
    )
