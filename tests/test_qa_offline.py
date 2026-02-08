"""Tests for Q&A functionality (offline mode)."""

import os

# Force offline mode
os.environ["LLM_PROVIDER"] = "none"

from medlinker_ai.models import (
    FacilityAnalysisOutput,
    CapabilitySchemaV0,
    Citation,
    RegionSummary
)
from medlinker_ai.qa import (
    keyword_match_score,
    retrieve_context,
    detect_question_intent,
    answer_planner_question
)


def create_test_facility(
    facility_id: str,
    services: list[str],
    equipment: list[str],
    staffing: list[str],
    status: str = "VERIFIED"
) -> FacilityAnalysisOutput:
    """Create a test facility output."""
    return FacilityAnalysisOutput(
        facility_id=facility_id,
        extracted_capabilities=CapabilitySchemaV0(
            services=services,
            equipment=equipment,
            staffing=staffing
        ),
        status=status,
        reasons=[] if status == "VERIFIED" else ["Test reason"],
        confidence="HIGH",
        citations=[
            Citation(
                source_id=facility_id,
                snippet=f"Test snippet for {facility_id}",
                field="services"
            )
        ],
        trace_id="test_trace"
    )


def create_test_region(
    country: str,
    region: str,
    desert_score: int,
    missing_critical: list[str]
) -> RegionSummary:
    """Create a test region summary."""
    return RegionSummary(
        country=country,
        region=region,
        total_facilities=5,
        facilities_analyzed=5,
        status_counts={"VERIFIED": 3, "INCOMPLETE": 2},
        coverage={
            "services": {"c-section": 2, "emergency": 3},
            "equipment": {"ultrasound": 2},
            "staffing": {"doctor": 4}
        },
        missing_critical=missing_critical,
        desert_score=desert_score,
        supporting_facility_ids=["TEST-001"],
        trace_id="test_trace"
    )


def test_keyword_match_score():
    """Test keyword matching."""
    query = "ultrasound capability"
    text = "This facility has ultrasound equipment and good capability"
    
    score = keyword_match_score(query, text)
    assert score == 2  # Both keywords match


def test_retrieve_context():
    """Test context retrieval."""
    facilities = [
        create_test_facility("F1", ["Ultrasound"], [], []),
        create_test_facility("F2", ["X-ray"], [], []),
        create_test_facility("F3", ["Emergency"], [], []),
    ]
    
    regions = [
        create_test_region("GH", "ACC", 20, []),
        create_test_region("GH", "ASH", 80, ["service:ultrasound"]),
    ]
    
    context = retrieve_context("ultrasound", facilities, regions, k=2)
    
    assert len(context["selected_facilities"]) <= 2
    assert len(context["selected_regions"]) <= 2


def test_detect_question_intent():
    """Test question intent detection."""
    assert detect_question_intent("Which regions lack C-section?") == "desert"
    assert detect_question_intent("Show suspicious facilities") == "suspicious"
    assert detect_question_intent("Which facilities are incomplete?") == "incomplete"
    assert detect_question_intent("Where can I find ultrasound?") == "capability"


def test_answer_medical_desert_question():
    """Test answering medical desert question."""
    facilities = []
    regions = [
        create_test_region("GH", "ACC", 20, ["service:laboratory"]),
        create_test_region("GH", "ASH", 80, ["service:c-section", "equipment:ultrasound"]),
        create_test_region("GH", "NTH", 60, ["service:emergency"]),
    ]
    
    result = answer_planner_question(
        "Which regions are medical deserts?",
        facilities,
        regions
    )
    
    assert result["answer"] is not None
    assert len(result["answer"]) > 0
    assert result["citations"] is not None
    assert result["trace_id"] is not None


def test_answer_suspicious_facilities_question():
    """Test answering suspicious facilities question."""
    facilities = [
        create_test_facility("F1", ["Surgery"], [], [], status="SUSPICIOUS"),
        create_test_facility("F2", ["Emergency"], [], [], status="VERIFIED"),
        create_test_facility("F3", ["C-Section"], [], [], status="SUSPICIOUS"),
    ]
    regions = []
    
    result = answer_planner_question(
        "Show suspicious facilities",
        facilities,
        regions
    )
    
    assert result["answer"] is not None
    assert "suspicious" in result["answer"].lower() or "F1" in result["answer"]
    assert result["citations"] is not None


def test_answer_capability_question():
    """Test answering capability search question."""
    facilities = [
        create_test_facility("F1", ["Ultrasound"], ["Ultrasound machine"], []),
        create_test_facility("F2", ["X-ray"], ["X-ray machine"], []),
        create_test_facility("F3", ["Emergency"], [], []),
    ]
    regions = []
    
    result = answer_planner_question(
        "Where can I find ultrasound capability?",
        facilities,
        regions
    )
    
    assert result["answer"] is not None
    assert len(result["answer"]) > 0
    assert result["citations"] is not None


def test_citations_non_empty():
    """Test that citations are provided."""
    facilities = [
        create_test_facility("F1", ["Surgery"], [], [], status="SUSPICIOUS"),
    ]
    regions = [
        create_test_region("GH", "ASH", 80, ["service:c-section"]),
    ]
    
    # Test desert question
    result = answer_planner_question(
        "Which regions lack critical services?",
        facilities,
        regions
    )
    
    assert len(result["citations"]) > 0


