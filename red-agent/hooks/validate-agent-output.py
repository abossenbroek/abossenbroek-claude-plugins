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
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

# ============================================================================
# Inline Pydantic Models (subset needed for validation)
# ============================================================================


class AttackerFinding(BaseModel):
    """A single finding from an attacker agent."""

    id: str
    title: str
    severity: str
    confidence: str | int | float
    evidence: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2,3}-\d{3}$", v):
            msg = f"ID must match pattern XX-NNN or XXX-NNN, got: {v}"
            raise ValueError(msg)
        return v


class AttackerOutput(BaseModel):
    """Output from attacker agents."""

    attack_results: dict[str, Any]


class GroundingAssessment(BaseModel):
    """Assessment of a single finding's grounding."""

    finding_id: str
    status: str
    evidence_strength: float = Field(ge=0.0, le=1.0)


class GroundingOutput(BaseModel):
    """Output from grounding agents."""

    grounding_results: dict[str, Any]
    agent: str


class ContextAnalysisOutput(BaseModel):
    """Output from context analyzer."""

    context_analysis: dict[str, Any]


class AttackStrategyOutput(BaseModel):
    """Output from attack strategist."""

    attack_strategy: dict[str, Any]


class RedTeamReport(BaseModel):
    """Final synthesized report."""

    executive_summary: str = Field(min_length=50)
    risk_level: str
    findings: list[dict[str, Any]] = Field(default_factory=list)


class FixOption(BaseModel):
    """A single fix option for a finding."""

    label: str
    description: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    complexity: str  # LOW, MEDIUM, HIGH
    affected_components: list[str] = Field(default_factory=list)

    @field_validator("complexity")
    @classmethod
    def validate_complexity(cls, v: str) -> str:
        valid = {"LOW", "MEDIUM", "HIGH"}
        if v.upper() not in valid:
            msg = f"Complexity must be LOW, MEDIUM, or HIGH, got: {v}"
            raise ValueError(msg)
        return v.upper()


class FixPlannerOutput(BaseModel):
    """Output from fix-planner agent."""

    finding_id: str
    finding_title: str
    options: list[FixOption] = Field(min_length=1, max_length=3)


class FindingWithFixes(BaseModel):
    """A finding with its fix options."""

    finding_id: str
    title: str
    severity: str
    options: list[FixOption] = Field(min_length=1, max_length=3)


class FixCoordinatorOutput(BaseModel):
    """Output from fix-coordinator agent (legacy format)."""

    findings_with_fixes: list[FindingWithFixes] = Field(default_factory=list)


# Valid severity levels for question batches
QUESTION_BATCH_SEVERITY_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "CRITICAL_HIGH"}


class AskUserQuestionOption(BaseModel):
    """Option for AskUserQuestion (matches Claude Code schema)."""

    label: str
    description: str


class AskUserQuestion(BaseModel):
    """A question for AskUserQuestion (matches Claude Code schema)."""

    question: str = Field(min_length=10)
    header: str = Field(max_length=12)
    multiSelect: bool
    options: list[AskUserQuestionOption] = Field(min_length=2, max_length=4)


class QuestionBatch(BaseModel):
    """A batch of questions grouped by severity."""

    batch_number: int = Field(ge=1)
    severity_level: str
    questions: list[AskUserQuestion] = Field(min_length=1, max_length=4)

    @field_validator("severity_level")
    @classmethod
    def validate_severity_level(cls, v: str) -> str:
        if v not in QUESTION_BATCH_SEVERITY_LEVELS:
            msg = f"Severity '{v}' must be one of {QUESTION_BATCH_SEVERITY_LEVELS}"
            raise ValueError(msg)
        return v


class FindingDetailOption(BaseModel):
    """Full option details for implementation summary."""

    label: str
    description: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    complexity: str
    affected_components: list[str] = Field(default_factory=list)

    @field_validator("complexity")
    @classmethod
    def validate_complexity(cls, v: str) -> str:
        valid = {"LOW", "MEDIUM", "HIGH"}
        if v.upper() not in valid:
            msg = f"Complexity must be LOW, MEDIUM, or HIGH, got: {v}"
            raise ValueError(msg)
        return v.upper()


class FindingDetail(BaseModel):
    """Full finding details for implementation summary."""

    finding_id: str
    title: str
    severity: str
    full_options: list[FindingDetailOption] = Field(min_length=1, max_length=3)


class FixCoordinatorAskUserOutput(BaseModel):
    """Output from fix-coordinator in AskUserQuestion-compatible format."""

    question_batches: list[QuestionBatch] = Field(min_length=1)
    finding_details: list[FindingDetail] = Field(default_factory=list)


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
}

MODEL_MAP = {
    "attacker": AttackerOutput,
    "strategy": AttackStrategyOutput,
    "context": ContextAnalysisOutput,
    "grounding": GroundingOutput,
    "report": RedTeamReport,
    "fix_planner": FixPlannerOutput,
    "fix_coordinator": FixCoordinatorAskUserOutput,
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
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return False, errors


def main() -> None:
    """Process PostToolUse hook input and validate agent output."""
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Not valid JSON, skip
        print(json.dumps({"continue": True}))
        return

    # Check if this is a Task tool invocation
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Task":
        print(json.dumps({"continue": True}))
        return

    # Extract agent name from tool input
    tool_input = hook_input.get("tool_input", {})
    agent_name = extract_agent_name(tool_input)

    if not agent_name:
        # Not a red-agent sub-agent, skip
        print(json.dumps({"continue": True}))
        return

    # Get output type for this agent
    output_type = AGENT_TYPE_MAP.get(agent_name)
    if not output_type:
        print(json.dumps({"continue": True}))
        return

    # Extract agent response
    tool_response = hook_input.get("tool_response", "")
    if isinstance(tool_response, dict):
        tool_response = tool_response.get("result", "")

    # Parse YAML from response
    parsed_output = extract_yaml_from_response(str(tool_response))

    if not parsed_output:
        # Could not parse YAML - block and request fix
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        f"YAML parse error in {agent_name} output. "
                        "Could not find valid YAML block. "
                        "Please wrap output in ```yaml ... ``` with valid YAML syntax."
                    ),
                }
            )
        )
        return

    # Validate against model
    is_valid, errors = validate_output(parsed_output, output_type)

    if is_valid:
        # Success - pass silently (no message to user)
        print(json.dumps({"continue": True}))
    else:
        # Validation failed - block with specific errors
        error_list = "\n- ".join(errors[:5])  # Limit to first 5 errors
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        f"Validation failed for {agent_name} output:\n- {error_list}\n"
                        "Please fix these fields and regenerate the output."
                    ),
                }
            )
        )


if __name__ == "__main__":
    main()
