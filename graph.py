"""LangGraph workflow for ingredient analysis.

Assembles the multi-agent workflow with conditional routing
and retry logic.
"""

from typing import Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from config.logging_config import get_logger, setup_logging
from state.schema import WorkflowState, ValidationResult, StageTiming
from agents.supervisor import route_next, NODE_END
from agents.research import research_ingredients
from agents.analysis import analyze_ingredients
from agents.critic import validate_report


logger = get_logger(__name__)


def create_workflow() -> StateGraph:
    """Create the ingredient analysis workflow graph.

    The workflow follows this pattern:
    1. Research: Fetch ingredient data
    2. Analysis: Generate safety report
    3. Critic: Validate report
    4. If rejected, retry analysis (max 2 times)
    5. End with approved or escalated report

    Returns:
        Compiled StateGraph workflow.
    """
    # Create the graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("research", research_ingredients)
    workflow.add_node("analysis", analyze_ingredients)
    workflow.add_node("critic", validate_report)

    # Add conditional routing from entry
    workflow.set_conditional_entry_point(
        route_next,
        {
            "research": "research",
            "analysis": "analysis",
            "critic": "critic",
            "end": END,
        },
    )

    # Add edges from each node through supervisor routing
    workflow.add_conditional_edges(
        "research",
        route_next,
        {
            "research": "research",
            "analysis": "analysis",
            "critic": "critic",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "analysis",
        route_next,
        {
            "research": "research",
            "analysis": "analysis",
            "critic": "critic",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "critic",
        route_next,
        {
            "research": "research",
            "analysis": "analysis",
            "critic": "critic",
            "end": END,
        },
    )

    return workflow


def compile_workflow():
    """Create and compile the workflow.

    Returns:
        Compiled workflow ready for invocation.
    """
    workflow = create_workflow()
    return workflow.compile()


def run_analysis(
    session_id: str,
    product_name: str,
    ingredients: list[str],
    allergies: list[str],
    skin_type: str,
    expertise: str,
) -> WorkflowState:
    """Run the ingredient analysis workflow.

    Args:
        session_id: Unique session identifier.
        product_name: Name of the product.
        ingredients: List of ingredient names.
        allergies: User's known allergies.
        skin_type: User's skin type.
        expertise: User's expertise level.

    Returns:
        Final workflow state with analysis results.
    """
    from state.schema import SkinType, ExpertiseLevel, UserProfile

    setup_logging()
    logger.info(f"Starting analysis for '{product_name}' ({len(ingredients)} ingredients)")

    # Create initial state
    initial_state = WorkflowState(
        session_id=session_id,
        product_name=product_name,
        raw_ingredients=ingredients,
        user_profile=UserProfile(
            allergies=allergies,
            skin_type=SkinType(skin_type),
            expertise=ExpertiseLevel(expertise),
        ),
        ingredient_data=[],
        analysis_report=None,
        critic_feedback=None,
        retry_count=0,
        routing_history=[],
        stage_timings=StageTiming(
            research_time=0.0,
            analysis_time=0.0,
            critic_time=0.0,
        ),
        error=None,
    )

    # Compile and run workflow
    app = compile_workflow()

    try:
        final_state = app.invoke(initial_state, {"recursion_limit": 50})
        logger.info(
            f"Analysis complete. Route history: {final_state.get('routing_history', [])}"
        )
        return final_state
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        initial_state["error"] = str(e)
        return initial_state


# Export for LangSmith tracing
__all__ = ["create_workflow", "compile_workflow", "run_analysis"]
