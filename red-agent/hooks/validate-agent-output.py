#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pydantic>=2.0.0",
#   "pyyaml>=6.0.0",
# ]
# ///
"""PostToolUse hook to validate red-agent sub-agent outputs.

Receives Task tool results via stdin, validates YAML output against
Pydantic models. On failure, blocks with error details so the coordinator
can retry the sub-agent. On success, passes silently.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

# Add src directory to path to import models
SCRIPT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

# ruff: noqa: E402 (imports after sys.path modification)
from red_agent.models import (
    AttackerOutput,
    AttackStrategyOutput,
    ContextAnalysisOutput,
    FixApplicatorOutput,
    FixCommitterOutput,
    FixCoordinatorAskUserOutput,
    FixOrchestratorOutput,
    FixPhaseCoordinatorOutput,
    FixPlannerOutput,
    FixPlanV2Output,
    FixReaderOutput,
    FixRedTeamerOutput,
    FixValidatorOutput,
    GroundingOutput,
    RedTeamReport,
)


def format_validation_error(error: dict[str, Any]) -> str:
    """Format Pydantic validation error with actionable hints."""
    location = ".".join(str(x) for x in error["loc"])
    message = error["msg"]
    error_type = error.get("type", "")

    formatted = f"- {location}: {message}"

    if "missing" in error_type:
        formatted += f"\n  Hint: Add '{location}' field to output"
    elif "enum" in error_type or "literal" in error_type:
        formatted += "\n  Hint: Check valid values in model definition"
    elif "type_error.float" in error_type or "greater_than" in error_type:
        formatted += "\n  Hint: Value must be numeric in valid range"
    elif "string_too_short" in error_type:
        formatted += "\n  Hint: Field requires more content"

    return formatted


# ============================================================================
# Agent Path to Validation Type Mapping
# ============================================================================

AGENT_TYPE_MAP = {
    "reasoning-attacker": "attacker",
    "context-attacker": "attacker",
    "hallucination-prober": "attacker",
    "scope-analyzer": "attacker",
    "attack-strategist": "strategy",
    "context-analyzer": "context",
    "evidence-checker": "grounding",
    "proportion-checker": "grounding",
    "alternative-explorer": "grounding",
    "calibrator": "grounding",
    "insight-synthesizer": "report",
    "fix-planner": "fix_planner",
    "fix-coordinator": "fix_coordinator",
    # Fix orchestration agents
    "fix-orchestrator": "fix_orchestrator",
    "fix-phase-coordinator": "fix_phase_coordinator",
    "fix-reader": "fix_reader",
    "fix-planner-v2": "fix_planner_v2",
    "fix-red-teamer": "fix_red_teamer",
    "fix-applicator": "fix_applicator",
    "fix-committer": "fix_committer",
    "fix-validator": "fix_validator",
}

MODEL_MAP = {
    "attacker": AttackerOutput,
    "strategy": AttackStrategyOutput,
    "context": ContextAnalysisOutput,
    "grounding": GroundingOutput,
    "report": RedTeamReport,
    "fix_planner": FixPlannerOutput,
    "fix_coordinator": FixCoordinatorAskUserOutput,
    # Fix orchestration models
    "fix_orchestrator": FixOrchestratorOutput,
    "fix_phase_coordinator": FixPhaseCoordinatorOutput,
    "fix_reader": FixReaderOutput,
    "fix_planner_v2": FixPlanV2Output,
    "fix_red_teamer": FixRedTeamerOutput,
    "fix_applicator": FixApplicatorOutput,
    "fix_committer": FixCommitterOutput,
    "fix_validator": FixValidatorOutput,
}


def extract_agent_name(tool_input: dict[str, Any]) -> str | None:
    """Extract agent name from Task tool input."""
    # The Task tool input might have 'prompt' or 'description' with agent path
    prompt = tool_input.get("prompt", "")
    description = tool_input.get("description", "")

    # Look for coordinator-internal agent paths
    for agent_name in AGENT_TYPE_MAP:
        if agent_name in prompt or agent_name in description:
            return agent_name
    return None


def extract_yaml_from_response(response: str) -> dict[str, Any] | None:
    """Extract YAML content from agent response."""
    # Try to find YAML block in response
    yaml_match = re.search(r"```ya?ml\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if yaml_match:
        try:
            return yaml.safe_load(yaml_match.group(1))
        except yaml.YAMLError:
            pass

    # Try parsing entire response as YAML
    try:
        return yaml.safe_load(response)
    except yaml.YAMLError:
        pass

    return None


def validate_output(data: dict[str, Any], output_type: str) -> tuple[bool, list[str]]:
    """Validate output against the appropriate model."""
    model = MODEL_MAP.get(output_type)
    if not model:
        return True, []  # Unknown type, skip validation

    try:
        model.model_validate(data)
        return True, []
    except ValidationError as e:
        errors = [format_validation_error(err) for err in e.errors()]
        return False, errors


def main() -> None:
    """Process PostToolUse hook input and validate agent output."""
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON, skip
        print("decision: continue")
        return

    # Check if this is a Task tool invocation
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Task":
        print("decision: continue")
        return

    # Extract agent name from tool input
    tool_input = hook_input.get("tool_input", {})
    agent_name = extract_agent_name(tool_input)

    if not agent_name:
        # Not a red-agent sub-agent, skip
        print("decision: continue")
        return

    # Get output type for this agent
    output_type = AGENT_TYPE_MAP.get(agent_name)
    if not output_type:
        print("decision: continue")
        return

    # Extract agent response
    tool_response = hook_input.get("tool_response", "")
    if isinstance(tool_response, dict):
        tool_response = tool_response.get("result", "")

    # Parse YAML from response
    parsed_output = extract_yaml_from_response(str(tool_response))

    if not parsed_output:
        # Could not parse YAML - block and request fix
        error_message = (
            f"YAML parse error in {agent_name} output. "
            "Could not find valid YAML block. "
            "Please wrap output in ```yaml ... ``` with valid YAML syntax."
        )
        print("decision: block")
        print("reason: |")
        for line in error_message.split("\n"):
            print(f"  {line}")
        return

    # Validate against model
    is_valid, errors = validate_output(parsed_output, output_type)

    if is_valid:
        # Success - pass silently (no message to user)
        print("decision: continue")
    else:
        # Validation failed - block with specific errors
        error_list = "\n".join(errors[:5])  # Limit to first 5 errors
        error_message = (
            f"Validation failed for {agent_name} output:\n{error_list}\n"
            "Please fix these fields and regenerate the output."
        )
        print("decision: block")
        print("reason: |")
        for line in error_message.split("\n"):
            print(f"  {line}")


if __name__ == "__main__":
    main()
