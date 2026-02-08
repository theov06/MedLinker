"""Tracing and auditability for MedLinker AI pipeline."""

import os
import json
from datetime import datetime
from typing import Dict, List, Literal, Optional, Any
from pathlib import Path

from pydantic import BaseModel


StepName = Literal["extract", "verify", "aggregate", "answer"]


class TraceSpan(BaseModel):
    """A single traced step in the pipeline."""
    trace_id: str
    step_name: StepName
    inputs_summary: Dict[str, Any]
    outputs_summary: Dict[str, Any]
    evidence_refs: int  # Count of citations/evidence
    timestamp: str  # ISO format


class TraceRun(BaseModel):
    """Complete trace of a pipeline run."""
    trace_id: str
    spans: List[TraceSpan]


# Global trace storage
_active_traces: Dict[str, List[TraceSpan]] = {}
_mlflow_available = False
_mlflow_client = None

# Check if MLflow is available
try:
    import mlflow
    if os.getenv("MLFLOW_TRACKING_URI"):
        _mlflow_available = True
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
except ImportError:
    pass


def start_trace(trace_id: str) -> str:
    """Start a new trace.
    
    Args:
        trace_id: Unique trace identifier
        
    Returns:
        The trace_id
    """
    _active_traces[trace_id] = []
    
    if _mlflow_available:
        try:
            mlflow.start_run(run_id=trace_id, run_name=f"medlinker_{trace_id[:8]}")
            mlflow.set_tag("pipeline", "medlinker_ai")
        except Exception:
            # If MLflow fails, continue with local logging
            pass
    
    return trace_id


def log_span(
    trace_id: str,
    step_name: StepName,
    inputs_summary: Dict[str, Any],
    outputs_summary: Dict[str, Any],
    evidence_refs: int
) -> None:
    """Log a pipeline step span.
    
    Args:
        trace_id: Trace identifier
        step_name: Name of the step
        inputs_summary: Summary of inputs (no raw text)
        outputs_summary: Summary of outputs (counts, IDs, booleans)
        evidence_refs: Count of citations/evidence
    """
    span = TraceSpan(
        trace_id=trace_id,
        step_name=step_name,
        inputs_summary=inputs_summary,
        outputs_summary=outputs_summary,
        evidence_refs=evidence_refs,
        timestamp=datetime.now().isoformat()
    )
    
    # Store locally
    if trace_id not in _active_traces:
        _active_traces[trace_id] = []
    _active_traces[trace_id].append(span)
    
    # Log to MLflow if available
    if _mlflow_available:
        try:
            # Log as tags and metrics
            mlflow.set_tag(f"step_{step_name}", "completed")
            
            # Log small params
            for key, value in inputs_summary.items():
                if isinstance(value, (str, int, float, bool)):
                    mlflow.log_param(f"{step_name}_input_{key}", str(value)[:250])
            
            # Log metrics (counts only)
            for key, value in outputs_summary.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(f"{step_name}_{key}", value)
            
            mlflow.log_metric(f"{step_name}_evidence_refs", evidence_refs)
        except Exception:
            # If MLflow fails, continue with local logging
            pass


def end_trace(trace_id: str) -> None:
    """End a trace and persist to local storage.
    
    Args:
        trace_id: Trace identifier
    """
    if trace_id in _active_traces:
        spans = _active_traces[trace_id]
        
        # Write to local JSON file
        output_dir = Path("./outputs")
        output_dir.mkdir(exist_ok=True)
        
        trace_file = output_dir / "traces.jsonl"
        
        trace_run = TraceRun(trace_id=trace_id, spans=spans)
        
        with open(trace_file, 'a') as f:
            f.write(json.dumps(trace_run.model_dump()) + "\n")
        
        # Clean up
        del _active_traces[trace_id]
    
    # End MLflow run if active
    if _mlflow_available:
        try:
            mlflow.end_run()
        except Exception:
            pass


def get_trace(trace_id: str) -> Optional[TraceRun]:
    """Retrieve a trace by ID.
    
    Args:
        trace_id: Trace identifier
        
    Returns:
        TraceRun if found, None otherwise
    """
    # Check active traces first
    if trace_id in _active_traces:
        return TraceRun(trace_id=trace_id, spans=_active_traces[trace_id])
    
    # Check local file
    trace_file = Path("./outputs/traces.jsonl")
    if trace_file.exists():
        with open(trace_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data["trace_id"] == trace_id:
                        return TraceRun(**data)
    
    # Check MLflow if available
    if _mlflow_available:
        try:
            run = mlflow.get_run(trace_id)
            # Reconstruct spans from MLflow data
            # (simplified - in production would parse tags/metrics)
            return None  # Placeholder
        except Exception:
            pass
    
    return None


def list_recent_traces(limit: int = 10) -> List[str]:
    """List recent trace IDs.
    
    Args:
        limit: Maximum number of traces to return
        
    Returns:
        List of trace IDs
    """
    trace_ids = []
    trace_file = Path("./outputs/traces.jsonl")
    
    if trace_file.exists():
        with open(trace_file, 'r') as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                if line.strip():
                    data = json.loads(line)
                    trace_ids.append(data["trace_id"])
    
    return trace_ids
