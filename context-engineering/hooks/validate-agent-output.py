#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pydantic>=2.0", "pyyaml"]
# ///
"""PostToolUse hook validator for context-engineering agent outputs.

This script validates agent outputs against Pydantic models by:
1. Reading agent output from stdin
2. Extracting YAML from the output
3. Detecting agent type from YAML structure
4. Validating against the appropriate Pydantic model

Exit codes:
- 0: Validation passed
- 1: Validation failed
"""

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
from context_engineering.models import (
    ChallengeAssessment,
    ConsistencyCheck,
    ContextFlowMap,
    ContextImprovement,
    HandoffImprovement,
    ImprovementReport,
    OrchestrationImprovement,
    PatternCompliance,
    PlanAnalysis,
    PluginAnalysis,
    RiskAssessment,
    TokenEstimate,
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


# Map agent names to their Pydantic models
AGENT_TYPE_MAP = {
    "plugin-analyzer": PluginAnalysis,
    "plan-analyzer": PlanAnalysis,
    "context-flow-mapper": ContextFlowMap,
    "context-optimizer": ContextImprovement,
    "orchestration-improver": OrchestrationImprovement,
    "handoff-improver": HandoffImprovement,
    "pattern-checker": PatternCompliance,
    "token-estimator": TokenEstimate,
    "consistency-checker": ConsistencyCheck,
    "risk-assessor": RiskAssessment,
    "challenger": ChallengeAssessment,  # Validates list of assessments
    "improvement-synthesizer": ImprovementReport,
    "audit-synthesizer": ImprovementReport,  # Same model as improvement-synthesizer
}

# Map YAML root keys to agent types (for structure-based detection)
ROOT_KEY_MAP = {
    "plugin_analysis": "plugin-analyzer",
    "plan_analysis": "plan-analyzer",
    "context_flow_map": "context-flow-mapper",
    "improvements": "context-optimizer",  # Can be optimizer, orch, or handoff
    "improvement_report": "improvement-synthesizer",
    "challenge_assessments": "challenger",
}


def extract_yaml_from_output(output: str) -> str | None:
    """Extract YAML content from agent output.

    Handles both:
    - YAML in code blocks: ```yaml ... ```
    - Raw YAML output
    """
    # Try to extract from code block first
    code_block_pattern = r"```yaml\s*\n(.*?)\n```"
    match = re.search(code_block_pattern, output, re.DOTALL)
    if match:
        return match.group(1)

    # Check if output is raw YAML (contains keys with colons)
    if ":" in output and ("\n" in output or len(output) < 500):
        # Likely raw YAML
        return output

    return None


def detect_agent_type_from_yaml(data: dict[str, Any]) -> str | None:
    """Detect agent type from YAML structure.

    Uses root keys to determine which agent produced the output.
    """
    # Check root keys
    for root_key, agent_type in ROOT_KEY_MAP.items():
        if root_key in data:
            # Special handling for improvements - could be multiple types
            if root_key == "improvements":
                return detect_improvement_type(data)
            return agent_type

    return None


def detect_improvement_type(data: dict[str, Any]) -> str:
    """Detect which improvement agent from the improvements structure.

    Context improvements have: file, improvement_type, code_change
    Orchestration improvements have: current_structure, proposed_structure
    Handoff improvements have: transition, current_handoff, optimized_handoff
    """
    improvements = data.get("improvements", [])
    if not improvements:
        return "context-optimizer"  # Default

    first = improvements[0]

    # Check for handoff-specific fields
    if "transition" in first or "current_handoff" in first:
        return "handoff-improver"

    # Check for orchestration-specific fields
    if "current_structure" in first or "proposed_structure" in first:
        return "orchestration-improver"

    # Default to context optimizer
    return "context-optimizer"


def _extract_validation_data(  # noqa: PLR0911
    data: dict[str, Any], agent_type: str
) -> tuple[Any, str | None]:
    """Extract validation data from parsed YAML based on agent type.

    Returns:
        Tuple of (validation_data, error_message)
    """
    # Most agents wrap their output in a root key matching their type
    if agent_type == "plugin-analyzer":
        return data.get("plugin_analysis", {}), None
    if agent_type == "plan-analyzer":
        return data.get("plan_analysis", {}), None
    if agent_type == "context-flow-mapper":
        return data.get("context_flow_map", {}), None
    if agent_type in {"improvement-synthesizer", "audit-synthesizer"}:
        return data.get("improvement_report", {}), None

    # Improvement agents
    if agent_type in {
        "context-optimizer",
        "orchestration-improver",
        "handoff-improver",
    }:
        improvements = data.get("improvements", [])
        if not improvements:
            return None, "No improvements found in output"
        return improvements[0], None

    # Grounding agents
    if agent_type in {
        "pattern-checker",
        "token-estimator",
        "consistency-checker",
        "risk-assessor",
    }:
        assessments = data.get("assessments", [])
        if not assessments:
            return None, "No assessments found in output"
        return assessments[0], None

    # Challenger agent (returns list of assessments)
    if agent_type == "challenger":
        assessments = data.get("challenge_assessments", [])
        if not assessments:
            return None, "No challenge_assessments found in output"
        return assessments[0], None

    # Default
    return data, None


def validate_agent_output(output: str) -> tuple[bool, str]:  # noqa: PLR0911
    """Validate agent output against Pydantic models.

    Returns:
        Tuple of (is_valid, message)
    """
    # Extract YAML
    yaml_content = extract_yaml_from_output(output)
    if not yaml_content:
        return False, "No YAML content found in output"

    # Parse YAML
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(data, dict):
        return False, f"Expected YAML dict, got {type(data).__name__}"

    # Detect agent type
    agent_type = detect_agent_type_from_yaml(data)
    if not agent_type:
        available_keys = list(data.keys())
        return (
            False,
            f"Cannot detect agent type. Root keys: {available_keys}",
        )

    # Get appropriate model
    model_class = AGENT_TYPE_MAP.get(agent_type)
    if not model_class:
        return False, f"No validation model for agent type: {agent_type}"

    # Extract the data for validation
    validation_data, error_msg = _extract_validation_data(data, agent_type)
    if error_msg:
        return False, error_msg

    # Validate against model
    try:
        model_class.model_validate(validation_data)
        return True, f"VALID ({agent_type})"
    except ValidationError as e:
        # Format validation errors with actionable hints
        errors = [format_validation_error(err) for err in e.errors()]
        error_msg = "\n".join(errors)
        return False, f"INVALID ({agent_type}):\n{error_msg}"


def main() -> None:
    """Main entry point for the validation hook."""
    # Read agent output from stdin
    output = sys.stdin.read()

    if not output.strip():
        print("decision: block")
        print("reason: |")
        print("  INVALID: Empty output")
        return

    # Validate
    is_valid, message = validate_agent_output(output)

    if is_valid:
        print("decision: continue")
    else:
        print("decision: block")
        print("reason: |")
        for line in message.split("\n"):
            print(f"  {line}")


if __name__ == "__main__":
    main()
