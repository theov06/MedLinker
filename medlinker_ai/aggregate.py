"""Regional aggregation and medical desert detection."""

from typing import Dict, List, Tuple
from collections import defaultdict

from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary
from medlinker_ai.config import (
    CRITICAL_SERVICES,
    CRITICAL_EQUIPMENT,
    CRITICAL_STAFFING,
    DESERT_SCORE_WEIGHTS,
    MAX_DESERT_SCORE
)
from medlinker_ai.normalize import normalize_and_map
from medlinker_ai.utils import generate_trace_id
from medlinker_ai.trace import log_span


def group_by_region(
    facility_outputs: List[FacilityAnalysisOutput]
) -> Dict[Tuple[str, str], List[FacilityAnalysisOutput]]:
    """Group facility outputs by (country, region).
    
    Args:
        facility_outputs: List of facility analysis outputs
        
    Returns:
        Dictionary mapping (country, region) to list of outputs
    """
    grouped = defaultdict(list)
    
    for output in facility_outputs:
        # Use region and country fields from the output
        country = output.country if hasattr(output, 'country') else "UNKNOWN"
        region = output.region if hasattr(output, 'region') else "UNKNOWN"
        
        grouped[(country, region)].append(output)
    
    return grouped


def compute_coverage(
    facilities: List[FacilityAnalysisOutput]
) -> Dict[str, Dict[str, int]]:
    """Compute coverage counts for services, equipment, and staffing.
    
    Args:
        facilities: List of facility outputs for a region
        
    Returns:
        Dictionary with coverage counts by category
    """
    coverage = {
        "services": defaultdict(int),
        "equipment": defaultdict(int),
        "staffing": defaultdict(int)
    }
    
    for facility in facilities:
        caps = facility.extracted_capabilities
        
        # Count services
        for service in caps.services:
            normalized = normalize_and_map(service)
            coverage["services"][normalized] += 1
        
        # Count equipment
        for equip in caps.equipment:
            normalized = normalize_and_map(equip)
            coverage["equipment"][normalized] += 1
        
        # Count staffing
        for staff in caps.staffing:
            normalized = normalize_and_map(staff)
            coverage["staffing"][normalized] += 1
    
    # Convert defaultdicts to regular dicts
    return {
        "services": dict(coverage["services"]),
        "equipment": dict(coverage["equipment"]),
        "staffing": dict(coverage["staffing"])
    }


def compute_missing_critical(
    coverage: Dict[str, Dict[str, int]]
) -> List[str]:
    """Identify critical capabilities missing in the region.
    
    Args:
        coverage: Coverage counts by category
        
    Returns:
        List of missing critical capability names
    """
    missing = []
    
    # Check critical services
    for service in CRITICAL_SERVICES:
        if coverage["services"].get(service, 0) == 0:
            missing.append(f"service:{service}")
    
    # Check critical equipment
    for equip in CRITICAL_EQUIPMENT:
        if coverage["equipment"].get(equip, 0) == 0:
            missing.append(f"equipment:{equip}")
    
    # Check critical staffing
    for staff in CRITICAL_STAFFING:
        if coverage["staffing"].get(staff, 0) == 0:
            missing.append(f"staffing:{staff}")
    
    return missing


def compute_desert_score(missing_critical: List[str]) -> int:
    """Compute medical desert score based on missing critical capabilities.
    
    Args:
        missing_critical: List of missing critical items
        
    Returns:
        Desert score (0-100)
    """
    score = 0
    
    # Count missing by category
    missing_services = sum(1 for m in missing_critical if m.startswith("service:"))
    missing_equipment = sum(1 for m in missing_critical if m.startswith("equipment:"))
    missing_staffing = sum(1 for m in missing_critical if m.startswith("staffing:"))
    
    # Add points for each missing item
    score += missing_services * DESERT_SCORE_WEIGHTS["service"]
    score += missing_equipment * DESERT_SCORE_WEIGHTS["equipment"]
    score += missing_staffing * DESERT_SCORE_WEIGHTS["staffing"]
    
    # Cap at maximum
    return min(score, MAX_DESERT_SCORE)


def get_supporting_facilities(
    facilities: List[FacilityAnalysisOutput],
    max_count: int = 5
) -> List[str]:
    """Get facility IDs that support the region's capabilities.
    
    Args:
        facilities: List of facility outputs
        max_count: Maximum number of facility IDs to return
        
    Returns:
        List of facility IDs (prioritize VERIFIED facilities)
    """
    # Prioritize VERIFIED facilities
    verified = [f for f in facilities if f.status == "VERIFIED"]
    
    if len(verified) >= max_count:
        return [f.facility_id for f in verified[:max_count]]
    
    # Add other facilities if needed
    all_facilities = verified + [f for f in facilities if f.status != "VERIFIED"]
    return [f.facility_id for f in all_facilities[:max_count]]


def compute_region_summary(
    country: str,
    region: str,
    facilities: List[FacilityAnalysisOutput],
    parent_trace_id: str = None
) -> RegionSummary:
    """Compute summary for a single region.
    
    Args:
        country: Country code
        region: Region code
        facilities: List of facility outputs for this region
        parent_trace_id: Optional parent trace ID
        
    Returns:
        RegionSummary with aggregated data
    """
    # Count statuses
    status_counts = defaultdict(int)
    for facility in facilities:
        status_counts[facility.status] += 1
    
    # Compute coverage
    coverage = compute_coverage(facilities)
    
    # Identify missing critical capabilities
    missing_critical = compute_missing_critical(coverage)
    
    # Compute desert score
    desert_score = compute_desert_score(missing_critical)
    
    # Get supporting facilities
    supporting_facility_ids = get_supporting_facilities(facilities)
    
    # Generate trace ID
    trace_id = generate_trace_id()
    
    # Log aggregation span if parent trace provided
    if parent_trace_id:
        log_span(
            trace_id=parent_trace_id,
            step_name="aggregate",
            inputs_summary={
                "country": country,
                "region": region,
                "facilities_count": len(facilities)
            },
            outputs_summary={
                "desert_score": desert_score,
                "missing_critical_count": len(missing_critical)
            },
            evidence_refs=len(facilities)
        )
    
    return RegionSummary(
        country=country,
        region=region,
        total_facilities=len(facilities),
        facilities_analyzed=len(facilities),
        status_counts=dict(status_counts),
        coverage=coverage,
        missing_critical=missing_critical,
        desert_score=desert_score,
        supporting_facility_ids=supporting_facility_ids,
        trace_id=trace_id
    )


def aggregate_regions(
    facility_outputs: List[FacilityAnalysisOutput],
    parent_trace_id: str = None
) -> List[RegionSummary]:
    """Aggregate facility outputs into regional summaries.
    
    Args:
        facility_outputs: List of facility analysis outputs
        parent_trace_id: Optional parent trace ID for logging
        
    Returns:
        List of RegionSummary objects, one per region
    """
    # Group by region
    grouped = group_by_region(facility_outputs)
    
    # Compute summary for each region
    summaries = []
    for (country, region), facilities in grouped.items():
        summary = compute_region_summary(country, region, facilities, parent_trace_id)
        summaries.append(summary)
    
    # Sort by desert score (descending) for easy identification of problem areas
    summaries.sort(key=lambda s: s.desert_score, reverse=True)
    
    return summaries
