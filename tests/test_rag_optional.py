"""Tests for optional RAG functionality."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary
from medlinker_ai.qa import answer_planner_question


def test_qa_works_without_rag_indexes():
    """Test that Q&A works when RAG indexes are missing (default behavior)."""
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
    
    # Ensure RAG is disabled
    os.environ.pop("RAG_ENABLED", None)
    
    # Should work without RAG
    result = answer_planner_question(
        "Which regions lack C-section?",
        [],
        regions,
        llm_provider="none"
    )
    
    assert "answer" in result
    assert "citations" in result
    assert "trace_id" in result
    assert len(result["answer"]) > 0


def test_rag_retrieval_with_indexes():
    """Test RAG retrieval when indexes are built."""
    try:
        from medlinker_ai.rag import build_indexes, retrieve
    except ImportError:
        pytest.skip("RAG dependencies not installed")
    
    # Create test data
    facilities = [
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
        ),
        FacilityAnalysisOutput(
            facility_id="TEST-002",
            extracted_capabilities={
                "services": ["Maternity", "C-Section"],
                "equipment": ["X-Ray"],
                "staffing": ["Midwives"],
                "hours": "Mon-Fri",
                "referral_capacity": "NONE",
                "emergency_capability": "NO"
            },
            status="INCOMPLETE",
            reasons=["Hours not specified"],
            confidence="MEDIUM",
            citations=[],
            trace_id="test"
        )
    ]
    
    regions = [
        RegionSummary(
            country="TEST",
            region="R1",
            total_facilities=2,
            facilities_analyzed=2,
            status_counts={"VERIFIED": 1, "INCOMPLETE": 1},
            coverage={},
            missing_critical=[],
            desert_score=20,
            supporting_facility_ids=["TEST-001", "TEST-002"],
            trace_id="test"
        )
    ]
    
    # Build indexes in temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        build_indexes(facilities, regions, out_dir=tmpdir)
        
        # Test retrieval
        result = retrieve("surgery emergency", k_fac=2, k_reg=1, index_dir=tmpdir)
        
        assert result is not None
        facility_ids, region_keys = result
        assert len(facility_ids) > 0
        assert "TEST-001" in facility_ids  # Should retrieve surgery facility


def test_rag_fallback_when_indexes_missing():
    """Test that RAG falls back gracefully when indexes are missing."""
    try:
        from medlinker_ai.rag import retrieve
    except ImportError:
        pytest.skip("RAG dependencies not installed")
    
    # Try to retrieve from non-existent directory
    result = retrieve("test question", index_dir="/nonexistent/path")
    
    # Should return None, not crash
    assert result is None


def test_qa_with_rag_enabled():
    """Test Q&A with RAG enabled (if indexes exist)."""
    try:
        from medlinker_ai.rag import build_indexes
    except ImportError:
        pytest.skip("RAG dependencies not installed")
    
    # Create test data
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
    
    # Build indexes in temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        build_indexes(facilities, regions, out_dir=tmpdir)
        
        # Enable RAG and point to temp indexes
        os.environ["RAG_ENABLED"] = "1"
        
        # Monkey-patch the index directory for this test
        import medlinker_ai.rag.faiss_store as faiss_store
        original_retrieve = faiss_store.retrieve
        
        def patched_retrieve(question, k_fac=8, k_reg=5, index_dir="outputs/faiss"):
            return original_retrieve(question, k_fac, k_reg, tmpdir)
        
        faiss_store.retrieve = patched_retrieve
        
        try:
            # Run Q&A with RAG
            result = answer_planner_question(
                "Which regions lack C-section?",
                facilities,
                regions,
                llm_provider="none"
            )
            
            # Should still work and return valid response
            assert "answer" in result
            assert "citations" in result
            assert len(result["answer"]) > 0
        finally:
            # Restore original function
            faiss_store.retrieve = original_retrieve
            os.environ.pop("RAG_ENABLED", None)
