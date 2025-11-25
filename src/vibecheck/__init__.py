"""
VibeCheck - Restaurant recommendation based on visual aesthetics.
"""

__version__ = "0.1.0"

from vibecheck.logging_config import get_logger, setup_logging
from vibecheck.recommender import VibeCheckRecommender
from vibecheck.utils import hello_vibecheck, validate_restaurant_name

__all__ = [
    "VibeCheckRecommender",
    "hello_vibecheck",
    "validate_restaurant_name",
    "setup_logging",
    "get_logger",
]
