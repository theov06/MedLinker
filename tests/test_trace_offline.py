"""Tests for tracing and auditability (offline mode)."""

import os
import json
import uuid
from pathlib import Path

import pytest

from medlinker_ai.models import (
    FacilityDocInput,
    FacilityAnalysisOutput,
    RegionSummary,
)
from medlinker_ai.extract import extract_capabilities
from medlinker_ai.verify import verify_facility
from medlinker_ai.aggregate import aggregate_regions
from medlinker_ai.qa import answer_planner_question
from medlinker_ai.trace import (
    start_trace,
    log_span,
    end_trace,
    get_trace,
    list_recent_traces,
)


@pytest.fixture(autouse=True)
def force_offline():
    """Force offline mode for all tests."""
    # Ensure no MLflow
    if "MLFLOW_TRACKING_URI" in os.environ:
        del os.environ["MLFLOW_TRACKING_URI"]
    
    # Ensure offline LLM
    os.environ["LLM_PROVIDER"] = "none"
    
    yield
    
    # Cleanup
    if "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]


@pytest.fixture
def sample_facility_doc():
    """Sample facility document for testing."""
    return FacilityDocInput(
        facility_id="FAC001",
        facility_name="Test Hospital",
        region="Test Region",
        country="Test Country",
        source_id="test_source",
        source_type="dataset_row",
        source_text="This hospital provides emergency care, surgery, and maternity services. "
                    "Equipment includes ultrasound machines and X-ray. "
                    "Staff: 5 doctors, 10 nurses."
    )


@pytest.fixture
def cleanup_traces():
    """Clean up trace files after tests."""
    yield
    
    # Remove traces file
    trace_file = Path("./outputs/traces.jsonl")
    if trace_file.exists():
        trace_file.unlink()


def test_trace_basic_lifecycle(cleanup_traces):
    """Test basic trace lifecycle: start, log, end, retrieve."""
    trace_id = str(uuid.uuid4())
    
    # Start trace
    returned_id = start_trace(trace_id)
    assert returned_id == trace_id
    
    # Log a span
    log_span(
        trace_id=trace_id,
        step_name="extract",
        inputs_summary={"facility_id": "FAC001"},
        outputs_summary={"services_count": 3},
        evidence_refs=2
    )
    
    # End trace
    end_trace(trace_id)
    
    # Retrieve trace
    trace = get_trace(trace_id)
    assert trace is not None
    assert trace.trace_id == trace_id
    assert len(trace.spans) == 1
    assert trace.spans[0].step_name == "extract"
    assert trace.spans[0].inputs_summary["facility_id"] == "FAC001"
    assert trace.spans[0].outputs_summary["services_count"] == 3
    assert trace.spans[0].evidence_refs == 2


def test_trace_multiple_spans(cleanup_traces):
    """Test trace with multiple spans."""
    trace_id = str(uuid.uuid4())
    
    start_trace(trace_id)
    
    # Log multiple spans
    log_span(
        trace_id=trace_id,
        step_name="extract",
        inputs_summary={"facility_id": "FAC001"},
        outputs_summary={"services_count": 3},
        evidence_refs=2
    )
    
    log_span(
        trace_id=trace_id,
        step_name="verify",
        inputs_summary={"facility_id": "FAC001"},
        outputs_summary={"status": "VERIFIED", "reasons_count": 0},
        evidence_refs=2
    )
    
    log_span(
        trace_id=trace_id,
        step_name="aggregate",
        inputs_summary={"region": "Test Region", "country": "Test Country"},
        outputs_summary={"desert_score": 30, "missing_critical_count": 1},
        evidence_refs=5
    )
    
    end_trace(trace_id)
    
    # Retrieve and verify
    trace = get_trace(trace_id)
    assert trace is not None
    assert len(trace.spans) == 3
    
    # Verify span order
    assert trace.spans[0].step_name == "extract"
    assert trace.spans[1].step_name == "verify"
    assert trace.spans[2].step_name == "aggregate"


