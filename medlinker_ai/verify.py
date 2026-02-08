"""Verification logic for facility capability analysis."""

import re
from typing import Optional

from medlinker_ai.models import (
    FacilityDocInput,
    FacilityAnalysisOutput,
    CapabilitySchemaV0,
    Citation,
)
from medlinker_ai.extract import extract_capabilities
from medlinker_ai.utils import generate_trace_id
from medlinker_ai.trace import start_trace, log_span, end_trace


def find_evidence_snippet(
    source_text: str,
    keywords: list[str],
    max_length: int = 500
) -> Optional[str]:
    """Find evidence snippet in source text for given keywords.
    
    Args:
        source_text: Source text to search
        keywords: List of keywords to search for
        max_length: Maximum snippet length
        
    Returns:
        Evidence snippet or None if not found
    """
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        match = pattern.search(source_text)
        if match:
            # Extract context window around match
            start = max(0, match.start() - 100)
            end = min(len(source_text), match.end() + 100)
            snippet = source_text[start:end].strip()
            
            # Ensure snippet is <= max_length
            if len(snippet) > max_length:
                snippet = snippet[:max_length - 3] + "..."
            
            return snippet
    
    return None


def check_incomplete_rules(
    capabilities: CapabilitySchemaV0,
    source_text: str,
    source_id: str,
    extracted_citations: list[Citation]
) -> tuple[list[str], list[Citation]]:
    """Check for incomplete information.
    
    Args:
        capabilities: Extracted capabilities
        source_text: Original source text
        source_id: Source document ID
        extracted_citations: Citations from extraction
        
    Returns:
        Tuple of (reasons, citations)
    """
    reasons = []
    citations = []
    
    # Check hours
    if capabilities.hours is None or not capabilities.hours.strip():
        reason = "Hours not specified; availability is unclear."
        reasons.append(reason)
        
        # Try to find evidence or reuse existing citation
        hours_citation = next(
            (c for c in extracted_citations if c.field == "hours"),
            None
        )
        if hours_citation:
            citations.append(Citation(
                source_id=source_id,
                source_url=hours_citation.source_url,
                snippet=hours_citation.snippet,
                field="flag:incomplete"
            ))
        else:
            # Search for hours-related keywords
            snippet = find_evidence_snippet(
                source_text,
                ["hours", "open", "operating", "available", "schedule"]
            )
            if snippet:
                citations.append(Citation(
                    source_id=source_id,
                    snippet=snippet,
                    field="flag:incomplete"
                ))
    
    # Check staffing
    if len(capabilities.staffing) == 0:
        reason = "Staffing information is missing; capability claims cannot be fully trusted."
        reasons.append(reason)
        
        # Try to find evidence
        snippet = find_evidence_snippet(
            source_text,
            ["staff", "doctor", "nurse", "physician", "personnel"]
        )
        if snippet:
            citations.append(Citation(
                source_id=source_id,
                snippet=snippet,
                field="flag:incomplete"
            ))
    
    # Check referral capacity
    if capabilities.referral_capacity == "UNKNOWN":
        reason = "Referral capacity is not stated; transfer readiness is unclear."
        reasons.append(reason)
        
        # Try to find evidence or reuse existing citation
        referral_citation = next(
            (c for c in extracted_citations if c.field == "referral_capacity"),
            None
        )
        if referral_citation:
            citations.append(Citation(
                source_id=source_id,
                source_url=referral_citation.source_url,
                snippet=referral_citation.snippet,
                field="flag:incomplete"
            ))
        else:
            snippet = find_evidence_snippet(
                source_text,
                ["referral", "refer", "transfer", "tertiary"]
            )
            if snippet:
                citations.append(Citation(
                    source_id=source_id,
                    snippet=snippet,
                    field="flag:incomplete"
                ))
    
    return reasons, citations


