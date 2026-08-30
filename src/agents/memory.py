"""
Memory module - conversation history interface.

Implementation deferred for single-turn baseline.
"""


def get_context() -> list[dict]:
    """Get conversation context.

    Returns:
        List of prior turns (empty for now)
    """
    return []


def add_turn(question: str, answer: str):
    """Record a turn (no-op for now)."""
    pass