def test_trace_no_raw_source_text(sample_facility_doc, cleanup_traces):
    """Test that traces never contain raw source_text."""
    trace_id = str(uuid.uuid4())
    
    # Run extraction with tracing
    start_trace(trace_id)
    capabilities, citations = extract_capabilities(sample_facility_doc, trace_id=trace_id)
    end_trace(trace_id)
    
    # Retrieve trace
    trace = get_trace(trace_id)
    assert trace is not None
    
    # Check that no span contains source_text
    for span in trace.spans:
        # Convert to JSON string for easy searching
        span_json = json.dumps(span.model_dump())
        
        # Should not contain the actual source text
        assert "emergency care, surgery, and maternity" not in span_json
        assert "ultrasound machines and X-ray" not in span_json
        
        # Should contain summaries only
        assert "facility_id" in span_json or "source_id" in span_json


def test_trace_full_pipeline(sample_facility_doc, cleanup_traces):
    """Test full pipeline with tracing."""
    # Run full pipeline
    analysis = verify_facility(sample_facility_doc)
    
    # Verify trace_id exists
    assert analysis.trace_id is not None
    assert len(analysis.trace_id) > 0
    
    # Retrieve trace
    trace = get_trace(analysis.trace_id)
    assert trace is not None
    
    # Should have extract and verify spans
    assert len(trace.spans) >= 2
    
    step_names = [s.step_name for s in trace.spans]
    assert "extract" in step_names
    assert "verify" in step_names


def test_trace_aggregation(sample_facility_doc, cleanup_traces):
    """Test aggregation with tracing."""
    # Create multiple facility outputs
    facilities = []
    for i in range(3):
        doc = FacilityDocInput(
            facility_id=f"FAC{i:03d}",
            facility_name=f"Hospital {i}",
            region="Test Region",
            country="Test Country",
            source_id=f"source_{i}",
            source_type="dataset_row",
            source_text="Provides emergency care and surgery."
        )
        analysis = verify_facility(doc)
        facilities.append(analysis)
    
    # Aggregate with tracing
    parent_trace_id = str(uuid.uuid4())
    start_trace(parent_trace_id)
    summaries = aggregate_regions(facilities, parent_trace_id=parent_trace_id)
    end_trace(parent_trace_id)
    
    # Verify trace
    trace = get_trace(parent_trace_id)
    assert trace is not None
    
    # Should have aggregate span
    step_names = [s.step_name for s in trace.spans]
    assert "aggregate" in step_names
    
    # Find aggregate span
    agg_span = next(s for s in trace.spans if s.step_name == "aggregate")
    assert "region" in agg_span.inputs_summary
    assert "desert_score" in agg_span.outputs_summary


def test_trace_qa(sample_facility_doc, cleanup_traces):
    """Test Q&A with tracing."""
    # Create facility outputs
    facilities = []
    for i in range(2):
        doc = FacilityDocInput(
            facility_id=f"FAC{i:03d}",
            facility_name=f"Hospital {i}",
            region="Test Region",
            country="Test Country",
            source_id=f"source_{i}",
            source_type="dataset_row",
            source_text="Provides emergency care and surgery."
        )
        analysis = verify_facility(doc)
        facilities.append(analysis)
    
    # Create region summary
    regions = [
        RegionSummary(
            country="Test Country",
            region="Test Region",
            total_facilities=2,
            facilities_analyzed=2,
            status_counts={"VERIFIED": 2, "SUSPICIOUS": 0, "INCOMPLETE": 0},
            verified_count=2,
            suspicious_count=0,
            incomplete_count=0,
            desert_score=30,
            missing_critical=["C-section"],
            coverage={
                "services": {"emergency": 2, "surgery": 2},
                "equipment": {},
                "staffing": {}
            },
            supporting_facility_ids=["FAC000", "FAC001"],
            trace_id="test_trace_id"
        )
    ]
    
    # Answer question
    result = answer_planner_question(
        "Which regions lack C-section capability?",
        facilities,
        regions
    )
    
    # Verify trace_id exists
    assert "trace_id" in result
    assert result["trace_id"] is not None
    
    # Retrieve trace
    trace = get_trace(result["trace_id"])
    assert trace is not None
    
    # Should have answer span
    step_names = [s.step_name for s in trace.spans]
    assert "answer" in step_names