def check_suspicious_rules(
    capabilities: CapabilitySchemaV0,
    source_text: str,
    source_id: str,
    extracted_citations: list[Citation]
) -> tuple[list[str], list[Citation]]:
    """Check for suspicious inconsistencies.
    
    Args:
        capabilities: Extracted capabilities
        source_text: Original source text
        source_id: Source document ID
        extracted_citations: Citations from extraction
        
    Returns:
        Tuple of (reasons, citations)
    """
    reasons = []
    citations = []
    
    # Check surgery without anesthesia
    surgical_keywords = [
        "surgery", "surgical", "cesarean", "c-section", 
        "caesarean", "operating theatre", "operative"
    ]
    has_surgery = any(
        any(keyword in service.lower() for keyword in surgical_keywords)
        for service in capabilities.services
    )
    
    if has_surgery:
        has_anesthesia = any(
            "anesthe" in staff.lower() or "anaesthe" in staff.lower()
            for staff in capabilities.staffing
        )
        
        # Also check for negative mentions in source text
        negative_anesthesia_patterns = [
            "no anesthesiologist", "no anaesthesiologist",
            "no anesthetist", "no anaesthetist",
            "without anesthesiologist", "without anaesthesiologist",
            "lacking anesthesiologist", "lacking anaesthesiologist"
        ]
        has_negative_mention = any(
            pattern in source_text.lower() for pattern in negative_anesthesia_patterns
        )
        
        if not has_anesthesia or has_negative_mention:
            reason = "Surgical services are claimed but anesthesia staffing is not mentioned; claim may be incomplete or inconsistent."
            reasons.append(reason)
            
            # Find surgery citation
            surgery_citation = next(
                (c for c in extracted_citations 
                 if c.field == "services" and any(kw in c.snippet.lower() for kw in surgical_keywords)),
                None
            )
            if surgery_citation:
                citations.append(Citation(
                    source_id=source_id,
                    source_url=surgery_citation.source_url,
                    snippet=surgery_citation.snippet,
                    field="flag:suspicious"
                ))
            else:
                # Search for surgery mention
                snippet = find_evidence_snippet(
                    source_text,
                    surgical_keywords
                )
                if snippet:
                    citations.append(Citation(
                        source_id=source_id,
                        snippet=snippet,
                        field="flag:suspicious"
                    ))
    
    # Check emergency without hours
    if capabilities.emergency_capability == "YES":
        if capabilities.hours is None or not capabilities.hours.strip():
            reason = "Emergency capability is claimed but operating hours are not specified; claim may be inconsistent."
            reasons.append(reason)
            
            # Find emergency citation
            emergency_citation = next(
                (c for c in extracted_citations if c.field == "emergency_capability"),
                None
            )
            if emergency_citation:
                citations.append(Citation(
                    source_id=source_id,
                    source_url=emergency_citation.source_url,
                    snippet=emergency_citation.snippet,
                    field="flag:suspicious"
                ))
            else:
                snippet = find_evidence_snippet(
                    source_text,
                    ["emergency", "ER", "accident", "24/7"]
                )
                if snippet:
                    citations.append(Citation(
                        source_id=source_id,
                        snippet=snippet,
                        field="flag:suspicious"
                    ))
    
    # Check advanced equipment without staffing
    advanced_equipment_keywords = ["ct", "mri", "ventilator"]
    has_advanced_equipment = any(
        any(keyword in equip.lower() for keyword in advanced_equipment_keywords)
        for equip in capabilities.equipment
    )
    
    if has_advanced_equipment and len(capabilities.staffing) == 0:
        reason = "Advanced equipment is listed but staffing is not provided; claim may be incomplete."
        reasons.append(reason)
        
        # Find equipment citation
        equipment_citation = next(
            (c for c in extracted_citations 
             if c.field == "equipment" and any(kw in c.snippet.lower() for kw in advanced_equipment_keywords)),
            None
        )
        if equipment_citation:
            citations.append(Citation(
                source_id=source_id,
                source_url=equipment_citation.source_url,
                snippet=equipment_citation.snippet,
                field="flag:suspicious"
            ))
        else:
            snippet = find_evidence_snippet(
                source_text,
                advanced_equipment_keywords
            )
            if snippet:
                citations.append(Citation(
                    source_id=source_id,
                    snippet=snippet,
                    field="flag:suspicious"
                ))
    
    return reasons, citations


def calculate_confidence(
    status: str,
    citation_count: int
) -> str:
    """Calculate confidence level based on status and evidence.
    
    Args:
        status: Verification status
        citation_count: Total number of citations
        
    Returns:
        Confidence level: LOW, MEDIUM, or HIGH
    """
    # Start at HIGH
    confidence = "HIGH"
    
    # Adjust based on status
    if status == "INCOMPLETE":
        confidence = "MEDIUM"
    elif status == "SUSPICIOUS":
        confidence = "LOW"
    
    # Reduce if insufficient citations
    if citation_count < 2:
        if confidence == "HIGH":
            confidence = "MEDIUM"
        elif confidence == "MEDIUM":
            confidence = "LOW"
    
    return confidence


def verify_facility(
    doc: FacilityDocInput,
    llm_provider: Optional[str] = None
) -> FacilityAnalysisOutput:
    """Verify facility capabilities and detect inconsistencies.
    
    Args:
        doc: Input facility document
        llm_provider: Optional LLM provider override
        
    Returns:
        Complete facility analysis with verification status
    """
    # Generate trace ID and start trace
    trace_id = generate_trace_id()
    start_trace(trace_id)
    
    # Phase 1: Extract capabilities
    capabilities, extracted_citations = extract_capabilities(doc, llm_provider, trace_id=trace_id)
    
    # Phase 2: Run verification checks
    incomplete_reasons, incomplete_citations = check_incomplete_rules(
        capabilities, doc.source_text, doc.source_id, extracted_citations
    )
    
    suspicious_reasons, suspicious_citations = check_suspicious_rules(
        capabilities, doc.source_text, doc.source_id, extracted_citations
    )
    
    # Determine status
    if len(suspicious_reasons) > 0:
        status = "SUSPICIOUS"
        reasons = suspicious_reasons + incomplete_reasons
    elif len(incomplete_reasons) > 0:
        status = "INCOMPLETE"
        reasons = incomplete_reasons
    else:
        status = "VERIFIED"
        reasons = []
    
    # Merge all citations
    all_citations = extracted_citations + incomplete_citations + suspicious_citations
    
    # Calculate confidence
    confidence = calculate_confidence(status, len(all_citations))
    
    # Log verification span
    log_span(
        trace_id=trace_id,
        step_name="verify",
        inputs_summary={
            "facility_id": doc.facility_id
        },
        outputs_summary={
            "status": status,
            "reasons_count": len(reasons),
            "confidence": confidence
        },
        evidence_refs=len(all_citations)
    )
    
    # End trace
    end_trace(trace_id)
    
    return FacilityAnalysisOutput(
        facility_id=doc.facility_id,
        extracted_capabilities=capabilities,
        status=status,
        reasons=reasons,
        confidence=confidence,
        citations=all_citations,
        trace_id=trace_id
    )
