#!/usr/bin/env python3
"""Runtime validator for red team agent outputs.

Validates sub-agent outputs during execution to catch:
- Missing required fields
- Invalid severity/confidence values
- Findings without evidence
- Grounding results without proper scores

Uses Pydantic models for type-safe validation.

Usage:
    from validate_agent_output import validate_attacker_output
    python validate_agent_output.py --type attacker --input output.yaml
"""

import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# Import Pydantic models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import (
    AttackerOutput,
    ContextAnalysisOutput,
    GroundingOutput,
    RedTeamReport,
    RiskCategoryName,
)


class ValidationResult:
    """Result of validation with errors and warnings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        lines: list[str] = []
        if self.errors:
            lines.append(f"ERRORS ({len(self.errors)}):")
            lines.extend(f"  - {e}" for e in self.errors)
        if self.warnings:
            lines.append(f"WARNINGS ({len(self.warnings)}):")
            lines.extend(f"  - {w}" for w in self.warnings)
        if not lines:
            lines.append("Validation passed")
        return "\n".join(lines)


def _pydantic_errors_to_result(exc: ValidationError) -> ValidationResult:
    """Convert Pydantic ValidationError to ValidationResult."""
    result = ValidationResult()
    for error in exc.errors():
        loc = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]
        result.add_error(f"{loc}: {msg}")
    return result


def _add_attacker_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in attacker output."""
    attack = data.get("attack_results", {})
    findings = attack.get("findings", [])
    if len(findings) == 0:
        result.add_warning("No findings reported - verify this is intentional")
    for idx, finding in enumerate(findings):
        finding_id = finding.get("id", "unknown")
        if "evidence" not in finding:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing 'evidence' field"
            )
        if "recommendation" not in finding:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing 'recommendation' field"
            )
    # Check for unknown risk categories
    valid_categories = {cat.value for cat in RiskCategoryName}
    for cat in attack.get("categories_probed", []):
        if cat not in valid_categories:
            result.add_warning(f"Unknown risk category: '{cat}'")


def _add_grounding_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in grounding output."""
    grounding = data.get("grounding_results", {})
    for idx, assessment in enumerate(grounding.get("assessments", [])):
        if "adjusted_confidence" not in assessment:
            result.add_warning(f"Assessment [{idx}]: missing 'adjusted_confidence'")
        if "notes" not in assessment:
            result.add_warning(
                f"Assessment [{idx}]: missing 'notes' - explain rationale"
            )


def _add_context_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in context output."""
    analysis = data.get("context_analysis", {})
    for idx, claim in enumerate(analysis.get("claim_analysis", [])):
        if "risk_level" not in claim:
            result.add_warning(f"Claim [{idx}]: missing 'risk_level'")


def _add_report_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in report output."""
    if "limitations" not in data:
        result.add_warning("Missing 'limitations' section")
    summary = data.get("executive_summary", "")
    if len(str(summary)) < 50:
        result.add_warning("Executive summary seems too short")


# Mapping of output types to warning functions
_WARNING_FUNCS = {
    "attacker": _add_attacker_warnings,
    "grounding": _add_grounding_warnings,
    "context": _add_context_warnings,
    "report": _add_report_warnings,
}


def _add_warnings_for_missing_optional(
    data: dict[str, Any],
    result: ValidationResult,
    output_type: str,
) -> None:
    """Add warnings for missing optional fields (not enforced by Pydantic)."""
    warning_func = _WARNING_FUNCS.get(output_type)
    if warning_func:
        warning_func(data, result)


def validate_attacker_output(data: dict[str, Any]) -> ValidationResult:
    """Validate attacker agent output structure using Pydantic.

    Expected format:
    ```yaml
    attack_results:
      attack_type: [attacker name]
      categories_probed: [list]
      findings:
        - id: XX-NNN
          severity: HIGH
          title: "..."
          confidence: 0.85
    ```
    """
    try:
        AttackerOutput.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "attacker")
    return result


def validate_grounding_output(data: dict[str, Any]) -> ValidationResult:
    """Validate grounding agent output structure using Pydantic.

    Expected format:
    ```yaml
    grounding_results:
      agent: [grounding agent name]
      assessments:
        - finding_id: XX-NNN
          evidence_strength: 0.85
          adjusted_confidence: 0.80
          notes: "..."
    ```
    """
    try:
        GroundingOutput.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "grounding")
    return result


def validate_context_analysis(data: dict[str, Any]) -> ValidationResult:
    """Validate context analyzer output structure using Pydantic.

    Expected format:
    ```yaml
    context_analysis:
      summary: {...}
      claim_analysis: [...]
      reasoning_patterns: [...]
      risk_surface: {...}
    ```
    """
    try:
        ContextAnalysisOutput.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "context")
    return result


def validate_final_report(data: dict[str, Any]) -> ValidationResult:
    """Validate final synthesized report structure using Pydantic.

    Expected format:
    ```yaml
    executive_summary: "..."
    risk_overview:
      overall_risk_level: HIGH
      categories: [...]
    findings:
      critical: [...]
      high: [...]
    ```
    """
    try:
        RedTeamReport.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "report")
    return result


def validate_yaml_string(yaml_str: str, output_type: str) -> ValidationResult:
    """Validate a YAML string based on output type."""
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        result = ValidationResult()
        result.add_error(f"Invalid YAML: {e}")
        return result

    return validate_output(data, output_type)


def validate_output(data: dict[str, Any], output_type: str) -> ValidationResult:
    """Validate agent output based on type.

    Args:
        data: Parsed YAML/dict output from agent
        output_type: One of 'attacker', 'grounding', 'context', 'report'

    Returns:
        ValidationResult with errors and warnings
    """
    validators = {
        "attacker": validate_attacker_output,
        "grounding": validate_grounding_output,
        "context": validate_context_analysis,
        "report": validate_final_report,
    }

    if output_type not in validators:
        result = ValidationResult()
        valid_types = list(validators.keys())
        result.add_error(f"Unknown output type: {output_type}. Valid: {valid_types}")
        return result

    return validators[output_type](data)


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate red team agent outputs")
    parser.add_argument(
        "--type",
        "-t",
        required=True,
        choices=["attacker", "grounding", "context", "report"],
        help="Type of output to validate",
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to YAML file or '-' for stdin",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    if args.input == "-":
        content = sys.stdin.read()
    else:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: File not found: {path}")
            return 1
        content = path.read_text()

    result = validate_yaml_string(content, args.type)
    print(result)

    if not result.is_valid:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
