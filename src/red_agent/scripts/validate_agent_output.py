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

import argparse
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
from red_agent.models import (
    AttackerOutput,
    AttackStrategyOutput,
    CodeAttackerOutput,
    ContextAnalysisOutput,
    DiffAnalysisOutput,
    GroundingOutput,
    PRRedTeamReport,
    RedTeamReport,
    RiskCategoryName,
)

# Minimum length for executive summary (characters)
MIN_SUMMARY_LENGTH = 50


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
    if len(str(summary)) < MIN_SUMMARY_LENGTH:
        result.add_warning("Executive summary seems too short")


def _add_strategy_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in strategy output."""
    strategy = data.get("attack_strategy", {})
    if not strategy.get("selected_vectors"):
        result.add_warning("No attack vectors selected")
    if not strategy.get("attacker_assignments"):
        result.add_warning("No attacker assignments defined")


def _add_diff_analysis_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in diff analysis output."""
    analysis = data.get("diff_analysis", {})
    if not analysis:
        result.add_warning("Empty diff_analysis section")
        return

    # Check for key sections
    if "summary" not in analysis:
        result.add_warning("Missing 'summary' section in diff_analysis")
    if "file_analysis" not in analysis or not analysis.get("file_analysis"):
        result.add_warning("Missing or empty 'file_analysis' section")
    if "risk_surface" not in analysis or not analysis.get("risk_surface"):
        result.add_warning("Missing or empty 'risk_surface' section")

    # Check file analysis completeness
    for idx, file_item in enumerate(analysis.get("file_analysis", [])):
        if "risk_factors" not in file_item or not file_item["risk_factors"]:
            result.add_warning(
                f"File [{idx}]: missing or empty 'risk_factors' "
                "- explain risk rationale"
            )
        if "line_ranges" not in file_item or not file_item["line_ranges"]:
            result.add_warning(
                f"File [{idx}]: missing or empty 'line_ranges' - specify affected lines"
            )