def test_trace_list_recent(cleanup_traces):
    """Test listing recent traces."""
    # Create multiple traces
    trace_ids = []
    for i in range(5):
        trace_id = str(uuid.uuid4())
        trace_ids.append(trace_id)
        
        start_trace(trace_id)
        log_span(
            trace_id=trace_id,
            step_name="extract",
            inputs_summary={"facility_id": f"FAC{i:03d}"},
            outputs_summary={"services_count": 3},
            evidence_refs=2
        )
        end_trace(trace_id)
    
    # List recent traces
    recent = list_recent_traces(limit=10)
    
    # Should contain all our traces
    assert len(recent) >= 5
    
    # Should be in reverse order (most recent first)
    for trace_id in trace_ids:
        assert trace_id in recent


def test_trace_step_order_validation(sample_facility_doc, cleanup_traces):
    """Test that trace spans are in logical order."""
    # Run full pipeline
    analysis = verify_facility(sample_facility_doc)
    
    # Retrieve trace
    trace = get_trace(analysis.trace_id)
    assert trace is not None
    
    # Get step names in order
    step_names = [s.step_name for s in trace.spans]
    
    # Extract should come before verify
    if "extract" in step_names and "verify" in step_names:
        extract_idx = step_names.index("extract")
        verify_idx = step_names.index("verify")
        assert extract_idx < verify_idx


def test_trace_evidence_refs_count(sample_facility_doc, cleanup_traces):
    """Test that evidence_refs are properly counted."""
    trace_id = str(uuid.uuid4())
    
    # Run extraction with tracing
    start_trace(trace_id)
    capabilities, citations = extract_capabilities(sample_facility_doc, trace_id=trace_id)
    end_trace(trace_id)
    
    # Retrieve trace
    trace = get_trace(trace_id)
    assert trace is not None
    
    # Find extract span
    extract_span = next(s for s in trace.spans if s.step_name == "extract")
    
    # Evidence refs should match citation count
    assert extract_span.evidence_refs == len(citations)
    assert extract_span.evidence_refs > 0


def test_trace_persistence(cleanup_traces):
    """Test that traces persist to disk."""
    trace_id = str(uuid.uuid4())
    
    start_trace(trace_id)
    log_span(
        trace_id=trace_id,
        step_name="extract",
        inputs_summary={"facility_id": "FAC001"},
        outputs_summary={"services_count": 3},
        evidence_refs=2
    )
    end_trace(trace_id)
    
    # Verify file exists
    trace_file = Path("./outputs/traces.jsonl")
    assert trace_file.exists()
    
    # Verify content
    with open(trace_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) >= 1
        
        # Find our trace
        found = False
        for line in lines:
            data = json.loads(line)
            if data["trace_id"] == trace_id:
                found = True
                assert len(data["spans"]) == 1
                break
        
        assert found, "Trace not found in file"


def test_trace_outputs_summary_no_large_payloads(sample_facility_doc, cleanup_traces):
    """Test that outputs_summary contains only counts/IDs, not large payloads."""
    # Run full pipeline
    analysis = verify_facility(sample_facility_doc)
    
    # Retrieve trace
    trace = get_trace(analysis.trace_id)
    assert trace is not None
    
    for span in trace.spans:
        # Check outputs_summary values
        for key, value in span.outputs_summary.items():
            # Should be small types only
            assert isinstance(value, (int, float, bool, str))
            
            # If string, should be short (ID or status)
            if isinstance(value, str):
                assert len(value) < 100, f"outputs_summary contains large string: {key}={value}"
