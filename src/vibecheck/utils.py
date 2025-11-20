"""Utility functions for VibeCheck."""


def hello_vibecheck() -> str:
    """
    Return a greeting message.

    Returns:
        A welcome message string.

    Example:
        >>> hello_vibecheck()
        'Welcome to VibeCheck!'
    """
    return "Welcome to VibeCheck!"


def validate_restaurant_name(name: str) -> bool:
    """
    Validate a restaurant name.

    Args:
        name: The restaurant name to validate.

    Returns:
        True if the name is valid, False otherwise.

    Example:
        >>> validate_restaurant_name("Joe's Pizza")
        True
        >>> validate_restaurant_name("")
        False
    """
    return bool(name and name.strip())
