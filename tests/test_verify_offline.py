"""Tests for verification logic (offline mode)."""

import os
import json
from pathlib import Path

# Force offline mode for all tests
os.environ["LLM_PROVIDER"] = "none"

from medlinker_ai.models import FacilityDocInput, FacilityAnalysisOutput
from medlinker_ai.verify import verify_facility


def load_example(filename: str) -> FacilityDocInput:
    """Load example input from JSON file."""
    examples_dir = Path(__file__).parent.parent / "examples"
    with open(examples_dir / filename) as f:
        data = json.load(f)
    return FacilityDocInput(**data)


def test_verify_returns_analysis_output():
    """Test that verify returns FacilityAnalysisOutput instance."""
    doc = load_example("facility_input_golden.json")
    analysis = verify_facility(doc)
    
    assert isinstance(analysis, FacilityAnalysisOutput)
    assert analysis.facility_id == doc.facility_id


def test_verify_golden_example():
    """Test verification on golden example (should be VERIFIED or INCOMPLETE)."""
    doc = load_example("facility_input_golden.json")
    analysis = verify_facility(doc)
    
    # Should have valid status
    assert analysis.status in ["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]
    
    # Should have capabilities
    assert len(analysis.extracted_capabilities.services) > 0
    
    # Should have citations
    assert len(analysis.citations) > 0
    
    # Should have trace_id
    assert analysis.trace_id is not None
    assert len(analysis.trace_id) > 0


def test_verify_input_2_incomplete():
    """Test verification on input 2 (basic facility, likely INCOMPLETE)."""
    doc = load_example("facility_input_2.json")
    analysis = verify_facility(doc)
    
    assert isinstance(analysis, FacilityAnalysisOutput)
    assert analysis.status in ["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]
    
    # If not VERIFIED, should have reasons
    if analysis.status != "VERIFIED":
        assert len(analysis.reasons) > 0


def test_verify_input_3_suspicious():
    """Test verification on input 3 (surgery without anesthesiologist, should be SUSPICIOUS)."""
    doc = load_example("facility_input_3.json")
    analysis = verify_facility(doc)
    
    assert isinstance(analysis, FacilityAnalysisOutput)
    
    # Should detect surgery without anesthesia issue
    assert analysis.status == "SUSPICIOUS"
    assert len(analysis.reasons) > 0
    
    # Should have reason about surgery/anesthesia
    assert any("surgical" in r.lower() or "surgery" in r.lower() for r in analysis.reasons)


def test_status_values_valid():
    """Test that status is always one of allowed values."""
    for filename in ["facility_input_golden.json", "facility_input_2.json", "facility_input_3.json"]:
        doc = load_example(filename)
        analysis = verify_facility(doc)
        
        assert analysis.status in ["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]


def test_reasons_non_empty_when_not_verified():
    """Test that reasons list is non-empty when status is not VERIFIED."""
    for filename in ["facility_input_golden.json", "facility_input_2.json", "facility_input_3.json"]:
        doc = load_example(filename)
        analysis = verify_facility(doc)
        
        if analysis.status != "VERIFIED":
            assert len(analysis.reasons) > 0, f"Status {analysis.status} but no reasons provided"


def test_flag_citations_for_reasons():
    """Test that reasons have supporting citations with flag: field."""
    doc = load_example("facility_input_3.json")
    analysis = verify_facility(doc)
    
    # Should have reasons (SUSPICIOUS)
    assert len(analysis.reasons) > 0
    
    # Should have flag citations
    flag_citations = [c for c in analysis.citations if c.field.startswith("flag:")]
    assert len(flag_citations) > 0, "Reasons provided but no flag citations found"


def test_citation_snippets_are_substrings():
    """Test that all citation snippets exist in source text."""
    doc = load_example("facility_input_golden.json")
    analysis = verify_facility(doc)
    
    for citation in analysis.citations:
        assert citation.snippet in doc.source_text, (
            f"Citation snippet not found in source text: {citation.snippet[:50]}..."
        )


def test_citation_snippets_max_length():
    """Test that all citation snippets are <= 500 chars."""
    for filename in ["facility_input_golden.json", "facility_input_2.json", "facility_input_3.json"]:
        doc = load_example(filename)
        analysis = verify_facility(doc)
        
        for citation in analysis.citations:
            assert len(citation.snippet) <= 500, (
                f"Citation snippet exceeds 500 chars: {len(citation.snippet)}"
            )


def test_confidence_values_valid():
    """Test that confidence is always one of allowed values."""
    for filename in ["facility_input_golden.json", "facility_input_2.json", "facility_input_3.json"]:
        doc = load_example(filename)
        analysis = verify_facility(doc)
        
        assert analysis.confidence in ["LOW", "MEDIUM", "HIGH"]


def test_confidence_matches_status():
    """Test that confidence generally matches status severity."""
    doc = load_example("facility_input_3.json")
    analysis = verify_facility(doc)
    
    # SUSPICIOUS should have LOW confidence
    if analysis.status == "SUSPICIOUS":
        assert analysis.confidence == "LOW"


def test_trace_id_generated():
    """Test that trace_id is always generated."""
    for filename in ["facility_input_golden.json", "facility_input_2.json", "facility_input_3.json"]:
        doc = load_example(filename)
        analysis = verify_facility(doc)
        
        assert analysis.trace_id is not None
        assert len(analysis.trace_id) > 0
        # Should be UUID format
        assert "-" in analysis.trace_id


def test_incomplete_hours_detection():
    """Test that missing hours triggers INCOMPLETE."""
    doc = load_example("facility_input_2.json")
    analysis = verify_facility(doc)
    
    # If hours are missing, should be flagged
    if analysis.extracted_capabilities.hours is None:
        assert any("hours" in r.lower() for r in analysis.reasons)


def test_suspicious_surgery_without_anesthesia():
    """Test that surgery without anesthesia triggers SUSPICIOUS."""
    doc = load_example("facility_input_3.json")
    analysis = verify_facility(doc)
    
    # Input 3 has surgery but no permanent anesthesiologist
    has_surgery = any(
        "surg" in s.lower() for s in analysis.extracted_capabilities.services
    )
    has_anesthesia = any(
        "anesthe" in s.lower() for s in analysis.extracted_capabilities.staffing
    )
    
    if has_surgery and not has_anesthesia:
        assert analysis.status == "SUSPICIOUS"
        assert any("anesthe" in r.lower() or "surgical" in r.lower() for r in analysis.reasons)
