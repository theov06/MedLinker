"""Planner Q&A with grounded answers and citations."""

import re
import json
import os
from typing import List, Dict, Tuple, Optional

from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary, Citation
from medlinker_ai.utils import generate_trace_id
from medlinker_ai.llm import get_llm_client
from medlinker_ai.llm.fallback import FallbackClient
from medlinker_ai.trace import start_trace, log_span, end_trace
from medlinker_ai.mlflow_utils import (
    start_mlflow_run,
    end_mlflow_run,
    log_params,
    log_metrics,
    set_tags
)


def keyword_match_score(query: str, text: str) -> int:
    """Compute simple keyword match score.
    
    Args:
        query: Search query
        text: Text to search in
        
    Returns:
        Number of query keywords found in text
    """
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Extract keywords (words 3+ chars)
    keywords = [w for w in re.findall(r'\b\w+\b', query_lower) if len(w) >= 3]
    
    score = 0
    for keyword in keywords:
        if keyword in text_lower:
            score += 1
    
    return score


def build_facility_search_text(facility: FacilityAnalysisOutput) -> str:
    """Build searchable text from facility output.
    
    Args:
        facility: Facility analysis output
        
    Returns:
        Concatenated searchable text
    """
    parts = [
        facility.facility_name,  # Use name instead of ID
        facility.facility_id,
        facility.status,
        " ".join(facility.extracted_capabilities.services),
        " ".join(facility.extracted_capabilities.equipment),
        " ".join(facility.extracted_capabilities.staffing),
        " ".join(facility.reasons)
    ]
    return " ".join(parts)


def build_region_search_text(region: RegionSummary) -> str:
    """Build searchable text from region summary.
    
    Args:
        region: Region summary
        
    Returns:
        Concatenated searchable text
    """
    parts = [
        region.country,
        region.region,
        f"desert_score_{region.desert_score}",
        " ".join(region.missing_critical),
        " ".join(region.coverage.get("services", {}).keys()),
        " ".join(region.coverage.get("equipment", {}).keys()),
        " ".join(region.coverage.get("staffing", {}).keys())
    ]
    return " ".join(parts)


def retrieve_context(
    question: str,
    facilities: List[FacilityAnalysisOutput],
    regions: List[RegionSummary],
    k: int = 8
) -> Dict[str, List]:
    """Retrieve relevant facilities and regions for question.
    
    Uses RAG (FAISS) if enabled and available, otherwise falls back to keyword matching.
    
    Args:
        question: User question
        facilities: List of facility outputs
        regions: List of region summaries
        k: Number of items to retrieve
        
    Returns:
        Dictionary with selected_facilities and selected_regions
    """
    # Try RAG retrieval first (if enabled)
    try:
        from medlinker_ai.rag import is_rag_available, retrieve as rag_retrieve
        
        if is_rag_available():
            result = rag_retrieve(question, k_fac=k, k_reg=k)
            if result is not None:
                facility_ids, region_keys = result
                
                # Filter to retrieved IDs
                selected_facilities = [f for f in facilities if f.facility_id in facility_ids]
                selected_regions = [r for r in regions if f"{r.country}-{r.region}" in region_keys]
                
                # If we got results, return them
                if selected_facilities or selected_regions:
                    return {
                        "selected_facilities": selected_facilities[:k],
                        "selected_regions": selected_regions[:k]
                    }
    except Exception:
        # RAG failed, fall back to keyword matching
        pass
    
    # Fallback: keyword-based retrieval (current behavior)
    # Score facilities
    facility_scores = []
    for facility in facilities:
        search_text = build_facility_search_text(facility)
        score = keyword_match_score(question, search_text)
        facility_scores.append((score, facility))
    
    # Score regions
    region_scores = []
    for region in regions:
        search_text = build_region_search_text(region)
        score = keyword_match_score(question, search_text)
        region_scores.append((score, region))
    
    # Sort and select top k
    facility_scores.sort(key=lambda x: x[0], reverse=True)
    region_scores.sort(key=lambda x: x[0], reverse=True)
    
    selected_facilities = [f for _, f in facility_scores[:k]]
    selected_regions = [r for _, r in region_scores[:k]]
    
    return {
        "selected_facilities": selected_facilities,
        "selected_regions": selected_regions
    }


