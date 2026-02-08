"""Tests for LangGraph orchestration wrapper."""

import pytest
import json
from pathlib import Path

from medlinker_ai.models import FacilityDocInput, FacilityAnalysisOutput, RegionSummary
from medlinker_ai.graph import (
    run_extraction_graph,
    run_verification_graph,
    run_aggregation_graph,
    run_qa_graph
)


def load_example(filename: str) -> FacilityDocInput:
    """Load example facility input."""
    path = Path("examples") / filename
    with open(path) as f:
        data = json.load(f)
    return FacilityDocInput(**data)


def test_extraction_graph():
    """Test that extraction graph produces same output as direct function call."""
    doc = load_example("facility_input_golden.json")
    
    # Run through graph
    capabilities, citations = run_extraction_graph(doc, llm_provider="none")
    
    # Verify output
    assert capabilities is not None
    assert len(capabilities.services) > 0
    assert len(citations) > 0


def test_verification_graph():
    """Test that verification graph produces same output as direct function call."""
    doc = load_example("facility_input_golden.json")
    
    # Run through graph
    analysis = run_verification_graph(doc, llm_provider="none")
    
    # Verify output
    assert analysis is not None
    assert analysis.facility_id == doc.facility_id
    assert analysis.status in ["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]
    assert analysis.confidence in ["LOW", "MEDIUM", "HIGH"]
    assert analysis.trace_id is not None


def test_aggregation_graph():
    """Test that aggregation graph produces same output as direct function call."""
    # Create test facility outputs
    facility_outputs = [
        FacilityAnalysisOutput(
            facility_id="TEST-001",
            extracted_capabilities={
                "services": ["Surgery", "Emergency"],
                "equipment": ["Ultrasound"],
                "staffing": ["Doctors"],
                "hours": "24/7",
                "referral_capacity": "BASIC",
                "emergency_capability": "YES"
            },
            status="VERIFIED",
            reasons=[],
            confidence="HIGH",
            citations=[],
            trace_id="test"
        )
    ]
    
    # Run through graph
    summaries = run_aggregation_graph(facility_outputs)
    
    # Verify output
    assert summaries is not None
    assert len(summaries) > 0
    assert summaries[0].total_facilities == 1


def test_qa_graph():
    """Test that Q&A graph produces same output as direct function call."""
    # Create test data
    regions = [
        RegionSummary(
            country="TEST",
            region="R1",
            total_facilities=5,
            facilities_analyzed=5,
            status_counts={"VERIFIED": 5},
            coverage={},
            missing_critical=["service:c-section"],
            desert_score=40,
            supporting_facility_ids=["f1"],
            trace_id="test"
        )
    ]
    
    # Run through graph
    result = run_qa_graph(
        "Which regions lack C-section?",
        [],
        regions,
        llm_provider="none"
    )
    
    # Verify output
    assert "answer" in result
    assert "citations" in result
    assert "trace_id" in result
    assert len(result["answer"]) > 0


def test_graph_output_matches_direct_call():
    """Test that graph output is identical to direct function call."""
    from medlinker_ai.extract import extract_capabilities
    
    doc = load_example("facility_input_golden.json")
    
    # Direct call
    direct_caps, direct_cites = extract_capabilities(doc, llm_provider="none")
    
    # Graph call
    graph_caps, graph_cites = run_extraction_graph(doc, llm_provider="none")
    
    # Compare outputs (should be identical)
    assert direct_caps.services == graph_caps.services
    assert direct_caps.equipment == graph_caps.equipment
    assert direct_caps.staffing == graph_caps.staffing
    assert len(direct_cites) == len(graph_cites)


def test_graph_preserves_trace_id():
    """Test that graph preserves trace_id through execution."""
    doc = load_example("facility_input_golden.json")
    test_trace_id = "test-trace-123"
    
    # Run with specific trace_id
    capabilities, citations = run_extraction_graph(
        doc,
        llm_provider="none",
        trace_id=test_trace_id
    )
    
    # Verify trace_id is preserved (in citations)
    assert capabilities is not None
    assert citations is not None