def test_citation_snippets_max_length():
    """Test that citation snippets are <= 500 chars."""
    facilities = []
    regions = [
        create_test_region("GH", "ASH", 100, ["service:c-section"] * 20),
    ]
    
    result = answer_planner_question(
        "Which regions are medical deserts?",
        facilities,
        regions
    )
    
    for citation in result["citations"]:
        assert len(citation["snippet"]) <= 500


def test_answer_non_empty():
    """Test that answer is always non-empty."""
    facilities = [
        create_test_facility("F1", ["Emergency"], [], []),
    ]
    regions = [
        create_test_region("GH", "ACC", 20, []),
    ]
    
    questions = [
        "Which regions are medical deserts?",
        "Show suspicious facilities",
        "Where can I find ultrasound?"
    ]
    
    for question in questions:
        result = answer_planner_question(question, facilities, regions)
        assert result["answer"] is not None
        assert len(result["answer"]) > 0


def test_no_hallucinations():
    """Test that answer doesn't mention non-existent facilities."""
    facilities = [
        create_test_facility("F1", ["Emergency"], [], []),
    ]
    regions = []
    
    result = answer_planner_question(
        "Show all facilities",
        facilities,
        regions
    )
    
    # Should only mention F1, not invent F2, F3, etc.
    assert "F1" in result["answer"] or "1 facilit" in result["answer"].lower()
    assert "F2" not in result["answer"]
    assert "F3" not in result["answer"]


def test_insufficient_data_handling():
    """Test handling of insufficient data."""
    facilities = []
    regions = []
    
    result = answer_planner_question(
        "Where can I find MRI machines?",
        facilities,
        regions
    )
    
    # Should indicate no data or not found
    assert "no" in result["answer"].lower() or "not found" in result["answer"].lower()



def test_citations_required_for_numeric_claims():
    """Test that numeric claims always have citations."""
    import re
    
    # Create test data with high desert score
    from medlinker_ai.models import RegionSummary
    
    facilities = []
    regions = [
        RegionSummary(
            country="GH",
            region="Northern",
            total_facilities=5,
            facilities_analyzed=5,
            status_counts={"VERIFIED": 2, "INCOMPLETE": 3},
            verified_count=2,
            suspicious_count=0,
            incomplete_count=3,
            desert_score=85,
            missing_critical=["service:c-section"],
            coverage={"services": {}, "equipment": {}, "staffing": {}},
            supporting_facility_ids=["FAC001"],
            trace_id="test"
        )
    ]
    
    # Ask a question that will generate numeric claims
    result = answer_planner_question(
        "Which regions are medical deserts?",
        facilities,
        regions
    )
    
    answer = result["answer"]
    citations = result["citations"]
    
    # Check if answer contains specific numeric claims about regions/scores
    has_specific_claims = bool(re.search(r'\d+\s+(region|score)', answer, re.IGNORECASE))
    
    if has_specific_claims:
        # If answer makes factual claims, it MUST have citations
        # OR it should be the rejection message
        if "cannot support this claim" not in answer.lower():
            assert len(citations) > 0, f"Answer makes factual claims but has no citations: {answer}"
    
    # All citations must be valid
    for citation in citations:
        assert len(citation["snippet"]) > 0
        assert len(citation["snippet"]) <= 500


def test_region_based_answers_have_citations():
    """Test that region-based answers always include citations."""
    from medlinker_ai.models import RegionSummary
    
    facilities = []
    
    # Create regions with high desert scores
    high_desert_regions = [
        RegionSummary(
            country="GH",
            region="Northern",
            total_facilities=5,
            facilities_analyzed=5,
            status_counts={"VERIFIED": 2, "INCOMPLETE": 3},
            verified_count=2,
            suspicious_count=0,
            incomplete_count=3,
            desert_score=85,
            missing_critical=["service:c-section", "service:emergency"],
            coverage={
                "services": {"surgery": 2},
                "equipment": {},
                "staffing": {"doctor": 3}
            },
            supporting_facility_ids=["FAC001", "FAC002"],
            trace_id="test_trace"
        )
    ]
    
    result = answer_planner_question(
        "Which regions lack C-section capability?",
        facilities,
        high_desert_regions
    )
    
    answer = result["answer"]
    citations = result["citations"]
    
    # If answer mentions specific regions with scores, must have citations
    if "85" in answer or ("northern" in answer.lower() and "score" in answer.lower()):
        if "cannot support" not in answer.lower():
            assert len(citations) > 0, "Region-based answer must have citations"
            
            # Check that citations reference regions
            has_region_citation = any(
                c["field"] == "region_summary" for c in citations
            )
            assert has_region_citation, "Must have at least one region citation"


def test_no_unsupported_factual_claims():
    """Test that system never returns unsupported factual claims."""
    from medlinker_ai.models import RegionSummary
    import re
    
    # Create test data
    regions = [
        RegionSummary(
            country="GH",
            region="Test",
            total_facilities=1,
            facilities_analyzed=1,
            status_counts={"VERIFIED": 1},
            verified_count=1,
            suspicious_count=0,
            incomplete_count=0,
            desert_score=50,
            missing_critical=[],
            coverage={"services": {}, "equipment": {}, "staffing": {}},
            supporting_facility_ids=["FAC001"],
            trace_id="test"
        )
    ]
    
    result = answer_planner_question(
        "What is the average desert score?",
        [],
        regions
    )
    
    answer = result["answer"]
    citations = result["citations"]
    
    # Check for factual claims
    has_numbers = bool(re.search(r'\d+', answer))
    
    if has_numbers and "cannot support" not in answer.lower():
        # Must have citations
        assert len(citations) > 0, "Numeric claims require citations"
