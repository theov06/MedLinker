"""LangGraph orchestration wrapper for MedLinker AI pipeline.

This module wraps the existing pipeline in LangGraph to explicitly show
agentic orchestration. All logic remains in the original modules - this
is purely an orchestration layer.
"""

from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END

from medlinker_ai.models import (
    FacilityDocInput,
    CapabilitySchemaV0,
    Citation,
    FacilityAnalysisOutput,
    RegionSummary
)
from medlinker_ai.extract import extract_capabilities
from medlinker_ai.verify import verify_facility
from medlinker_ai.aggregate import aggregate_regions
from medlinker_ai.qa import answer_planner_question


# State definitions for different pipeline flows
class ExtractionState(TypedDict):
    """State for extraction flow."""
    facility_doc: FacilityDocInput
    capabilities: Optional[CapabilitySchemaV0]
    citations: Optional[List[Citation]]
    llm_provider: Optional[str]
    trace_id: Optional[str]


class VerificationState(TypedDict):
    """State for verification flow."""
    facility_doc: FacilityDocInput
    analysis: Optional[FacilityAnalysisOutput]
    llm_provider: Optional[str]


class AggregationState(TypedDict):
    """State for aggregation flow."""
    facility_outputs: List[FacilityAnalysisOutput]
    region_summaries: Optional[List[RegionSummary]]


class QAState(TypedDict):
    """State for Q&A flow."""
    question: str
    facilities: List[FacilityAnalysisOutput]
    regions: List[RegionSummary]
    answer: Optional[str]
    citations: Optional[List[dict]]
    trace_id: Optional[str]
    llm_provider: Optional[str]


# Node functions - thin wrappers around existing functions
def extract_node(state: ExtractionState) -> ExtractionState:
    """Extract capabilities from facility document.
    
    Args:
        state: Current extraction state
        
    Returns:
        Updated state with capabilities and citations
    """
    capabilities, citations = extract_capabilities(
        state["facility_doc"],
        llm_provider=state.get("llm_provider"),
        trace_id=state.get("trace_id")
    )
    
    return {
        **state,
        "capabilities": capabilities,
        "citations": citations
    }


def verify_node(state: VerificationState) -> VerificationState:
    """Verify facility and detect inconsistencies.
    
    Args:
        state: Current verification state
        
    Returns:
        Updated state with analysis output
    """
    analysis = verify_facility(
        state["facility_doc"],
        llm_provider=state.get("llm_provider")
    )
    
    return {
        **state,
        "analysis": analysis
    }


def aggregate_node(state: AggregationState) -> AggregationState:
    """Aggregate facilities into regional summaries.
    
    Args:
        state: Current aggregation state
        
    Returns:
        Updated state with region summaries
    """
    summaries = aggregate_regions(state["facility_outputs"])
    
    return {
        **state,
        "region_summaries": summaries
    }


def answer_node(state: QAState) -> QAState:
    """Answer planner question with grounded response.
    
    Args:
        state: Current Q&A state
        
    Returns:
        Updated state with answer and citations
    """
    result = answer_planner_question(
        state["question"],
        state["facilities"],
        state["regions"],
        llm_provider=state.get("llm_provider")
    )
    
    return {
        **state,
        "answer": result["answer"],
        "citations": result["citations"],
        "trace_id": result["trace_id"]
    }


# Graph builders
def build_extraction_graph() -> StateGraph:
    """Build LangGraph for extraction flow.
    
    Returns:
        Compiled StateGraph for extraction
    """
    graph = StateGraph(ExtractionState)
    
    # Add node
    graph.add_node("extract", extract_node)
    
    # Set entry point
    graph.set_entry_point("extract")
    
    # Add edge to end
    graph.add_edge("extract", END)
    
    return graph.compile()


