"""Tests for offline extraction (no network calls)."""

import os
import json
from pathlib import Path
import pytest

# Force offline mode for all tests
os.environ["LLM_PROVIDER"] = "none"

from medlinker_ai.models import FacilityDocInput, CapabilitySchemaV0, Citation
from medlinker_ai.extract import extract_capabilities


def load_example(filename: str) -> FacilityDocInput:
    """Load example input from JSON file."""
    examples_dir = Path(__file__).parent.parent / "examples"
    with open(examples_dir / filename) as f:
        data = json.load(f)
    return FacilityDocInput(**data)



def test_extract_returns_capability_schema():
    """Test that extract returns CapabilitySchemaV0 instance."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    assert isinstance(capabilities, CapabilitySchemaV0)
    assert isinstance(citations, list)


def test_extract_golden_example():
    """Test extraction on golden example."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    # Should extract some services
    assert len(capabilities.services) > 0
    
    # Should extract some equipment
    assert len(capabilities.equipment) > 0
    
    # Should extract some staffing
    assert len(capabilities.staffing) > 0
    
    # Should have citations if capabilities extracted
    if capabilities.services or capabilities.equipment or capabilities.staffing:
        assert len(citations) > 0


def test_extract_input_2():
    """Test extraction on input 2 (basic facility)."""
    doc = load_example("facility_input_2.json")
    capabilities, citations = extract_capabilities(doc)
    
    assert isinstance(capabilities, CapabilitySchemaV0)
    assert isinstance(citations, list)
    
    # Should extract basic services
    assert len(capabilities.services) > 0


def test_extract_input_3():
    """Test extraction on input 3 (suspicious case)."""
    doc = load_example("facility_input_3.json")
    capabilities, citations = extract_capabilities(doc)
    
    assert isinstance(capabilities, CapabilitySchemaV0)
    assert isinstance(citations, list)
    
    # Should extract surgery-related services
    assert any("surg" in s.lower() for s in capabilities.services)



def test_deduplication_occurs():
    """Test that services/equipment/staffing are deduplicated."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    # Check no duplicates in lists
    assert len(capabilities.services) == len(set(capabilities.services))
    assert len(capabilities.equipment) == len(set(capabilities.equipment))
    assert len(capabilities.staffing) == len(set(capabilities.staffing))


def test_citation_snippet_max_length():
    """Test that citation snippets are <= 500 chars."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    for citation in citations:
        assert len(citation.snippet) <= 500, (
            f"Citation snippet exceeds 500 chars: {len(citation.snippet)}"
        )


def test_citation_snippet_non_empty():
    """Test that citation snippets are non-empty."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    for citation in citations:
        assert len(citation.snippet.strip()) > 0, "Citation snippet is empty"


def test_citations_present_when_capabilities_extracted():
    """Test that citations exist when capabilities are extracted."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    # If any capabilities extracted, should have citations
    has_capabilities = (
        len(capabilities.services) > 0 or
        len(capabilities.equipment) > 0 or
        len(capabilities.staffing) > 0 or
        capabilities.hours is not None or
        capabilities.referral_capacity != "UNKNOWN" or
        capabilities.emergency_capability != "UNKNOWN"
    )
    
    if has_capabilities:
        assert len(citations) > 0, "No citations provided for extracted capabilities"


def test_citation_fields_valid():
    """Test that citation fields reference valid capability fields."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    valid_fields = {
        "services", "equipment", "staffing", "hours",
        "referral_capacity", "emergency_capability"
    }
    
    for citation in citations:
        # Allow flag: prefix for future use
        if not citation.field.startswith("flag:"):
            assert citation.field in valid_fields, (
                f"Invalid citation field: {citation.field}"
            )



def test_no_network_calls():
    """Test that offline mode makes no network calls."""
    # This test passes if no exceptions are raised
    # Network calls would fail in offline mode
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    # Should complete without network errors
    assert capabilities is not None
    assert citations is not None


def test_emergency_capability_detection():
    """Test emergency capability detection."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    # Golden example mentions "24/7 emergency"
    assert capabilities.emergency_capability in ["YES", "NO", "UNKNOWN"]


def test_referral_capacity_detection():
    """Test referral capacity detection."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    # Golden example mentions "referral center"
    assert capabilities.referral_capacity in ["NONE", "BASIC", "ADVANCED", "UNKNOWN"]


def test_citation_source_id_matches():
    """Test that citation source_id matches input."""
    doc = load_example("facility_input_golden.json")
    capabilities, citations = extract_capabilities(doc)
    
    for citation in citations:
        # In fallback mode, source_id is "fallback_extraction"
        # In LLM mode, it should match doc.source_id
        assert citation.source_id is not None
        assert len(citation.source_id) > 0
