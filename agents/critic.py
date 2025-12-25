"""Critic Agent for validating analysis reports.

Validates report quality using multi-gate validation:
1. Completeness - All ingredients addressed
2. Format - Proper table structure with required columns
3. Allergen Match - User allergies properly flagged
4. Consistency - Safety scores match concern descriptions
5. Tone - Appropriate for user expertise level

The critic uses a single LLM call with a comprehensive validation prompt
to evaluate all gates simultaneously.

Uses langchain-google-genai for LangSmith tracing integration.
"""

import re
import time

from config.settings import get_settings
from config.logging_config import get_logger
from config.gemini_logger import get_gemini_logger
from config.llm import invoke_llm
from prompts.critic_prompts import VALIDATION_PROMPT
from state.schema import (
    AnalysisReport,
    CriticFeedback,
    StageTiming,
    ValidationResult,
    WorkflowState,
)


logger = get_logger(__name__)


def validate_report(state: WorkflowState) -> dict:
    """Critic agent node function.

    Validates the analysis report using multi-gate validation.
    All 5 gates must pass for approval.

    Args:
        state: Current workflow state.

    Returns:
        State update with critic_feedback and routing_history.
    """
    start_time = time.time()

    report = state["analysis_report"]
    raw_ingredients = state["raw_ingredients"]
    user_profile = state["user_profile"]
    retry_count = state.get("retry_count", 0)

    logger.info(f"Validating report (attempt {retry_count + 1})")

    routing_history = state.get("routing_history", []).copy()
    routing_history.append("critic")

    # Build validation context
    ingredient_count = len(raw_ingredients)
    ingredient_names = ", ".join(raw_ingredients)
    allergen_list = ", ".join(user_profile["allergies"]) if user_profile["allergies"] else "None declared"
    expertise_level = user_profile["expertise"].value

    # Run multi-gate validation via LLM
    validation_result = _run_multi_gate_validation(
        report=report,
        ingredient_count=ingredient_count,
        ingredient_names=ingredient_names,
        allergen_list=allergen_list,
        expertise_level=expertise_level,
    )

    # Determine final result based on gate outcomes
    max_retries = get_settings().max_retries
    all_gates_passed = all([
        validation_result["completeness_ok"],
        validation_result["format_ok"],
        validation_result["allergens_ok"],
        validation_result["consistency_ok"],
        validation_result["tone_ok"],
    ])

    if all_gates_passed:
        result = ValidationResult.APPROVED
        feedback = "All validation gates passed. Report meets quality standards."
        failed_gates = []
    elif retry_count >= max_retries:
        result = ValidationResult.ESCALATED
        failed_gates = validation_result["failed_gates"]
        feedback = (
            f"Report could not meet quality standards after {max_retries + 1} attempts. "
            f"Failed gates: {', '.join(failed_gates)}. "
            "Results are provided with reduced confidence."
        )
    else:
        result = ValidationResult.REJECTED
        failed_gates = validation_result["failed_gates"]
        feedback = validation_result["feedback"]

    critic_feedback = CriticFeedback(
        result=result,
        completeness_ok=validation_result["completeness_ok"],
        format_ok=validation_result["format_ok"],
        allergens_ok=validation_result["allergens_ok"],
        consistency_ok=validation_result["consistency_ok"],
        tone_ok=validation_result["tone_ok"],
        feedback=feedback,
        failed_gates=failed_gates,
    )

    elapsed = time.time() - start_time
    logger.info(
        f"Validation result in {elapsed:.2f}s: {result.value} | "
        f"Gates: completeness={validation_result['completeness_ok']}, "
        f"format={validation_result['format_ok']}, "
        f"allergens={validation_result['allergens_ok']}, "
        f"consistency={validation_result['consistency_ok']}, "
        f"tone={validation_result['tone_ok']}"
    )

    # Increment retry count if rejected
    new_retry_count = retry_count
    if result == ValidationResult.REJECTED:
        new_retry_count = retry_count + 1
        logger.info(f"Retry count incremented to {new_retry_count}")

    # Update stage timings
    stage_timings = state.get("stage_timings") or StageTiming(
        research_time=0.0,
        analysis_time=0.0,
        critic_time=0.0,
    )
    stage_timings["critic_time"] = stage_timings.get("critic_time", 0.0) + elapsed

    return {
        "critic_feedback": critic_feedback,
        "retry_count": new_retry_count,
        "routing_history": routing_history,
        "stage_timings": stage_timings,
    }


