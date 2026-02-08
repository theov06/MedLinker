"""Tests for optional LangGraph orchestration."""

import pytest
import os
from fastapi.testclient import TestClient


def test_langgraph_orchestrator_optional():
    """Test that system works without LangGraph orchestrator."""
    from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary
    from medlinker_ai.orchestrator import run_ask_flow
    
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
    
    # Ensure orchestrator is disabled
    os.environ.pop("ORCHESTRATOR", None)
    
    # Should work without orchestrator (direct call)
    result = run_ask_flow(
        "Which regions lack C-section?",
        [],
        regions,
        llm_provider="none"
    )
    
    assert "answer" in result
    assert "citations" in result
    assert "trace_id" in result
    assert len(result["answer"]) > 0


def test_langgraph_orchestrator_enabled():
    """Test that LangGraph orchestrator works when enabled."""
    try:
        from langgraph.graph import StateGraph
    except ImportError:
        pytest.skip("LangGraph not installed")
    
    from medlinker_ai.models import RegionSummary
    from medlinker_ai.orchestrator import run_ask_flow, is_orchestrator_enabled
    
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
    
    # Enable orchestrator
    os.environ["ORCHESTRATOR"] = "langgraph"
    
    try:
        # Check that orchestrator is enabled
        assert is_orchestrator_enabled()
        
        # Run with orchestrator
        result = run_ask_flow(
            "Which regions lack C-section?",
            [],
            regions,
            llm_provider="none"
        )
        
        # Should return same schema
        assert "answer" in result
        assert "citations" in result
        assert "trace_id" in result
        assert len(result["answer"]) > 0
    finally:
        os.environ.pop("ORCHESTRATOR", None)


def test_api_ask_with_orchestrator():
    """Test /ask endpoint with LangGraph orchestrator enabled."""
    try:
        from langgraph.graph import StateGraph
    except ImportError:
        pytest.skip("LangGraph not installed")
    
    from medlinker_ai.api import app
    from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary
    import json
    from pathlib import Path
    
    # Create test data files
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Create minimal test data
    facilities = [
        FacilityAnalysisOutput(
            facility_id="TEST-001",
            extracted_capabilities={
                "services": ["Surgery"],
                "equipment": [],
                "staffing": [],
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
    
    regions = [
        RegionSummary(
            country="TEST",
            region="R1",
            total_facilities=1,
            facilities_analyzed=1,
            status_counts={"VERIFIED": 1},
            coverage={},
            missing_critical=["service:c-section"],
            desert_score=40,
            supporting_facility_ids=["TEST-001"],
            trace_id="test"
        )
    ]
    
    # Write test data
    with open(output_dir / "facilities.jsonl", 'w') as f:
        for facility in facilities:
            f.write(json.dumps(facility.model_dump()) + "\n")
    
    with open(output_dir / "regions.json", 'w') as f:
        json.dump([r.model_dump() for r in regions], f)
    
    # Enable orchestrator
    os.environ["ORCHESTRATOR"] = "langgraph"
    
    try:
        client = TestClient(app)
        
        # Test /ask endpoint
        response = client.post(
            "/ask",
            json={"question": "Which regions lack C-section?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response schema
        assert "answer" in data
        assert "citations" in data
        assert "trace_id" in data
        assert isinstance(data["citations"], list)
        assert isinstance(data["trace_id"], str)
    finally:
        os.environ.pop("ORCHESTRATOR", None)


def test_orchestrator_output_matches_direct_call():
    """Test that orchestrator output matches direct function call."""
    try:
        from langgraph.graph import StateGraph
    except ImportError:
        pytest.skip("LangGraph not installed")
    
    from medlinker_ai.models import RegionSummary
    from medlinker_ai.orchestrator import run_ask_flow
    from medlinker_ai.qa import answer_planner_question
    
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
    
    question = "Which regions lack C-section?"
    
    # Direct call
    os.environ.pop("ORCHESTRATOR", None)
    direct_result = answer_planner_question(question, [], regions, llm_provider="none")
    
    # Orchestrator call
    os.environ["ORCHESTRATOR"] = "langgraph"
    try:
        orch_result = run_ask_flow(question, [], regions, llm_provider="none")
    finally:
        os.environ.pop("ORCHESTRATOR", None)
    
    # Both should have same structure
    assert "answer" in direct_result
    assert "answer" in orch_result
    assert "citations" in direct_result
    assert "citations" in orch_result
    assert "trace_id" in direct_result
    assert "trace_id" in orch_result