def detect_question_intent(question: str) -> str:
    """Detect question intent from keywords.
    
    Args:
        question: User question
        
    Returns:
        Intent type: desert_ranking, desert, suspicious, incomplete, verified, all_facilities, capability, general
    """
    question_lower = question.lower()
    
    # Check for ranking queries first (top/highest/worst/rank)
    if any(kw in question_lower for kw in ["top", "highest", "worst", "rank", "most"]) and \
       any(kw in question_lower for kw in ["desert", "score"]):
        return "desert_ranking"
    elif "all facilities" in question_lower or "list facilities" in question_lower or "show facilities" in question_lower or "show me all" in question_lower:
        return "all_facilities"
    elif "verified" in question_lower:
        return "verified"
    elif any(kw in question_lower for kw in ["lack", "missing", "desert", "gap", "shortage"]):
        return "desert"
    elif any(kw in question_lower for kw in ["suspicious", "inconsistent", "contradiction"]):
        return "suspicious"
    elif any(kw in question_lower for kw in ["incomplete", "partial", "missing data"]):
        return "incomplete"
    elif any(kw in question_lower for kw in ["where", "which", "find", "has", "available", "offer", "provide", "what facilities"]):
        return "capability"
    else:
        return "general"


def generate_fallback_answer(
    question: str,
    selected_facilities: List[FacilityAnalysisOutput],
    selected_regions: List[RegionSummary]
) -> Tuple[str, List[Citation]]:
    """Generate deterministic answer without LLM.
    
    Args:
        question: User question
        selected_facilities: Retrieved facilities
        selected_regions: Retrieved regions
        
    Returns:
        Tuple of (answer text, citations)
    """
    intent = detect_question_intent(question)
    citations = []
    
    if intent == "desert_ranking":
        # Ranking query - show top N regions by desert score
        # Extract number if present (e.g., "top 3", "top 5")
        match = re.search(r'top\s+(\d+)', question.lower())
        limit = int(match.group(1)) if match else 5
        
        # Sort all regions by desert score (highest first)
        sorted_regions = sorted(selected_regions, key=lambda r: r.desert_score, reverse=True)
        top_regions = sorted_regions[:limit]
        
        if not top_regions:
            answer = "No regional data available."
        else:
            answer = f"Top {len(top_regions)} regions by desert score:\n\n"
            for i, region in enumerate(top_regions, 1):
                severity = "high" if region.desert_score >= 50 else "moderate" if region.desert_score >= 30 else "low"
                answer += f"{i}. {region.country}-{region.region}: Desert score {region.desert_score} ({severity})\n"
                if region.missing_critical:
                    answer += f"   Missing: {', '.join(region.missing_critical[:3])}\n"
                
                # Create citation for each region
                snippet = f"Region: {region.country}-{region.region}; desert_score: {region.desert_score}; missing_critical: {', '.join(region.missing_critical[:5])}"
                if len(snippet) > 500:
                    snippet = snippet[:497] + "..."
                
                citations.append(Citation(
                    source_id="regions_aggregate",
                    snippet=snippet,
                    field="region_summary"
                ))
    
    elif intent == "desert":
        # Medical desert query
        high_deserts = [r for r in selected_regions if r.desert_score >= 50]
        
        if not high_deserts:
            # Check for moderate deserts
            moderate = [r for r in selected_regions if r.desert_score >= 30]
            if moderate:
                answer = f"No high-desert regions found (score ≥50). However, {len(moderate)} regions have moderate desert scores (30-49)."
                # Add citations for moderate deserts
                for region in moderate[:3]:
                    snippet = f"Region: {region.country}-{region.region}; desert_score: {region.desert_score}; missing_critical: {', '.join(region.missing_critical[:3])}"
                    if len(snippet) > 500:
                        snippet = snippet[:497] + "..."
                    citations.append(Citation(
                        source_id="regions_aggregate",
                        snippet=snippet,
                        field="region_summary"
                    ))
            else:
                answer = "No high-desert or moderate-desert regions found in the available data."
                # Add citation for first region to show data exists
                if selected_regions:
                    region = selected_regions[0]
                    snippet = f"Region: {region.country}-{region.region}; desert_score: {region.desert_score}"
                    citations.append(Citation(
                        source_id="regions_aggregate",
                        snippet=snippet,
                        field="region_summary"
                    ))
        else:
            answer = f"Found {len(high_deserts)} high-desert regions (score ≥50):\n\n"
            for i, region in enumerate(high_deserts[:5], 1):
                answer += f"{i}. {region.country}-{region.region}: Desert score {region.desert_score}\n"
                answer += f"   Missing: {', '.join(region.missing_critical[:3])}\n"
                
                # Create citation for each region mentioned
                snippet = f"Region: {region.country}-{region.region}; desert_score: {region.desert_score}; missing_critical: {', '.join(region.missing_critical[:5])}"
                if len(snippet) > 500:
                    snippet = snippet[:497] + "..."
                
                citations.append(Citation(
                    source_id="regions_aggregate",
                    snippet=snippet,
                    field="region_summary"
                ))
    
    elif intent == "suspicious":
        # Suspicious facilities query
        suspicious = [f for f in selected_facilities if f.status == "SUSPICIOUS"]
        
        if not suspicious:
            answer = "No suspicious facilities found in the available data."
            # Add citation from first facility to show data exists
            if selected_facilities:
                facility = selected_facilities[0]
                if facility.citations:
                    citations.append(facility.citations[0])
        else:
            answer = f"Found {len(suspicious)} suspicious facilities:\n\n"
            for i, facility in enumerate(suspicious[:5], 1):
                location_str = f" ({facility.location})" if facility.location else ""
                answer += f"{i}. {facility.facility_name}{location_str}: {facility.reasons[0] if facility.reasons else 'No reason provided'}\n"
                
                # Reuse existing citations
                if facility.citations:
                    citations.extend(facility.citations[:2])
    
    elif intent == "incomplete":
        # Incomplete facilities query
        incomplete = [f for f in selected_facilities if f.status == "INCOMPLETE"]
        
        if not incomplete:
            answer = "No incomplete facilities found in the available data."
            # Add citation from first facility to show data exists
            if selected_facilities:
                facility = selected_facilities[0]
                if facility.citations:
                    citations.append(facility.citations[0])
        else:
            answer = f"Found {len(incomplete)} incomplete facilities:\n\n"
            for i, facility in enumerate(incomplete[:5], 1):
                location_str = f" ({facility.location})" if facility.location else ""
                answer += f"{i}. {facility.facility_name}{location_str}: {facility.reasons[0] if facility.reasons else 'No reason provided'}\n"
                
                # Reuse existing citations
                if facility.citations:
                    citations.extend(facility.citations[:2])
    
    elif intent == "verified":
        # Verified facilities query
        verified = [f for f in selected_facilities if f.status == "VERIFIED"]
        
        if not verified:
            answer = "No verified facilities found in the available data."
            # Add citation from first facility to show data exists
            if selected_facilities:
                facility = selected_facilities[0]
                if facility.citations:
                    citations.append(facility.citations[0])
        else:
            answer = f"Found {len(verified)} verified facilities:\n\n"
            for i, facility in enumerate(verified[:10], 1):
                caps = facility.extracted_capabilities
                location_str = f" ({facility.location})" if facility.location else ""
                answer += f"{i}. {facility.facility_name}{location_str}\n"
                
                # Add services if available
                if caps.services:
                    answer += f"   Services: {', '.join(caps.services[:3])}"
                    if len(caps.services) > 3:
                        answer += f" (+{len(caps.services) - 3} more)"
                    answer += "\n"
                
                # Add equipment if available
                if caps.equipment:
                    answer += f"   Equipment: {', '.join(caps.equipment[:3])}"
                    if len(caps.equipment) > 3:
                        answer += f" (+{len(caps.equipment) - 3} more)"
                    answer += "\n"
                
                answer += "\n"
                
                # Reuse existing citations
                if facility.citations:
                    citations.extend(facility.citations[:1])
    
    elif intent == "all_facilities":
        # All facilities query - show all regardless of status
        if not selected_facilities:
            answer = "No facilities found in the available data."
        else:
            # Group by status
            by_status = {}
            for facility in selected_facilities:
                status = facility.status
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(facility)
            
            answer = f"Found {len(selected_facilities)} facilities:\n\n"
            
            # Show each status group
            for status in ["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]:
                if status in by_status:
                    facilities_in_status = by_status[status]
                    answer += f"**{status}** ({len(facilities_in_status)} facilities):\n"
                    
                    for i, facility in enumerate(facilities_in_status[:10], 1):
                        caps = facility.extracted_capabilities
                        location_str = f" ({facility.location})" if facility.location else ""
                        answer += f"{i}. {facility.facility_name}{location_str}\n"
                        
                        # Add services if available
                        if caps.services:
                            answer += f"   Services: {', '.join(caps.services[:3])}"
                            if len(caps.services) > 3:
                                answer += f" (+{len(caps.services) - 3} more)"
                            answer += "\n"
                        
                        # Add equipment if available
                        if caps.equipment:
                            answer += f"   Equipment: {', '.join(caps.equipment[:3])}"
                            if len(caps.equipment) > 3:
                                answer += f" (+{len(caps.equipment) - 3} more)"
                            answer += "\n"
                        
                        # Reuse existing citations
                        if facility.citations:
                            citations.extend(facility.citations[:1])
                    
                    answer += "\n"
    
    elif intent == "capability":
        # Capability search query
        # Extract capability keywords
        capability_keywords = []
        for word in re.findall(r'\b\w+\b', question.lower()):
            if len(word) >= 4 and word not in ["where", "which", "find", "have", "with", "that"]:
                capability_keywords.append(word)
        
        matching_facilities = []
        for facility in selected_facilities:
            caps = facility.extracted_capabilities
            search_text = " ".join(caps.services + caps.equipment + caps.staffing).lower()
            
            if any(kw in search_text for kw in capability_keywords):
                matching_facilities.append(facility)
        
        if not matching_facilities:
            answer = f"No facilities found with the requested capabilities in the available data."
            # Add citation from first facility to show data exists
            if selected_facilities:
                facility = selected_facilities[0]
                if facility.citations:
                    citations.append(facility.citations[0])
        else:
            answer = f"Found {len(matching_facilities)} facilities with matching capabilities:\n\n"
            for i, facility in enumerate(matching_facilities[:5], 1):
                caps = facility.extracted_capabilities
                location_str = f" ({facility.location})" if facility.location else ""
                answer += f"{i}. {facility.facility_name}{location_str}\n"
                answer += f"   Services: {', '.join(caps.services[:3])}\n"
                answer += f"   Equipment: {', '.join(caps.equipment[:3])}\n"
                
                # Reuse existing citations
                if facility.citations:
                    citations.extend(facility.citations[:2])
    
    else:
        # General query
        answer = f"Based on the available data:\n\n"
        answer += f"- {len(selected_facilities)} facilities analyzed\n"
        answer += f"- {len(selected_regions)} regions covered\n\n"
        
        if selected_regions:
            avg_desert = sum(r.desert_score for r in selected_regions) / len(selected_regions)
            answer += f"Average desert score: {avg_desert:.1f}\n"
            
            # Add citations for regions used in calculation
            for region in selected_regions[:3]:
                snippet = f"Region: {region.country}-{region.region}; desert_score: {region.desert_score}"
                if len(snippet) > 500:
                    snippet = snippet[:497] + "..."
                citations.append(Citation(
                    source_id="regions_aggregate",
                    snippet=snippet,
                    field="region_summary"
                ))
        
        # Add citations from facilities if no regions
        if not citations and selected_facilities:
            for facility in selected_facilities[:3]:
                if facility.citations:
                    citations.extend(facility.citations[:1])
    
    return answer, citations


def answer_planner_question(
    question: str,
    facilities: List[FacilityAnalysisOutput],
    regions: List[RegionSummary],
    llm_provider: Optional[str] = None
) -> Dict[str, any]:
    """Answer planner question with grounded response and citations.
    
    Args:
        question: User question
        facilities: List of facility outputs
        regions: List of region summaries
        llm_provider: Optional LLM provider override
        
    Returns:
        Dictionary with answer, citations, and trace_id
    """
    # Start MLflow run for Q&A
    start_mlflow_run("planner_qa")
    
    # Log parameters
    log_params({
        "pipeline_version": "v0.6",
        "llm_provider": llm_provider or os.environ.get("LLM_PROVIDER", "none"),
        "question_length": len(question)
    })
    
    # Generate trace ID and start trace
    trace_id = generate_trace_id()
    start_trace(trace_id)
    
    # Retrieve relevant context
    context = retrieve_context(question, facilities, regions, k=8)
    selected_facilities = context["selected_facilities"]
    selected_regions = context["selected_regions"]
    
    # Get LLM client
    client = get_llm_client(llm_provider)
    
    # Use fallback for deterministic answers
    if isinstance(client, FallbackClient) or llm_provider == "none":
        answer, citations = generate_fallback_answer(
            question, selected_facilities, selected_regions
        )
    else:
        # LLM-based answering (future enhancement)
        # For now, fall back to deterministic
        answer, citations = generate_fallback_answer(
            question, selected_facilities, selected_regions
        )
    
    # HARD GUARDRAIL: Enforce citations for factual claims
    if not citations:
        # Check if answer contains factual claims that need citations
        # Only reject if answer makes specific numeric or regional claims
        has_specific_numbers = bool(re.search(r'\d+\s+(region|facilit|score)', answer, re.IGNORECASE))
        has_desert_score = 'desert' in answer.lower() and 'score' in answer.lower()
        has_specific_region = bool(re.search(r'(region|country):\s*\w+', answer, re.IGNORECASE))
        
        needs_citations = has_specific_numbers or has_desert_score or has_specific_region
        
        if needs_citations:
            # Answer makes specific factual claims but has no citations - reject it
            answer = "I cannot support this claim with citations from the current dataset outputs."
            citations = []
    
    # Log answer span
    log_span(
        trace_id=trace_id,
        step_name="answer",
        inputs_summary={
            "question": question[:100],  # Truncate long questions
            "facilities_retrieved": len(selected_facilities),
            "regions_retrieved": len(selected_regions)
        },
        outputs_summary={
            "answer_length": len(answer),
            "citations_count": len(citations)
        },
        evidence_refs=len(citations)
    )
    
    # End trace
    end_trace(trace_id)
    
    # Log MLflow metrics
    log_metrics({
        "num_facilities": len(facilities),
        "num_regions": len(regions),
        "answer_length": len(answer),
        "citations_count": len(citations)
    })
    
    # Set tags
    intent = detect_question_intent(question)
    set_tags({
        "question_intent": intent,
        "trace_id": trace_id
    })
    
    # End MLflow run
    end_mlflow_run()
    
    return {
        "answer": answer,
        "citations": [c.model_dump() for c in citations],
        "trace_id": trace_id
    }