def _run_multi_gate_validation(
    report: AnalysisReport,
    ingredient_count: int,
    ingredient_names: str,
    allergen_list: str,
    expertise_level: str,
) -> dict:
    """Run multi-gate validation using a single LLM call.

    Args:
        report: The analysis report to validate.
        ingredient_count: Number of expected ingredients.
        ingredient_names: Comma-separated ingredient names.
        allergen_list: User's allergies or "None declared".
        expertise_level: User's expertise level.

    Returns:
        Dict with gate results and feedback.
    """
    # Default gate results (assume pass, will be overridden by LLM response)
    gate_results = {
        "completeness_ok": True,
        "format_ok": True,
        "allergens_ok": True,
        "consistency_ok": True,
        "tone_ok": True,
        "failed_gates": [],
        "feedback": "",
    }

    try:
        settings = get_settings()

        # Build the validation prompt
        prompt = VALIDATION_PROMPT.format(
            ingredient_count=ingredient_count,
            ingredient_names=ingredient_names,
            allergen_list=allergen_list,
            expertise_level=expertise_level,
            safety_analysis=report["summary"],
        )

        # Call LLM via LangChain (enables LangSmith tracing)
        start_time = time.time()
        response_text = invoke_llm(prompt, run_name="validate_report")
        response_text = response_text.strip()
        elapsed = time.time() - start_time

        # Parse LLM response
        gate_results = _parse_validation_response(response_text, gate_results)

        # Log to Gemini logger (backup logging)
        gemini_logger = get_gemini_logger()
        gemini_logger.log_interaction(
            operation="multi_gate_validation",
            prompt=prompt,
            response=response_text,
            metadata={
                "model": settings.gemini_model,
                "latency_seconds": f"{elapsed:.3f}",
                "ingredient_count": ingredient_count,
                "allergen_list": allergen_list,
                "expertise_level": expertise_level,
                "decision": "APPROVE" if not gate_results["failed_gates"] else "REJECT",
                "failed_gates": ", ".join(gate_results["failed_gates"]) or "none",
            },
        )

        logger.debug(f"Validation LLM response: {response_text[:200]}...")

    except Exception as e:
        logger.error(f"Multi-gate validation LLM call failed: {e}")
        # On error, assume all gates pass to avoid blocking workflow
        gate_results["feedback"] = f"Validation error: {str(e)}"

    return gate_results


def _parse_validation_response(response_text: str, default_results: dict) -> dict:
    """Parse the LLM validation response into gate results.

    Args:
        response_text: Raw LLM response.
        default_results: Default gate results to use.

    Returns:
        Updated gate results dict.
    """
    results = default_results.copy()
    failed_gates = []

    # Check for APPROVE or REJECT decision
    upper_response = response_text.upper()

    if upper_response.startswith("APPROVE"):
        # All gates passed
        results["feedback"] = "All validation gates passed."
        return results

    if "REJECT" in upper_response:
        # Parse failed gates from response
        response_lower = response_text.lower()

        # Gate 1: Completeness - check if mentioned with negative context
        if "completeness" in response_lower:
            if _gate_failed(response_text, "completeness") or _gate_mentioned_negatively(response_text, "completeness"):
                results["completeness_ok"] = False
                failed_gates.append("Completeness")

        # Gate 2: Format - check if mentioned with negative context
        if "format" in response_lower:
            if _gate_failed(response_text, "format") or _gate_mentioned_negatively(response_text, "format"):
                results["format_ok"] = False
                failed_gates.append("Format")

        # Gate 3: Allergen Match - check if mentioned with negative context
        if "allergen" in response_lower:
            if _gate_failed(response_text, "allergen") or _gate_mentioned_negatively(response_text, "allergen"):
                results["allergens_ok"] = False
                failed_gates.append("Allergen Match")

        # Gate 4: Consistency - check if mentioned with negative context
        if "consistency" in response_lower:
            if _gate_failed(response_text, "consistency") or _gate_mentioned_negatively(response_text, "consistency"):
                results["consistency_ok"] = False
                failed_gates.append("Consistency")

        # Gate 5: Tone - check if mentioned with negative context
        if "tone" in response_lower:
            if _gate_failed(response_text, "tone") or _gate_mentioned_negatively(response_text, "tone"):
                results["tone_ok"] = False
                failed_gates.append("Tone")

        # Extract the reason from the REJECT line itself
        reject_reason = _extract_reject_reason(response_text)

        # If no specific gates identified but REJECT found, try to infer from reason
        if not failed_gates:
            # Try to infer gate from reject reason
            if reject_reason:
                inferred_gate, inferred_ok_field = _infer_gate_from_reason(reject_reason)
                if inferred_gate:
                    failed_gates.append(inferred_gate)
                    if inferred_ok_field:
                        results[inferred_ok_field] = False
                else:
                    # Could not infer, use the reason as feedback
                    results["completeness_ok"] = False
                    failed_gates.append("Quality")
            else:
                results["completeness_ok"] = False
                failed_gates.append("Quality")

        results["failed_gates"] = failed_gates

        # Extract specific issues and required fixes from response
        feedback_parts = []

        # Use reject reason if available
        if reject_reason:
            feedback_parts.append(reject_reason)

        # Look for "Specific issues:" section
        issues_match = re.search(r"specific issues:(.+?)(?:required fixes:|$)", response_text, re.IGNORECASE | re.DOTALL)
        if issues_match:
            issues = issues_match.group(1).strip()
            feedback_parts.append(f"Issues: {issues[:300]}")

        # Look for "Required fixes:" section
        fixes_match = re.search(r"required fixes:(.+?)(?:$)", response_text, re.IGNORECASE | re.DOTALL)
        if fixes_match:
            fixes = fixes_match.group(1).strip()
            feedback_parts.append(f"Required fixes: {fixes[:300]}")

        if feedback_parts:
            results["feedback"] = " | ".join(feedback_parts)
        else:
            results["feedback"] = f"Failed gates: {', '.join(failed_gates)}. Please address these issues."

    return results


