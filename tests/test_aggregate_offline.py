"""Tests for regional aggregation (offline mode)."""

import os

# Force offline mode
os.environ["LLM_PROVIDER"] = "none"

from medlinker_ai.models import (
    FacilityAnalysisOutput,
    CapabilitySchemaV0,
    Citation,
    RegionSummary
)
from medlinker_ai.aggregate import (
    group_by_region,
    compute_coverage,
    compute_missing_critical,
    compute_desert_score,
    compute_region_summary,
    aggregate_regions
)
from medlinker_ai.normalize import normalize_and_map


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
        reasons=[],
        confidence="HIGH",
        citations=[],
        trace_id="test_trace"
    )



def test_group_by_region():
    """Test grouping facilities by region."""
    facilities = [
        create_test_facility("GH-ACC-001", [], [], []),
        create_test_facility("GH-ACC-002", [], [], []),
        create_test_facility("GH-ASH-001", [], [], []),
    ]
    
    grouped = group_by_region(facilities)
    
    assert len(grouped) == 2
    assert ("GH", "ACC") in grouped
    assert ("GH", "ASH") in grouped
    assert len(grouped[("GH", "ACC")]) == 2
    assert len(grouped[("GH", "ASH")]) == 1


def test_compute_coverage():
    """Test coverage computation."""
    facilities = [
        create_test_facility(
            "GH-ACC-001",
            services=["C-Section", "Emergency"],
            equipment=["Ultrasound", "X-ray"],
            staffing=["Midwife", "Doctor"]
        ),
        create_test_facility(
            "GH-ACC-002",
            services=["Cesarean", "Laboratory"],
            equipment=["X-ray"],
            staffing=["Doctor"]
        ),
    ]
    
    coverage = compute_coverage(facilities)
    
    # Check normalized counts
    assert coverage["services"]["c-section"] == 2  # C-Section + Cesarean
    assert coverage["services"]["emergency"] == 1
    assert coverage["services"]["laboratory"] == 1
    assert coverage["equipment"]["ultrasound"] == 1
    assert coverage["equipment"]["x-ray"] == 2
    assert coverage["staffing"]["midwife"] == 1
    assert coverage["staffing"]["doctor"] == 2


def test_normalize_synonyms():
    """Test that synonyms are normalized correctly."""
    assert normalize_and_map("Cesarean") == "c-section"
    assert normalize_and_map("caesarean") == "c-section"
    assert normalize_and_map("C Section") == "c-section"
    assert normalize_and_map("Accident & Emergency") == "emergency"
    assert normalize_and_map("ER") == "emergency"
    assert normalize_and_map("Xray") == "x-ray"
    assert normalize_and_map("Midwives") == "midwife"
    assert normalize_and_map("Doctors") == "doctor"


def test_compute_missing_critical():
    """Test identification of missing critical capabilities."""
    # Coverage with some missing items
    coverage = {
        "services": {"c-section": 1, "emergency": 1},  # Missing ultrasound, x-ray, laboratory
        "equipment": {"ultrasound": 1},  # Missing x-ray
        "staffing": {"doctor": 1}  # Missing midwife
    }
    
    missing = compute_missing_critical(coverage)
    
    assert "service:x-ray" in missing
    assert "service:laboratory" in missing
    assert "equipment:x-ray" in missing
    assert "staffing:midwife" in missing
    
    # Should not include items that are present
    assert "service:c-section" not in missing
    assert "service:emergency" not in missing
    assert "equipment:ultrasound" not in missing
    assert "staffing:doctor" not in missing



