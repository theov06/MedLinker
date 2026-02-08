"""FastAPI backend for MedLinker AI."""

import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from medlinker_ai.models import (
    FacilityAnalysisOutput,
    RegionSummary,
    Citation,
)
from medlinker_ai.qa import answer_planner_question
from medlinker_ai.trace import get_trace, TraceRun


# Initialize FastAPI app
app = FastAPI(
    title="MedLinker AI",
    description="Healthcare facility capability extraction and medical desert detection API",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AskRequest(BaseModel):
    """Request model for Q&A endpoint."""
    question: str


class AskResponse(BaseModel):
    """Response model for Q&A endpoint."""
    answer: str
    citations: List[Citation]
    trace_id: str


# Helper functions
def load_facilities() -> List[FacilityAnalysisOutput]:
    """Load facility outputs from file.
    
    Returns:
        List of facility analysis outputs
        
    Raises:
        HTTPException: If file not found or invalid
    """
    facilities_file = Path("./outputs/facilities.jsonl")
    
    if not facilities_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Facilities data not found. Run 'python -m medlinker_ai.cli run_dataset' first."
        )
    
    facilities = []
    try:
        with open(facilities_file, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    facilities.append(FacilityAnalysisOutput(**data))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading facilities: {str(e)}"
        )
    
    return facilities


def load_regions() -> List[RegionSummary]:
    """Load region summaries from file.
    
    Returns:
        List of region summaries
        
    Raises:
        HTTPException: If file not found or invalid
    """
    regions_file = Path("./outputs/regions.json")
    
    if not regions_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Regions data not found. Run 'python -m medlinker_ai.cli aggregate' first."
        )
    
    try:
        with open(regions_file, 'r') as f:
            regions_data = json.load(f)
            regions = [RegionSummary(**r) for r in regions_data]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading regions: {str(e)}"
        )
    
    return regions


# API Endpoints
@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "MedLinker AI",
        "version": "1.0.0",
        "description": "Healthcare facility capability extraction and medical desert detection API",
        "endpoints": {
            "facilities": "/facilities",
            "regions": "/regions",
            "ask": "/ask",
            "trace": "/trace/{trace_id}"
        }
    }


@app.get("/facilities", response_model=List[FacilityAnalysisOutput])
def get_facilities():
    """Get all facility analysis outputs.
    
    Returns:
        List of facility analysis outputs with extracted capabilities,
        verification status, and citations.
    """
    return load_facilities()


@app.get("/regions", response_model=List[RegionSummary])
def get_regions():
    """Get all regional summaries with medical desert scores.
    
    Returns:
        List of regional summaries with desert scores, missing capabilities,
        and coverage statistics.
    """
    return load_regions()


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Answer planner question using facility and region data.
    
    Args:
        request: Question request with question text
        
    Returns:
        Grounded answer with citations and trace ID
        
    Raises:
        HTTPException: If data not available or question invalid
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    # Load data
    try:
        facilities = load_facilities()
        regions = load_regions()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading data: {str(e)}"
        )
    
    # Answer question
    try:
        result = answer_planner_question(
            request.question,
            facilities,
            regions
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )
    
    return AskResponse(
        answer=result["answer"],
        citations=result["citations"],
        trace_id=result["trace_id"]
    )


@app.get("/trace/{trace_id}", response_model=TraceRun)
def get_trace_by_id(trace_id: str):
    """Get trace details by trace ID.
    
    Args:
        trace_id: Unique trace identifier
        
    Returns:
        Complete trace with all spans in chronological order
        
    Raises:
        HTTPException: If trace not found
    """
    trace = get_trace(trace_id)
    
    if not trace:
        raise HTTPException(
            status_code=404,
            detail=f"Trace not found: {trace_id}"
        )
    
    return trace


@app.get("/health")
def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy"}


@app.post("/demo/process_facility")
def demo_process_facility(facility_input: dict):
    """Demo endpoint: Process a single facility end-to-end with unified tracing.
    
    This endpoint demonstrates the complete pipeline with step-level tracing:
    1. Extract capabilities (extract span)
    2. Verify facility (verify span)
    3. Aggregate region (aggregate span)
    4. Answer question (answer span)
    
    Args:
        facility_input: FacilityDocInput as dict
        
    Returns:
        Complete analysis with unified trace_id showing all steps
    """
    from medlinker_ai.models import FacilityDocInput
    from medlinker_ai.extract import extract_capabilities
    from medlinker_ai.verify import check_incomplete_rules, check_suspicious_rules, calculate_confidence
    from medlinker_ai.aggregate import compute_region_summary
    from medlinker_ai.utils import generate_trace_id
    from medlinker_ai.trace import start_trace, log_span, end_trace
    
    try:
        # Parse input
        doc = FacilityDocInput(**facility_input)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid facility input: {str(e)}"
        )
    
    # Start unified trace
    trace_id = generate_trace_id()
    start_trace(trace_id)
    
    try:
        # Step 1: Extract capabilities
        capabilities, extracted_citations = extract_capabilities(doc, trace_id=trace_id)
        
        # Step 2: Verify facility
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
        
        # Create facility output
        from medlinker_ai.models import FacilityAnalysisOutput
        facility_output = FacilityAnalysisOutput(
            facility_id=doc.facility_id,
            extracted_capabilities=capabilities,
            status=status,
            reasons=reasons,
            confidence=confidence,
            citations=all_citations,
            trace_id=trace_id
        )
        
        # Step 3: Aggregate (single facility)
        region_summary = compute_region_summary(
            doc.country,
            doc.region,
            [facility_output],
            parent_trace_id=trace_id
        )
        
        # Step 4: Generate sample answer
        sample_question = f"What is the status of {doc.facility_name}?"
        sample_answer = f"Facility {doc.facility_name} in {doc.region}, {doc.country} has status: {status}. "
        if status == "VERIFIED":
            sample_answer += "All capabilities are verified and consistent."
        elif status == "INCOMPLETE":
            sample_answer += f"Missing information: {', '.join(reasons[:2])}."
        else:
            sample_answer += f"Inconsistencies detected: {', '.join(reasons[:2])}."
        
        # Log answer span
        log_span(
            trace_id=trace_id,
            step_name="answer",
            inputs_summary={
                "question": sample_question,
                "question_length": len(sample_question)
            },
            outputs_summary={
                "answer_length": len(sample_answer),
                "citations_count": len(all_citations)
            },
            evidence_refs=len(all_citations)
        )
        
        # End trace
        end_trace(trace_id)
        
        return {
            "facility_analysis": facility_output.model_dump(),
            "region_summary": region_summary.model_dump(),
            "sample_qa": {
                "question": sample_question,
                "answer": sample_answer
            },
            "trace_id": trace_id,
            "message": f"Complete pipeline executed. View trace at /trace/{trace_id}"
        }
        
    except Exception as e:
        end_trace(trace_id)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/health")
def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy"}
