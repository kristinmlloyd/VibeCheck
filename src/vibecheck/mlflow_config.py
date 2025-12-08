"""
MLFlow configuration and utilities for VibeCheck experiment tracking.
"""

import os
from pathlib import Path
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient


class MLFlowConfig:
    """Configuration class for MLFlow tracking."""

    # Default tracking URI (can be overridden by environment variable)
    DEFAULT_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

    # Experiment names
    EMBEDDING_EXPERIMENT = "vibecheck-embeddings"
    VIBE_MAPPING_EXPERIMENT = "vibecheck-vibe-mapping"
    RECOMMENDATION_EXPERIMENT = "vibecheck-recommendations"

    # Artifact paths
    ARTIFACTS_DIR = Path("mlruns/artifacts")

    @classmethod
    def setup_mlflow(cls, tracking_uri: str | None = None) -> None:
        """
        Initialize MLFlow tracking configuration.

        Args:
            tracking_uri: Optional custom tracking URI. If not provided, uses default.
        """
        uri = tracking_uri or cls.DEFAULT_TRACKING_URI
        mlflow.set_tracking_uri(uri)
        print(f"MLFlow tracking URI set to: {uri}")

        # Create artifacts directory if it doesn't exist
        cls.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create_experiment(cls, experiment_name: str, tags: dict[str, Any | None] = None) -> str:
        """
        Create an MLFlow experiment if it doesn't exist.

        Args:
            experiment_name: Name of the experiment
            tags: Optional tags for the experiment

        Returns:
            Experiment ID
        """
        client = MlflowClient()

        try:
            experiment = client.get_experiment_by_name(experiment_name)
            if experiment:
                return experiment.experiment_id
        except Exception:
            pass

        # Create new experiment
        experiment_id = mlflow.create_experiment(
            experiment_name,
            tags=tags or {}
        )
        print(f"Created experiment '{experiment_name}' with ID: {experiment_id}")
        return experiment_id

    @classmethod
    def get_or_create_experiment(cls, experiment_name: str) -> str:
        """
        Get existing experiment ID or create new one.

        Args:
            experiment_name: Name of the experiment

        Returns:
            Experiment ID
        """
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            return experiment.experiment_id
        return cls.create_experiment(experiment_name)


def init_mlflow(tracking_uri: str | None = None) -> None:
    """
    Initialize MLFlow tracking with default experiments.

    Args:
        tracking_uri: Optional custom tracking URI
    """
    MLFlowConfig.setup_mlflow(tracking_uri)

    # Create default experiments
    MLFlowConfig.get_or_create_experiment(MLFlowConfig.EMBEDDING_EXPERIMENT)
    MLFlowConfig.get_or_create_experiment(MLFlowConfig.VIBE_MAPPING_EXPERIMENT)
    MLFlowConfig.get_or_create_experiment(MLFlowConfig.RECOMMENDATION_EXPERIMENT)

    print("MLFlow initialized with default experiments")
