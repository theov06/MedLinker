"""Utility functions for MedLinker AI."""

import uuid


def generate_trace_id() -> str:
    """Generate a unique trace ID for tracking analysis runs.
    
    Returns:
        A UUID4 string for tracing.
    """
    return str(uuid.uuid4())