def _extract_reject_reason(response_text: str) -> str | None:
    """Extract the reason from a REJECT response.

    Args:
        response_text: Full LLM response.

    Returns:
        The reject reason or None.
    """
    # Look for "REJECT: reason" or "REJECT - reason" or "REJECT\nreason"
    patterns = [
        r"REJECT[:\-\s]+(.+?)(?:\n\n|Specific issues:|Required fixes:|Gate failures:|$)",
        r"REJECT\s*\n+(.+?)(?:\n\n|Specific issues:|Required fixes:|Gate failures:|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            reason = match.group(1).strip()
            # Clean up the reason
            reason = re.sub(r'\s+', ' ', reason)
            if reason and len(reason) > 5:  # Meaningful reason
                return reason[:500]

    return None


def _gate_mentioned_negatively(response_text: str, gate_name: str) -> bool:
    """Check if a gate is mentioned in a negative context.

    Args:
        response_text: Full LLM response.
        gate_name: Name of the gate to check.

    Returns:
        True if the gate is mentioned negatively.
    """
    response_lower = response_text.lower()

    # Patterns indicating negative mention
    negative_patterns = [
        f"{gate_name}.*not.*appropriate",
        f"{gate_name}.*not.*match",
        f"{gate_name}.*not.*correct",
        f"{gate_name}.*wrong",
        f"{gate_name}.*problem",
        f"{gate_name}.*error",
        f"not.*{gate_name}",
        f"lacks.*{gate_name}",
        f"missing.*{gate_name}",
        f"{gate_name}.*lacks",
        f"{gate_name}.*missing",
    ]

    for pattern in negative_patterns:
        if re.search(pattern, response_lower):
            return True

    return False


def _infer_gate_from_reason(reason: str) -> tuple[str | None, str | None]:
    """Infer which gate failed from the reject reason.

    Args:
        reason: The reject reason text.

    Returns:
        Tuple of (gate_name, ok_field_name) or (None, None).
    """
    reason_lower = reason.lower()

    # Map keywords to gates
    gate_keywords = {
        "Completeness": (["missing ingredient", "not all ingredient", "incomplete", "doesn't cover"], "completeness_ok"),
        "Format": (["table", "format", "structure", "markdown", "column"], "format_ok"),
        "Allergen Match": (["allergen", "allergy", "allergic"], "allergens_ok"),
        "Consistency": (["consistency", "inconsistent", "score.*match", "rating.*concern", "mismatch"], "consistency_ok"),
        "Tone": (["tone", "language", "technical", "beginner", "expert", "complex", "simple"], "tone_ok"),
    }

    for gate_name, (keywords, ok_field) in gate_keywords.items():
        for keyword in keywords:
            if re.search(keyword, reason_lower):
                return gate_name, ok_field

    return None, None


def _gate_failed(response_text: str, gate_name: str) -> bool:
    """Check if a specific gate failed based on response context.

    Args:
        response_text: Full LLM response.
        gate_name: Name of the gate to check.

    Returns:
        True if the gate failed, False otherwise.
    """
    # Look for patterns indicating gate failure
    response_lower = response_text.lower()

    # Common failure patterns
    failure_patterns = [
        f"{gate_name}.*fail",
        f"{gate_name}.*not.*pass",
        f"{gate_name}.*missing",
        f"{gate_name}.*issue",
        f"{gate_name}.*incomplete",
        f"{gate_name}.*violation",
        f"gate failure.*{gate_name}",
        f"failed gate.*{gate_name}",
    ]

    for pattern in failure_patterns:
        if re.search(pattern, response_lower):
            return True

    return False


def is_approved(state: WorkflowState) -> bool:
    """Check if report was approved.

    Args:
        state: Current workflow state.

    Returns:
        True if critic approved the report.
    """
    feedback = state.get("critic_feedback")
    if not feedback:
        return False
    return feedback["result"] == ValidationResult.APPROVED


def is_rejected(state: WorkflowState) -> bool:
    """Check if report was rejected (needs retry).

    Args:
        state: Current workflow state.

    Returns:
        True if critic rejected and retry is possible.
    """
    feedback = state.get("critic_feedback")
    if not feedback:
        return False
    return feedback["result"] == ValidationResult.REJECTED


def is_escalated(state: WorkflowState) -> bool:
    """Check if report was escalated.

    Args:
        state: Current workflow state.

    Returns:
        True if max retries exceeded.
    """
    feedback = state.get("critic_feedback")
    if not feedback:
        return False
    return feedback["result"] == ValidationResult.ESCALATED