def build_verification_graph() -> StateGraph:
    """Build LangGraph for verification flow.
    
    Returns:
        Compiled StateGraph for verification
    """
    graph = StateGraph(VerificationState)
    
    # Add node
    graph.add_node("verify", verify_node)
    
    # Set entry point
    graph.set_entry_point("verify")
    
    # Add edge to end
    graph.add_edge("verify", END)
    
    return graph.compile()


def build_aggregation_graph() -> StateGraph:
    """Build LangGraph for aggregation flow.
    
    Returns:
        Compiled StateGraph for aggregation
    """
    graph = StateGraph(AggregationState)
    
    # Add node
    graph.add_node("aggregate", aggregate_node)
    
    # Set entry point
    graph.set_entry_point("aggregate")
    
    # Add edge to end
    graph.add_edge("aggregate", END)
    
    return graph.compile()


def build_qa_graph() -> StateGraph:
    """Build LangGraph for Q&A flow.
    
    Returns:
        Compiled StateGraph for Q&A
    """
    graph = StateGraph(QAState)
    
    # Add node
    graph.add_node("answer", answer_node)
    
    # Set entry point
    graph.set_entry_point("answer")
    
    # Add edge to end
    graph.add_edge("answer", END)
    
    return graph.compile()


# Convenience functions for executing graphs
def run_extraction_graph(
    facility_doc: FacilityDocInput,
    llm_provider: Optional[str] = None,
    trace_id: Optional[str] = None
) -> tuple[CapabilitySchemaV0, List[Citation]]:
    """Run extraction using LangGraph orchestration.
    
    Args:
        facility_doc: Input facility document
        llm_provider: Optional LLM provider override
        trace_id: Optional trace ID
        
    Returns:
        Tuple of (capabilities, citations)
    """
    graph = build_extraction_graph()
    
    initial_state: ExtractionState = {
        "facility_doc": facility_doc,
        "capabilities": None,
        "citations": None,
        "llm_provider": llm_provider,
        "trace_id": trace_id
    }
    
    final_state = graph.invoke(initial_state)
    
    return final_state["capabilities"], final_state["citations"]


def run_verification_graph(
    facility_doc: FacilityDocInput,
    llm_provider: Optional[str] = None
) -> FacilityAnalysisOutput:
    """Run verification using LangGraph orchestration.
    
    Args:
        facility_doc: Input facility document
        llm_provider: Optional LLM provider override
        
    Returns:
        Facility analysis output
    """
    graph = build_verification_graph()
    
    initial_state: VerificationState = {
        "facility_doc": facility_doc,
        "analysis": None,
        "llm_provider": llm_provider
    }
    
    final_state = graph.invoke(initial_state)
    
    return final_state["analysis"]


def run_aggregation_graph(
    facility_outputs: List[FacilityAnalysisOutput]
) -> List[RegionSummary]:
    """Run aggregation using LangGraph orchestration.
    
    Args:
        facility_outputs: List of facility analysis outputs
        
    Returns:
        List of region summaries
    """
    graph = build_aggregation_graph()
    
    initial_state: AggregationState = {
        "facility_outputs": facility_outputs,
        "region_summaries": None
    }
    
    final_state = graph.invoke(initial_state)
    
    return final_state["region_summaries"]


def run_qa_graph(
    question: str,
    facilities: List[FacilityAnalysisOutput],
    regions: List[RegionSummary],
    llm_provider: Optional[str] = None
) -> dict:
    """Run Q&A using LangGraph orchestration.
    
    Args:
        question: User question
        facilities: List of facility outputs
        regions: List of region summaries
        llm_provider: Optional LLM provider override
        
    Returns:
        Dictionary with answer, citations, and trace_id
    """
    graph = build_qa_graph()
    
    initial_state: QAState = {
        "question": question,
        "facilities": facilities,
        "regions": regions,
        "answer": None,
        "citations": None,
        "trace_id": None,
        "llm_provider": llm_provider
    }
    
    final_state = graph.invoke(initial_state)
    
    return {
        "answer": final_state["answer"],
        "citations": final_state["citations"],
        "trace_id": final_state["trace_id"]
    }
