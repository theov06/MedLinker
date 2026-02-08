"""Tests for citation verification logic."""

from medlinker_ai.models import Citation
from medlinker_ai.extract import verify_citation_snippets


def test_verify_valid_citations():
    """Test that valid citations pass verification."""
    source_text = "The hospital has CT scanner and MRI machine. Emergency services available 24/7."
    
    citations = [
        Citation(
            source_id="test_001",
            snippet="CT scanner and MRI machine",
            field="equipment"
        ),
        Citation(
            source_id="test_001",
            snippet="Emergency services available 24/7",
            field="emergency_capability"
        )
    ]
    
    verified = verify_citation_snippets(citations, source_text)
    assert len(verified) == 2


def test_verify_rejects_hallucinated_citations():
    """Test that hallucinated citations are rejected."""
    source_text = "The hospital has CT scanner and MRI machine."
    
    citations = [
        Citation(
            source_id="test_001",
            snippet="CT scanner and MRI machine",
            field="equipment"
        ),
        Citation(
            source_id="test_001",
            snippet="X-ray equipment available",  # Not in source text
            field="equipment"
        )
    ]
    
    verified = verify_citation_snippets(citations, source_text)
    assert len(verified) == 1
    assert verified[0].snippet == "CT scanner and MRI machine"


def test_verify_all_hallucinated_returns_empty():
    """Test that all hallucinated citations returns empty list."""
    source_text = "The hospital has CT scanner."
    
    citations = [
        Citation(
            source_id="test_001",
            snippet="MRI machine available",  # Not in source
            field="equipment"
        ),
        Citation(
            source_id="test_001",
            snippet="X-ray equipment",  # Not in source
            field="equipment"
        )
    ]
    
    verified = verify_citation_snippets(citations, source_text)
    assert len(verified) == 0


def test_verify_case_sensitive():
    """Test that verification is case-sensitive."""
    source_text = "The hospital has CT scanner."
    
    citations = [
        Citation(
            source_id="test_001",
            snippet="CT scanner",  # Exact match
            field="equipment"
        ),
        Citation(
            source_id="test_001",
            snippet="ct scanner",  # Different case
            field="equipment"
        )
    ]
    
    verified = verify_citation_snippets(citations, source_text)
    # Only exact case match should pass
    assert len(verified) == 1
    assert verified[0].snippet == "CT scanner"


def test_verify_partial_match_fails():
    """Test that partial matches are rejected."""
    source_text = "The hospital has CT scanner equipment."
    
    citations = [
        Citation(
            source_id="test_001",
            snippet="CT scanner",  # Exact substring
            field="equipment"
        ),
        Citation(
            source_id="test_001",
            snippet="CT scanner machine",  # Not exact substring
            field="equipment"
        )
    ]
    
    verified = verify_citation_snippets(citations, source_text)
    assert len(verified) == 1
    assert verified[0].snippet == "CT scanner"
