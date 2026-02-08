"""FastAPI backend for MedLinker AI."""

import json
import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from medlinker_ai.models import (
    FacilityAnalysisOutput,
    RegionSummary,
    Citation,
)
from medlinker_ai.qa import answer_planner_question
from medlinker_ai.trace import get_trace, TraceRun


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    question: str = Field(
        ...,
        description="Question to answer about healthcare facilities and regions",
        json_schema_extra={"example": "Which regions have the highest desert score?"}
    )


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
    
    Returns all processed healthcare facilities with extracted capabilities,
    verification status, confidence scores, and citations to source data.
    
    Returns:
        List of facility analysis outputs with extracted capabilities,
        verification status, and citations.
    """
    return load_facilities()


@app.get("/regions", response_model=List[RegionSummary])
def get_regions():
    """Get all regional summaries with medical desert scores.
    
    Returns regional aggregations showing healthcare coverage, missing
    critical services, and desert scores (0-100, higher = worse).
    
    Returns:
        List of regional summaries with desert scores, missing capabilities,
        and coverage statistics.
    """
    return load_regions()


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """Answer planner question with grounded citations.
    
    This endpoint answers questions about healthcare facilities and regions
    using the processed data. All answers include citations to source data
    and a trace_id for full auditability.
    
    Args:
        request: Question request with question text
        
    Returns:
        Grounded answer with citations and trace ID
        
    Raises:
        HTTPException: If data not available or question invalid
    """
    # Validate question
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question must be a non-empty string."
        )
    
    logger.info(f"[/ask] Question received: {request.question[:100]}")
    
    # Load data
    try:
        facilities = load_facilities()
        regions = load_regions()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[/ask] Error loading data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading data: {str(e)}"
        )
    
    # Check for RAG
    rag_enabled = False
    try:
        from medlinker_ai.rag import is_rag_available
        rag_enabled = is_rag_available()
        if rag_enabled:
            logger.info("[/ask] RAG retrieval: ENABLED")
        else:
            logger.info("[/ask] RAG retrieval: DISABLED")
    except ImportError:
        logger.info("[/ask] RAG retrieval: NOT INSTALLED (using keyword matching)")
    except Exception as e:
        logger.warning(f"[/ask] RAG check failed: {str(e)}, falling back to keyword matching")
    
    # Check for orchestrator
    orchestrator_enabled = False
    try:
        from medlinker_ai.orchestrator import run_ask_flow, is_orchestrator_enabled
        orchestrator_enabled = is_orchestrator_enabled()
        if orchestrator_enabled:
            logger.info("[/ask] LangGraph orchestration: ENABLED")
        else:
            logger.info("[/ask] LangGraph orchestration: DISABLED")
    except ImportError:
        logger.info("[/ask] LangGraph orchestration: NOT INSTALLED (using direct calls)")
    except Exception as e:
        logger.warning(f"[/ask] Orchestrator check failed: {str(e)}, falling back to direct calls")
    
    # Answer question
    try:
        if orchestrator_enabled:
            result = run_ask_flow(
                request.question,
                facilities,
                regions
            )
        else:
            result = answer_planner_question(
                request.question,
                facilities,
                regions
            )
    except Exception as e:
        logger.error(f"[/ask] Error answering question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )
    
    # Ensure result has required fields
    if not result or "answer" not in result or "citations" not in result or "trace_id" not in result:
        logger.error(f"[/ask] Invalid result format: {result}")
        raise HTTPException(
            status_code=500,
            detail="Internal error: Invalid response format"
        )
    
    logger.info(f"[/ask] Answer generated with trace_id: {result['trace_id']}")
    
    return AskResponse(
        answer=result["answer"],
        citations=result["citations"] or [],  # Ensure citations is never None
        trace_id=result["trace_id"]
    )


@app.get("/trace/{trace_id}", response_model=TraceRun)
def get_trace_by_id(trace_id: str):
    """Inspect reasoning trace returned by /ask.
    
    Use this endpoint to view the complete reasoning trace for a question,
    including all pipeline steps, evidence references, and timing information.
    
    Args:
        trace_id: Unique trace identifier (UUID format, e.g., "a5ad364e-9e1f-40cb-9499-74572975ede9")
        
    Returns:
        Complete trace with all spans in chronological order
        
    Raises:
        HTTPException: If trace not found
    """
    # Sanitize trace_id input
    # Strip whitespace, quotes, and URL-decode
    trace_id = trace_id.strip()
    trace_id = trace_id.strip('"').strip("'")
    trace_id = unquote(trace_id)
    
    logger.info(f"[/trace] Looking up trace_id: {trace_id}")
    
    trace = get_trace(trace_id)
    
    if not trace:
        logger.warning(f"[/trace] Trace not found: {trace_id}")
        raise HTTPException(
            status_code=404,
            detail="Trace not found. Make sure you copied the trace_id exactly (without quotes)."
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