def test_compute_desert_score():
    """Test desert score computation."""
    # No missing items
    missing = []
    assert compute_desert_score(missing) == 0
    
    # One missing service (20 points)
    missing = ["service:c-section"]
    assert compute_desert_score(missing) == 20
    
    # One missing equipment (15 points)
    missing = ["equipment:x-ray"]
    assert compute_desert_score(missing) == 15
    
    # One missing staffing (10 points)
    missing = ["staffing:midwife"]
    assert compute_desert_score(missing) == 10
    
    # Multiple missing items
    missing = [
        "service:c-section",
        "service:emergency",
        "equipment:x-ray",
        "staffing:midwife"
    ]
    score = compute_desert_score(missing)
    assert score == 20 + 20 + 15 + 10  # 65
    
    # Score should be capped at 100
    missing = ["service:x"] * 10  # Would be 200 points
    score = compute_desert_score(missing)
    assert score <= 100


def test_compute_region_summary():
    """Test region summary computation."""
    facilities = [
        create_test_facility(
            "GH-ACC-001",
            services=["C-Section", "Emergency"],
            equipment=["Ultrasound"],
            staffing=["Midwife"],
            status="VERIFIED"
        ),
        create_test_facility(
            "GH-ACC-002",
            services=["Laboratory"],
            equipment=["X-ray"],
            staffing=["Doctor"],
            status="INCOMPLETE"
        ),
    ]
    
    summary = compute_region_summary("GH", "ACC", facilities)
    
    assert isinstance(summary, RegionSummary)
    assert summary.country == "GH"
    assert summary.region == "ACC"
    assert summary.total_facilities == 2
    assert summary.facilities_analyzed == 2
    assert summary.status_counts["VERIFIED"] == 1
    assert summary.status_counts["INCOMPLETE"] == 1
    assert summary.desert_score >= 0
    assert summary.desert_score <= 100
    assert summary.trace_id is not None


def test_aggregate_regions():
    """Test full regional aggregation."""
    facilities = [
        create_test_facility("GH-ACC-001", ["C-Section"], ["Ultrasound"], ["Midwife"]),
        create_test_facility("GH-ACC-002", ["Emergency"], ["X-ray"], ["Doctor"]),
        create_test_facility("GH-ASH-001", ["Laboratory"], [], []),
    ]
    
    summaries = aggregate_regions(facilities)
    
    assert len(summaries) == 2  # Two regions: ACC and ASH
    
    # Check that summaries are sorted by desert score (descending)
    for i in range(len(summaries) - 1):
        assert summaries[i].desert_score >= summaries[i+1].desert_score


def test_region_summary_validates():
    """Test that RegionSummary validates correctly."""
    summary = RegionSummary(
        country="GH",
        region="ACC",
        total_facilities=5,
        facilities_analyzed=5,
        status_counts={"VERIFIED": 3, "INCOMPLETE": 2},
        coverage={
            "services": {"c-section": 3, "emergency": 2},
            "equipment": {"ultrasound": 2},
            "staffing": {"midwife": 1, "doctor": 4}
        },
        missing_critical=["service:x-ray", "equipment:x-ray"],
        desert_score=35,
        supporting_facility_ids=["GH-ACC-001", "GH-ACC-002"],
        trace_id="test_trace_123"
    )
    
    assert summary.country == "GH"
    assert summary.region == "ACC"
    assert summary.desert_score == 35
    assert len(summary.missing_critical) == 2


def test_desert_score_in_range():
    """Test that desert score is always in valid range."""
    # Create facilities with varying coverage
    test_cases = [
        # Full coverage
        create_test_facility(
            "GH-001",
            services=["C-Section", "Emergency", "Ultrasound", "X-ray", "Laboratory"],
            equipment=["Ultrasound", "X-ray"],
            staffing=["Midwife", "Doctor"]
        ),
        # Partial coverage
        create_test_facility(
            "GH-002",
            services=["C-Section"],
            equipment=[],
            staffing=["Doctor"]
        ),
        # No coverage
        create_test_facility(
            "GH-003",
            services=[],
            equipment=[],
            staffing=[]
        ),
    ]
    
    for facility in test_cases:
        summary = compute_region_summary("GH", "TEST", [facility])
        assert 0 <= summary.desert_score <= 100
