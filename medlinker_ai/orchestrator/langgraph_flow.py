"""LangGraph orchestration flow for MedLinker AI.

This module provides optional LangGraph orchestration for the ask flow.
Falls back to direct function calls if LangGraph is not available.
"""

import os
from typing import TypedDict, List, Optional, Dict, Any

from medlinker_ai.models import FacilityAnalysisOutput, RegionSummary


# Try to import LangGraph (optional)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


def is_orchestrator_enabled() -> bool:
    """Check if LangGraph orchestrator is enabled.
    
    Returns:
        True if ORCHESTRATOR=langgraph and LangGraph is available
    """
    return (
        LANGGRAPH_AVAILABLE and
        os.environ.get("ORCHESTRATOR", "").lower() == "langgraph"
    )


if LANGGRAPH_AVAILABLE:
    class AskFlowState(TypedDict):
        """State for ask flow orchestration."""
        question: str
        facilities: List[FacilityAnalysisOutput]
        regions: List[RegionSummary]
        answer: Optional[str]
        citations: Optional[List[dict]]
        trace_id: Optional[str]
        llm_provider: Optional[str]
    
    
    def answer_node(state: AskFlowState) -> AskFlowState:
        """Answer node that calls existing answer_planner_question.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with answer
        """
        from medlinker_ai.qa import answer_planner_question
        
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
    
    
    def build_ask_graph() -> StateGraph:
        """Build LangGraph for ask flow.
        
        Returns:
            Compiled StateGraph
        """
        graph = StateGraph(AskFlowState)
        
        # Add answer node
        graph.add_node("answer", answer_node)
        
        # Set entry point
        graph.set_entry_point("answer")
        
        # Add edge to end
        graph.add_edge("answer", END)
        
        return graph.compile()


def run_ask_flow(
    question: str,
    facilities: List[FacilityAnalysisOutput],
    regions: List[RegionSummary],
    llm_provider: Optional[str] = None
) -> Dict[str, Any]:
    """Run ask flow with optional LangGraph orchestration.
    
    Args:
        question: User question
        facilities: List of facility outputs
        regions: List of region summaries
        llm_provider: Optional LLM provider
        
    Returns:
        Dictionary with answer, citations, and trace_id
    """
    if is_orchestrator_enabled():
        # Use LangGraph orchestration
        graph = build_ask_graph()
        
        initial_state: AskFlowState = {
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
    else:
        # Direct function call (current behavior)
        from medlinker_ai.qa import answer_planner_question
        
        return answer_planner_question(
            question,
            facilities,
            regions,
            llm_provider=llm_provider
        )
