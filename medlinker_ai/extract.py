"""Capability extraction logic for MedLinker AI with strict validation."""

import json
from typing import Optional

from pydantic import ValidationError

from medlinker_ai.models import (
    FacilityDocInput,
    CapabilitySchemaV0,
    Citation,
)
from medlinker_ai.llm import get_llm_client
from medlinker_ai.llm.fallback import FallbackClient
from medlinker_ai.prompts import build_gemini_prompt, build_retry_prompt
from medlinker_ai.trace import log_span


def verify_citation_snippets(
    citations: list[Citation],
    source_text: str
) -> list[Citation]:
    """Verify that citation snippets exist in source text.
    
    Args:
        citations: List of citations to verify
        source_text: Original source text
        
    Returns:
        List of verified citations (invalid ones removed)
    """
    verified = []
    for citation in citations:
        # Check if snippet is a substring of source text
        if citation.snippet in source_text:
            verified.append(citation)
    return verified


def validate_extraction_output(
    response_data: dict,
    source_text: str,
    source_id: str
) -> tuple[CapabilitySchemaV0, list[Citation]]:
    """Validate extraction output with strict rules.
    
    Args:
        response_data: Parsed JSON response
        source_text: Original source text for citation verification
        source_id: Source document ID
        
    Returns:
        Tuple of (capabilities, citations)
        
    Raises:
        ValueError: If validation fails
    """
    # Check required keys
    if "extracted_capabilities" not in response_data:
        raise ValueError("Response missing 'extracted_capabilities' key")
    if "citations" not in response_data:
        raise ValueError("Response missing 'citations' key")
    
    # Parse with Pydantic
    try:
        capabilities = CapabilitySchemaV0(**response_data["extracted_capabilities"])
    except ValidationError as e:
        raise ValueError(f"Invalid extracted_capabilities schema: {e}")
    
    try:
        citations = [Citation(**c) for c in response_data["citations"]]
    except ValidationError as e:
        raise ValueError(f"Invalid citation schema: {e}")
    
    # Verify citation fields are valid
    valid_fields = {
        "services", "equipment", "staffing", "hours",
        "referral_capacity", "emergency_capability"
    }
    for citation in citations:
        if citation.field not in valid_fields and not citation.field.startswith("flag:"):
            raise ValueError(
                f"Invalid citation field: {citation.field}. "
                f"Must be one of: {valid_fields}"
            )
    
    # Verify citation snippets exist in source text
    verified_citations = verify_citation_snippets(citations, source_text)
    
    if len(verified_citations) < len(citations):
        discarded = len(citations) - len(verified_citations)
        # If all citations were invalid, treat as validation failure
        if len(verified_citations) == 0 and len(citations) > 0:
            raise ValueError(
                f"All {len(citations)} citations contained hallucinated snippets "
                "not found in source text"
            )
    
    # Check if capabilities extracted but no citations
    has_capabilities = (
        len(capabilities.services) > 0 or
        len(capabilities.equipment) > 0 or
        len(capabilities.staffing) > 0 or
        capabilities.hours is not None or
        capabilities.referral_capacity != "UNKNOWN" or
        capabilities.emergency_capability != "UNKNOWN"
    )
    
    if has_capabilities and len(verified_citations) == 0:
        raise ValueError(
            "Extracted capabilities but provided no valid citations"
        )
    
    return capabilities, verified_citations


def extract_capabilities(
    doc: FacilityDocInput,
    llm_provider: Optional[str] = None,
    trace_id: Optional[str] = None
) -> tuple[CapabilitySchemaV0, list[Citation]]:
    """Extract capabilities from facility document with strict validation.
    
    Args:
        doc: Input facility document.
        llm_provider: Optional LLM provider override ("gemini", "openai", "none").
        trace_id: Optional trace ID for logging
        
    Returns:
        Tuple of (extracted capabilities, citations list).
        
    Raises:
        ValueError: If extraction fails after retry.
    """
    # Get LLM client
    client = get_llm_client(llm_provider)
    
    # If using fallback, skip strict validation
    if isinstance(client, FallbackClient):
        response_text = client.extract(doc.source_text)
        response_data = json.loads(response_text)
        capabilities = CapabilitySchemaV0(**response_data["extracted_capabilities"])
        citations = [Citation(**c) for c in response_data["citations"]]
        
        # Log trace span
        if trace_id:
            log_span(
                trace_id=trace_id,
                step_name="extract",
                inputs_summary={
                    "facility_id": doc.facility_id,
                    "source_id": doc.source_id,
                    "source_type": doc.source_type
                },
                outputs_summary={
                    "services_count": len(capabilities.services),
                    "equipment_count": len(capabilities.equipment),
                    "staffing_count": len(capabilities.staffing)
                },
                evidence_refs=len(citations)
            )
        
        return capabilities, citations
    
    # Build strict prompt for LLM
    prompt = build_gemini_prompt(
        facility_id=doc.facility_id,
        facility_name=doc.facility_name,
        country=doc.country,
        region=doc.region,
        source_id=doc.source_id,
        source_url=doc.source_url or "",
        source_text=doc.source_text
    )
    
    # First attempt
    try:
        response_text = client.extract(prompt)
        
        # Parse JSON
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        # Validate with strict rules
        capabilities, citations = validate_extraction_output(
            response_data, doc.source_text, doc.source_id
        )
        
        # Log trace span
        if trace_id:
            log_span(
                trace_id=trace_id,
                step_name="extract",
                inputs_summary={
                    "facility_id": doc.facility_id,
                    "source_id": doc.source_id,
                    "source_type": doc.source_type
                },
                outputs_summary={
                    "services_count": len(capabilities.services),
                    "equipment_count": len(capabilities.equipment),
                    "staffing_count": len(capabilities.staffing)
                },
                evidence_refs=len(citations)
            )
        
        return capabilities, citations
        
    except (ValueError, ValidationError) as first_error:
        # Retry once with error details
        error_details = str(first_error)
        retry_prompt = build_retry_prompt(
            error_details=error_details,
            source_id=doc.source_id,
            source_url=doc.source_url or ""
        )
        
        try:
            response_text = client.extract(retry_prompt)
            
            # Parse JSON
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Retry failed - Invalid JSON: {e}")
            
            # Validate with strict rules
            capabilities, citations = validate_extraction_output(
                response_data, doc.source_text, doc.source_id
            )
            
            return capabilities, citations
            
        except (ValueError, ValidationError) as retry_error:
            # Both attempts failed - fall back to offline extractor
            fallback_client = FallbackClient()
            response_text = fallback_client.extract(doc.source_text)
            response_data = json.loads(response_text)
            capabilities = CapabilitySchemaV0(**response_data["extracted_capabilities"])
            citations = [Citation(**c) for c in response_data["citations"]]
            return capabilities, citations
