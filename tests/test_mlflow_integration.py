"""Tests for MLflow integration (optional dependency)."""

import pytest
from medlinker_ai.mlflow_utils import (
    is_mlflow_enabled,
    start_mlflow_run,
    end_mlflow_run,
    log_params,
    log_metrics,
    log_artifacts,
    set_tags
)


def test_mlflow_utils_safe_without_mlflow():
    """Test that MLflow utils work safely when MLflow is not installed."""
    # These should all succeed without raising exceptions
    enabled = is_mlflow_enabled()
    assert isinstance(enabled, bool)
    
    # All these should be safe no-ops if MLflow not available
    start_mlflow_run("test_run")
    log_params({"test": "value", "number": 123})
    log_metrics({"metric1": 1.0, "metric2": 2.5})
    log_artifacts(["nonexistent_file.txt"])
    set_tags({"tag1": "value1"})
    end_mlflow_run()


def test_mlflow_utils_handle_none_values():
    """Test that MLflow utils handle None values gracefully."""
    # Should filter out None values
    log_params({"key1": "value1", "key2": None})
    log_metrics({"metric1": 1.0, "metric2": None})
    set_tags({"tag1": "value1", "tag2": None})


def test_mlflow_utils_handle_invalid_metrics():
    """Test that MLflow utils handle non-numeric metrics gracefully."""
    # Should skip non-numeric values
    log_metrics({
        "valid": 1.0,
        "invalid_str": "not a number",
        "invalid_none": None
    })


def test_mlflow_integration_in_qa():
    """Test that Q&A works with MLflow tracking."""
    from medlinker_ai.qa import answer_planner_question
    from medlinker_ai.models import RegionSummary
    
    regions = [
        RegionSummary(
            country="TEST",
            region="R1",
            total_facilities=5,
            facilities_analyzed=5,
            status_counts={"VERIFIED": 5},
            coverage={},
            missing_critical=[],
            desert_score=20,
            supporting_facility_ids=["f1"],
            trace_id="test"
        )
    ]
    
    result = answer_planner_question("Test question?", [], regions)
    
    assert "answer" in result
    assert "citations" in result
    assert "trace_id" in result
