"""Pydantic models for MedLinker AI data contracts."""

from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator

from medlinker_ai.constants import (
    SourceType,
    ReferralCapacityType,
    EmergencyCapabilityType,
    StatusType,
    ConfidenceType,
)


class FacilityDocInput(BaseModel):
    """Raw input document for a healthcare facility.
    
    This represents messy, unstructured text from various sources
    that needs to be extracted and verified.
    """
    facility_id: str
    facility_name: str
    country: str
    region: str
    source_id: str
    source_type: SourceType
    source_text: str
    source_url: Optional[str] = None
    timestamp: Optional[str] = None  # ISO 8601 format


class CapabilitySchemaV0(BaseModel):
    """Normalized structured facility capability fields.
    
    This schema represents the extracted and structured capabilities
    of a healthcare facility.
    """
    services: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    staffing: list[str] = Field(default_factory=list)
    hours: Optional[str] = None
    referral_capacity: ReferralCapacityType = "UNKNOWN"
    emergency_capability: EmergencyCapabilityType = "UNKNOWN"
    
    @field_validator("services", "equipment", "staffing")
    @classmethod
    def dedupe_and_trim(cls, v: list[str]) -> list[str]:
        """Deduplicate and trim list items."""
        if not v:
            return []
        # Trim whitespace and filter empty strings
        trimmed = [item.strip() for item in v if item and item.strip()]
        # Deduplicate while preserving order
        seen = set()
        result = []
        for item in trimmed:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result


class Citation(BaseModel):
    """Evidence snippet tied to a specific field or flag.
    
    Citations provide traceability from extracted data back to
    the source text that supports it.
    """
    source_id: str
    source_url: Optional[str] = None
    snippet: str = Field(..., min_length=1, max_length=500)
    field: str  # e.g., "services", "equipment", "flag:suspicious"
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    
    @field_validator("snippet")
    @classmethod
    def trim_snippet(cls, v: str) -> str:
        """Trim whitespace from snippet."""
        return v.strip()
    
    @field_validator("end_char")
    @classmethod
    def validate_char_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure start_char < end_char if both provided."""
        if v is not None and info.data.get("start_char") is not None:
            start = info.data["start_char"]
            if not (0 <= start < v):
                raise ValueError(
                    f"start_char must be >= 0 and < end_char, got start={start}, end={v}"
                )
        return v


class FacilityAnalysisOutput(BaseModel):
    """Final output for frontend consumption.
    
    This represents the complete analysis result including extracted
    capabilities, verification status, and supporting evidence.
    """
    facility_id: str
    extracted_capabilities: CapabilitySchemaV0
    status: StatusType
    reasons: list[str] = Field(default_factory=list)
    confidence: ConfidenceType
    citations: list[Citation] = Field(default_factory=list)
    trace_id: str
    
    @field_validator("reasons")
    @classmethod
    def trim_reasons(cls, v: list[str]) -> list[str]:
        """Trim and filter empty reason strings."""
        if not v:
            return []
        return [reason.strip() for reason in v if reason and reason.strip()]



class RegionSummary(BaseModel):
    """Regional aggregation summary with medical desert detection.
    
    This represents aggregated facility data for a geographic region,
    including coverage analysis and desert scoring.
    """
    country: str
    region: str
    total_facilities: int
    facilities_analyzed: int
    status_counts: Dict[str, int] = Field(default_factory=dict)
    coverage: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    missing_critical: list[str] = Field(default_factory=list)
    desert_score: int = Field(ge=0, le=100)
    supporting_facility_ids: list[str] = Field(default_factory=list)
    trace_id: str
