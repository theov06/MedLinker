"""MLflow lifecycle tracking utilities for agentic pipeline.

This module provides optional MLflow integration for tracking pipeline runs,
metrics, and artifacts. All functions fail gracefully if MLflow is not installed
or not configured.
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path


# Try to import MLflow, but don't fail if not installed
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def is_mlflow_enabled() -> bool:
    """Check if MLflow is available and should be used.
    
    Returns:
        True if MLflow is installed and tracking URI is set
    """
    if not MLFLOW_AVAILABLE:
        return False
    
    # Check if tracking URI is configured
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    return tracking_uri is not None and tracking_uri.strip() != ""


def start_mlflow_run(run_name: str, experiment_name: str = "MedLinker-AI") -> Optional[Any]:
    """Start an MLflow run for pipeline tracking.
    
    Args:
        run_name: Descriptive name for this run
        experiment_name: MLflow experiment name
        
    Returns:
        MLflow run object if successful, None otherwise
    """
    if not is_mlflow_enabled():
        return None
    
    try:
        # Set experiment (creates if doesn't exist)
        mlflow.set_experiment(experiment_name)
        
        # Start run
        run = mlflow.start_run(run_name=run_name)
        return run
    except Exception as e:
        # Fail silently - don't crash the pipeline
        print(f"Warning: Failed to start MLflow run: {e}")
        return None


def end_mlflow_run() -> None:
    """End the current MLflow run.
    
    Safe to call even if no run is active.
    """
    if not is_mlflow_enabled():
        return
    
    try:
        mlflow.end_run()
    except Exception as e:
        print(f"Warning: Failed to end MLflow run: {e}")


def log_params(params: Dict[str, Any]) -> None:
    """Log parameters to MLflow.
    
    Args:
        params: Dictionary of parameter names and values
    """
    if not is_mlflow_enabled():
        return
    
    try:
        # Filter out None values
        filtered_params = {k: v for k, v in params.items() if v is not None}
        
        # Convert all values to strings (MLflow requirement)
        str_params = {k: str(v) for k, v in filtered_params.items()}
        
        mlflow.log_params(str_params)
    except Exception as e:
        print(f"Warning: Failed to log MLflow params: {e}")


def log_metrics(metrics: Dict[str, float]) -> None:
    """Log metrics to MLflow.
    
    Args:
        metrics: Dictionary of metric names and numeric values
    """
    if not is_mlflow_enabled():
        return
    
    try:
        # Filter out None values and ensure numeric
        filtered_metrics = {}
        for k, v in metrics.items():
            if v is not None:
                try:
                    filtered_metrics[k] = float(v)
                except (ValueError, TypeError):
                    print(f"Warning: Skipping non-numeric metric {k}={v}")
        
        if filtered_metrics:
            mlflow.log_metrics(filtered_metrics)
    except Exception as e:
        print(f"Warning: Failed to log MLflow metrics: {e}")


def log_artifacts(file_paths: List[str]) -> None:
    """Log artifact files to MLflow.
    
    Args:
        file_paths: List of file paths to log as artifacts
    """
    if not is_mlflow_enabled():
        return
    
    try:
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists() and path.is_file():
                mlflow.log_artifact(str(path))
    except Exception as e:
        print(f"Warning: Failed to log MLflow artifacts: {e}")


def log_artifact_directory(dir_path: str) -> None:
    """Log all files in a directory as artifacts.
    
    Args:
        dir_path: Directory path containing artifacts
    """
    if not is_mlflow_enabled():
        return
    
    try:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            mlflow.log_artifacts(str(path))
    except Exception as e:
        print(f"Warning: Failed to log MLflow artifact directory: {e}")


def set_tags(tags: Dict[str, str]) -> None:
    """Set tags on the current MLflow run.
    
    Args:
        tags: Dictionary of tag names and values
    """
    if not is_mlflow_enabled():
        return
    
    try:
        # Filter out None values
        filtered_tags = {k: str(v) for k, v in tags.items() if v is not None}
        mlflow.set_tags(filtered_tags)
    except Exception as e:
        print(f"Warning: Failed to set MLflow tags: {e}")