def _add_code_attacker_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in code attacker output."""
    attack = data.get("attack_results", {})
    if not attack:
        result.add_warning("Empty attack_results section")
        return

    # Check for findings
    findings = attack.get("findings", [])
    if len(findings) == 0:
        result.add_warning("No findings reported - verify this is intentional")

    # Validate each finding has proper structure
    for idx, finding in enumerate(findings):
        finding_id = finding.get("id", "unknown")

        # Check target information
        target = finding.get("target", {})
        if not target:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing 'target' field"
            )
        elif "line_numbers" not in target or not target["line_numbers"]:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing line numbers in target"
            )

        # Check evidence
        if "evidence" not in finding:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing 'evidence' field"
            )

        # Check attack applied
        if "attack_applied" not in finding:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing 'attack_applied' field"
            )

        # Check recommendation
        if "recommendation" not in finding:
            result.add_warning(
                f"Finding [{idx}] ({finding_id}): missing 'recommendation' field"
            )

    # Check summary
    if "summary" not in attack:
        result.add_warning("Missing 'summary' section in attack_results")


def _add_pr_report_warnings(data: dict[str, Any], result: ValidationResult) -> None:
    """Add warnings for missing optional fields in PR report output."""
    if "test_coverage_notes" not in data:
        result.add_warning("Missing 'test_coverage_notes' - consider test coverage")
    summary = data.get("executive_summary", "")
    if len(str(summary)) < MIN_SUMMARY_LENGTH:
        result.add_warning("Executive summary seems too short")
    if not data.get("findings"):
        result.add_warning("No findings reported - verify this is intentional")
    if not data.get("recommendations"):
        result.add_warning("No recommendations provided")


# Mapping of output types to warning functions
_WARNING_FUNCS = {
    "attacker": _add_attacker_warnings,
    "grounding": _add_grounding_warnings,
    "context": _add_context_warnings,
    "report": _add_report_warnings,
    "strategy": _add_strategy_warnings,
    "diff_analysis": _add_diff_analysis_warnings,
    "code_attacker": _add_code_attacker_warnings,
    "pr_report": _add_pr_report_warnings,
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


def validate_strategy_output(data: dict[str, Any]) -> ValidationResult:
    """Validate attack strategy output structure using Pydantic.

    Expected format:
    ```yaml
    attack_strategy:
      mode: standard
      total_vectors: 5
      selected_vectors:
        - category: reasoning-flaws
          priority: 1
          rationale: "..."
      attacker_assignments:
        reasoning-attacker:
          categories: [reasoning-flaws, assumption-gaps]
    ```
    """
    try:
        AttackStrategyOutput.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "strategy")
    return result


def validate_diff_analysis(data: dict[str, Any]) -> ValidationResult:
    """Validate diff analyzer output structure using Pydantic.

    Expected format:
    ```yaml
    diff_analysis:
      summary:
        files_changed: 5
        high_risk_files: 2
        medium_risk_files: 2
        low_risk_files: 1
        total_insertions: 150
        total_deletions: 30
      file_analysis:
        - file_id: "auth_handler_001"
          path: "src/auth/handler.ts"
          risk_level: high
          risk_score: 0.85
          change_summary: "..."
          risk_factors: ["authentication", "validation"]
          line_ranges: [[45, 67]]
          change_type: modification
          insertions: 22
          deletions: 5
      risk_surface:
        - category: "reasoning-flaws"
          exposure: high
          affected_files: ["auth_handler_001"]
          notes: "..."
      patterns_detected:
        - pattern: "error-handling-changes"
          description: "..."
          instances: 3
          affected_files: [...]
          risk_implication: "..."
      high_risk_files: ["auth_handler_001"]
      focus_areas:
        - area: "authentication"
          files: ["auth_handler_001"]
          rationale: "..."
      key_observations: ["..."]
    ```
    """
    try:
        DiffAnalysisOutput.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "diff_analysis")
    return result


def validate_code_attacker(data: dict[str, Any]) -> ValidationResult:
    """Validate code reasoning attacker output structure using Pydantic.

    Expected format:
    ```yaml
    attack_results:
      attack_type: code-reasoning-attacker
      categories_probed:
        - logic-errors
        - assumption-gaps
        - edge-case-handling
      findings:
        - id: LE-001
          category: logic-errors
          severity: HIGH
          title: "..."
          target:
            file_path: "src/file.ts"
            line_numbers: [47, 52]
            diff_snippet: |
              ...
            function_name: "authenticate"
          evidence:
            type: control_flow_error
            description: "..."
            code_quote: "..."
          attack_applied:
            style: "control-flow-tracing"
            probe: "..."
          impact:
            if_exploited: "..."
            affected_functionality: "..."
          recommendation: "..."
          confidence: 0.85
      patterns_detected:
        - pattern: "error-handling-gaps"
          instances: 2
          files_affected: ["file1.ts", "file2.ts"]
          description: "..."
          systemic_recommendation: "..."
      summary:
        total_findings: 3
        by_severity:
          critical: 0
          high: 2
          medium: 1
          low: 0
          info: 0
        highest_risk_file: "src/auth.ts"
        primary_weakness: "..."
    ```
    """
    try:
        CodeAttackerOutput.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "code_attacker")
    return result


def validate_pr_report(data: dict[str, Any]) -> ValidationResult:
    """Validate PR red team report structure using Pydantic.

    Expected format:
    ```yaml
    executive_summary: "..."
    pr_summary:
      files_changed: 5
      additions: 150
      deletions: 30
      pr_size: medium
    risk_level: HIGH
    findings:
      - id: PR-001
        severity: HIGH
        title: "..."
    breaking_changes: [...]
    ```
    """
    try:
        PRRedTeamReport.model_validate(data)
        result = ValidationResult()
    except ValidationError as e:
        result = _pydantic_errors_to_result(e)

    _add_warnings_for_missing_optional(data, result, "pr_report")
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
        output_type: One of 'attacker', 'grounding', 'context', 'report', 'strategy',
                    'diff_analysis', 'code_attacker', 'pr_report'

    Returns:
        ValidationResult with errors and warnings
    """
    validators = {
        "attacker": validate_attacker_output,
        "grounding": validate_grounding_output,
        "context": validate_context_analysis,
        "report": validate_final_report,
        "strategy": validate_strategy_output,
        "diff_analysis": validate_diff_analysis,
        "code_attacker": validate_code_attacker,
        "pr_report": validate_pr_report,
    }

    if output_type not in validators:
        result = ValidationResult()
        valid_types = list(validators.keys())
        result.add_error(f"Unknown output type: {output_type}. Valid: {valid_types}")
        return result

    return validators[output_type](data)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate red team agent outputs")
    parser.add_argument(
        "--type",
        "-t",
        required=True,
        choices=[
            "attacker",
            "grounding",
            "context",
            "report",
            "strategy",
            "diff_analysis",
            "code_attacker",
            "pr_report",
        ],
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
