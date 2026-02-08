"""Tests for MedLinker AI model validation."""

import json
from pathlib import Path
import pytest

from medlinker_ai.models import (
    FacilityDocInput,
    CapabilitySchemaV0,
    Citation,
    FacilityAnalysisOutput,
)


def load_json(filename: str) -> dict:
    """Load JSON file from examples directory."""
    examples_dir = Path(__file__).parent.parent / "examples"
    with open(examples_dir / filename, "r") as f:
        return json.load(f)


def test_golden_input_validates():
    """Test that golden input example parses correctly."""
    data = load_json("facility_input_golden.json")
    input_obj = FacilityDocInput(**data)
    
    assert input_obj.facility_id == "GH-ACC-001"
    assert input_obj.facility_name == "Korle Bu Teaching Hospital"
    assert input_obj.source_type == "website"
    assert len(input_obj.source_text) > 0


def test_golden_output_validates():
    """Test that golden output example parses correctly."""
    data = load_json("facility_output_expected_golden.json")
    output_obj = FacilityAnalysisOutput(**data)
    
    assert output_obj.facility_id == "GH-ACC-001"
    assert output_obj.status == "VERIFIED"
    assert output_obj.confidence == "HIGH"
    assert len(output_obj.citations) > 0
    assert len(output_obj.extracted_capabilities.services) > 0


def test_input_2_validates():
    """Test that input example 2 parses correctly."""
    data = load_json("facility_input_2.json")
    input_obj = FacilityDocInput(**data)
    
    assert input_obj.facility_id == "GH-ASH-042"
    assert input_obj.source_type == "dataset_row"
    assert input_obj.source_url is None


def test_input_3_validates():
    """Test that input example 3 parses correctly."""
    data = load_json("facility_input_3.json")
    input_obj = FacilityDocInput(**data)
    
    assert input_obj.facility_id == "GH-NTH-088"
    assert input_obj.source_type == "pdf"


def test_capability_deduplication():
    """Test that services/equipment/staffing lists are deduplicated."""
    capability = CapabilitySchemaV0(
        services=["Surgery", "Surgery", "Pediatrics", "Surgery"],
        equipment=["X-ray", "CT Scanner", "X-ray"],
        staffing=["Doctors", "Nurses", "Doctors", "Nurses"]
    )
    
    assert capability.services == ["Surgery", "Pediatrics"]
    assert capability.equipment == ["X-ray", "CT Scanner"]
    assert capability.staffing == ["Doctors", "Nurses"]


def test_capability_trimming():
    """Test that list items are trimmed of whitespace."""
    capability = CapabilitySchemaV0(
        services=["  Surgery  ", "Pediatrics", "  Emergency "],
        equipment=["X-ray  ", "  CT Scanner"],
        staffing=["  Doctors", "Nurses  "]
    )
    
    assert capability.services == ["Surgery", "Pediatrics", "Emergency"]
    assert capability.equipment == ["X-ray", "CT Scanner"]
    assert capability.staffing == ["Doctors", "Nurses"]


def test_capability_empty_string_filtering():
    """Test that empty strings are filtered out."""
    capability = CapabilitySchemaV0(
        services=["Surgery", "", "  ", "Pediatrics"],
        equipment=["", "X-ray"],
        staffing=["Doctors", "   ", ""]
    )
    
    assert capability.services == ["Surgery", "Pediatrics"]
    assert capability.equipment == ["X-ray"]
    assert capability.staffing == ["Doctors"]


def test_citation_snippet_trimming():
    """Test that citation snippets are trimmed."""
    citation = Citation(
        source_id="test_001",
        snippet="  This is a test snippet  ",
        field="services"
    )
    
    assert citation.snippet == "This is a test snippet"


def test_citation_char_range_validation():
    """Test that start_char < end_char validation works."""
    # Valid range
    citation = Citation(
        source_id="test_001",
        snippet="Test",
        field="services",
        start_char=10,
        end_char=20
    )
    assert citation.start_char == 10
    assert citation.end_char == 20
    
    # Invalid range should raise error
    with pytest.raises(ValueError, match="start_char must be"):
        Citation(
            source_id="test_001",
            snippet="Test",
            field="services",
            start_char=20,
            end_char=10
        )


def test_citation_snippet_max_length():
    """Test that citation snippet has max length constraint."""
    long_snippet = "x" * 501
    
    with pytest.raises(ValueError):
        Citation(
            source_id="test_001",
            snippet=long_snippet,
            field="services"
        )


def test_reasons_trimming():
    """Test that reasons are trimmed and empty ones filtered."""
    output = FacilityAnalysisOutput(
        facility_id="TEST-001",
        extracted_capabilities=CapabilitySchemaV0(),
        status="INCOMPLETE",
        reasons=["  Reason 1  ", "", "Reason 2", "   "],
        confidence="LOW",
        trace_id="test_trace"
    )
    
    assert output.reasons == ["Reason 1", "Reason 2"]


def test_default_values():
    """Test that default values are set correctly."""
    capability = CapabilitySchemaV0()
    
    assert capability.services == []
    assert capability.equipment == []
    assert capability.staffing == []
    assert capability.hours is None
    assert capability.referral_capacity == "UNKNOWN"
    assert capability.emergency_capability == "UNKNOWN"
    
    output = FacilityAnalysisOutput(
        facility_id="TEST-001",
        extracted_capabilities=capability,
        status="INCOMPLETE",
        confidence="LOW",
        trace_id="test_trace"
    )
    
    assert output.reasons == []
    assert output.citations == []
