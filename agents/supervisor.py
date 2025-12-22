"""Supervisor Agent for workflow routing.

Manages the multi-agent workflow by determining which agent
should process next based on current state.

Integrates with:
- Research Agent: Parallel ingredient research (3 per worker)
- Analysis Agent: LLM-based safety analysis with tone adaptation
- Critic Agent: 5-gate validation (completeness, format, allergens, consistency, tone)
"""

from typing import Literal

from config.logging_config import get_logger
from state.schema import ValidationResult, WorkflowState
from agents.research import has_research_data, BATCH_SIZE
from agents.analysis import has_analysis_report
from agents.critic import is_approved, is_rejected, is_escalated


logger = get_logger(__name__)

# Node names for routing
NODE_RESEARCH = "research"
NODE_ANALYSIS = "analysis"
NODE_CRITIC = "critic"
NODE_END = "end"

RouteType = Literal["research", "analysis", "critic", "end"]


def route_next(state: WorkflowState) -> RouteType:
    """Determine the next node in the workflow.

    Routing logic:
    1. If no research data -> research
    2. If no analysis report -> analysis
    3. If report exists but not validated -> critic
    4. If approved or escalated -> end
    5. If rejected -> analysis (retry)

    Args:
        state: Current workflow state.

    Returns:
        Name of the next node to execute.
    """
    logger.info("Supervisor evaluating state for routing...")

    # Check for errors
    if state.get("error"):
        logger.warning(f"Error in state: {state['error']}")
        return NODE_END

    # Step 1: Need research data?
    if not has_research_data(state):
        ingredient_count = len(state.get("raw_ingredients", []))
        worker_count = max(1, (ingredient_count + BATCH_SIZE - 1) // BATCH_SIZE)
        parallel_note = f" ({worker_count} parallel workers)" if ingredient_count > BATCH_SIZE else ""
        logger.info(f"Route -> research (missing ingredient data){parallel_note}")
        return NODE_RESEARCH

    # Step 2: Need analysis report?
    if not has_analysis_report(state):
        logger.info("Route -> analysis (missing report)")
        return NODE_ANALYSIS

    # Step 3: Check validation status
    critic_feedback = state.get("critic_feedback")

    if critic_feedback is None:
        logger.info("Route -> critic (report needs validation)")
        return NODE_CRITIC

    # Step 4: Handle validation results
    if is_approved(state):
        logger.info("Route -> end (report approved)")
        return NODE_END

    if is_escalated(state):
        logger.info("Route -> end (escalated after max retries)")
        return NODE_END

    if is_rejected(state):
        # Get failed gate details for logging
        failed_gates = critic_feedback.get("failed_gates", [])
        feedback = critic_feedback.get("feedback", "")
        logger.info(
            f"Route -> analysis (retry after rejection) | "
            f"Failed gates: {', '.join(failed_gates) if failed_gates else 'unspecified'}"
        )
        return NODE_ANALYSIS

    # Fallback - should not reach here
    logger.warning("Unexpected state, routing to end")
    return NODE_END


def should_continue(state: WorkflowState) -> bool:
    """Check if workflow should continue.

    Args:
        state: Current workflow state.

    Returns:
        True if more processing needed.
    """
    next_node = route_next(state)
    return next_node != NODE_END


def get_routing_decision(state: WorkflowState) -> str:
    """Get a human-readable routing decision.

    Args:
        state: Current workflow state.

    Returns:
        Description of routing decision.
    """
    next_node = route_next(state)

    # Add context-aware details
    if next_node == NODE_RESEARCH:
        ingredient_count = len(state.get("raw_ingredients", []))
        worker_count = max(1, (ingredient_count + BATCH_SIZE - 1) // BATCH_SIZE)
        if ingredient_count > BATCH_SIZE:
            return f"Fetching ingredient data ({worker_count} parallel workers)"
        return "Fetching ingredient data from knowledge base"

    if next_node == NODE_CRITIC:
        return "Validating report (5-gate: completeness, format, allergens, consistency, tone)"

    decisions = {
        NODE_ANALYSIS: "Generating personalized safety analysis",
        NODE_END: "Workflow complete",
    }

    return decisions.get(next_node, "Unknown decision")
