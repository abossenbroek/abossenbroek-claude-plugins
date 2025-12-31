#!/usr/bin/env python3
"""Runtime validator for red team agent outputs.

Validates sub-agent outputs during execution to catch:
- Missing required fields
- Invalid severity/confidence values
- Findings without evidence
- Grounding results without proper scores

Usage:
    from validate_agent_output import validate_attacker_output
    python validate_agent_output.py --type attacker --input output.yaml
"""

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)


SEVERITY_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
CONFIDENCE_LEVELS = {
    "exploring",
    "low",
    "medium",
    "high",
    "very_high",
    "almost_certain",
    "certain",
}
RISK_CATEGORIES = {
    "reasoning-flaws",
    "assumption-gaps",
    "context-manipulation",
    "authority-exploitation",
    "information-leakage",
    "hallucination-risks",
    "over-confidence",
    "scope-creep",
    "dependency-blindness",
    "temporal-inconsistency",
}


class ValidationError(Exception):
    """Raised when agent output validation fails."""


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


def _validate_finding_required(
    finding: dict[str, Any],
    idx: int,
    result: ValidationResult,
) -> None:
    """Validate required fields in a finding."""
    if "id" not in finding:
        result.add_error(f"Finding [{idx}]: missing 'id' field")
    elif not isinstance(finding["id"], str):
        result.add_error(f"Finding [{idx}]: 'id' must be string")

    if "severity" not in finding:
        result.add_error(f"Finding [{idx}]: missing 'severity' field")
    elif finding["severity"] not in SEVERITY_LEVELS:
        sev = finding["severity"]
        result.add_error(f"Finding [{idx}]: invalid severity '{sev}'")

    if "title" not in finding:
        result.add_error(f"Finding [{idx}]: missing 'title' field")


def _validate_finding_confidence(
    finding: dict[str, Any],
    idx: int,
    result: ValidationResult,
) -> None:
    """Validate confidence field in a finding."""
    if "confidence" not in finding:
        result.add_error(f"Finding [{idx}]: missing 'confidence' field")
        return

    conf = finding["confidence"]
    if isinstance(conf, int | float):
        if not 0.0 <= conf <= 1.0:
            result.add_error(
                f"Finding [{idx}]: confidence {conf} out of range [0.0, 1.0]"
            )
    elif isinstance(conf, str) and not conf.endswith("%"):
        result.add_warning(
            f"Finding [{idx}]: confidence '{conf}' should be numeric or %"
        )


def _validate_finding_optional(
    finding: dict[str, Any],
    idx: int,
    result: ValidationResult,
) -> None:
    """Validate optional fields in a finding."""
    finding_id = finding.get("id", "unknown")
    if "evidence" not in finding:
        result.add_warning(f"Finding [{idx}] ({finding_id}): missing 'evidence' field")
    if "recommendation" not in finding:
        result.add_warning(
            f"Finding [{idx}] ({finding_id}): missing 'recommendation' field"
        )


def validate_finding(
    finding: dict[str, Any],
    idx: int,
    result: ValidationResult,
) -> None:
    """Validate a single finding entry."""
    _validate_finding_required(finding, idx, result)
    _validate_finding_confidence(finding, idx, result)
    _validate_finding_optional(finding, idx, result)


def validate_attacker_output(data: dict[str, Any]) -> ValidationResult:
    """Validate attacker agent output structure.

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
    result = ValidationResult()

    if "attack_results" not in data:
        result.add_error("Missing 'attack_results' root key")
        return result

    attack = data["attack_results"]

    if "attack_type" not in attack:
        result.add_error("Missing 'attack_type' field")

    if "findings" not in attack:
        result.add_error("Missing 'findings' field")
        return result

    findings = attack["findings"]
    if not isinstance(findings, list):
        result.add_error("'findings' must be a list")
        return result

    if len(findings) == 0:
        result.add_warning("No findings reported - verify this is intentional")

    for idx, finding in enumerate(findings):
        validate_finding(finding, idx, result)

    if "categories_probed" in attack:
        for cat in attack["categories_probed"]:
            if cat not in RISK_CATEGORIES:
                result.add_warning(f"Unknown risk category: '{cat}'")

    return result


def validate_grounding_output(data: dict[str, Any]) -> ValidationResult:
    """Validate grounding agent output structure.

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
    result = ValidationResult()

    if "grounding_results" not in data:
        result.add_error("Missing 'grounding_results' root key")
        return result

    grounding = data["grounding_results"]

    if "agent" not in grounding:
        result.add_error("Missing 'agent' field")

    if "assessments" not in grounding:
        result.add_error("Missing 'assessments' field")
        return result

    assessments = grounding["assessments"]
    if not isinstance(assessments, list):
        result.add_error("'assessments' must be a list")
        return result

    for idx, assessment in enumerate(assessments):
        _validate_assessment(assessment, idx, result)

    return result


def _validate_assessment(
    assessment: dict[str, Any],
    idx: int,
    result: ValidationResult,
) -> None:
    """Validate a single grounding assessment."""
    if "finding_id" not in assessment:
        result.add_error(f"Assessment [{idx}]: missing 'finding_id'")

    if "evidence_strength" not in assessment:
        result.add_error(f"Assessment [{idx}]: missing 'evidence_strength'")
    else:
        strength = assessment["evidence_strength"]
        if isinstance(strength, int | float) and not 0.0 <= strength <= 1.0:
            result.add_error(
                f"Assessment [{idx}]: evidence_strength {strength} out of range"
            )

    if "adjusted_confidence" not in assessment:
        result.add_warning(f"Assessment [{idx}]: missing 'adjusted_confidence'")

    if "notes" not in assessment:
        result.add_warning(f"Assessment [{idx}]: missing 'notes' - explain rationale")


def validate_context_analysis(data: dict[str, Any]) -> ValidationResult:
    """Validate context analyzer output structure.

    Expected format:
    ```yaml
    context_analysis:
      summary: {...}
      claim_analysis: [...]
      reasoning_patterns: [...]
      risk_surface: {...}
    ```
    """
    result = ValidationResult()

    if "context_analysis" not in data:
        result.add_error("Missing 'context_analysis' root key")
        return result

    analysis = data["context_analysis"]

    required_sections = ["claim_analysis", "risk_surface"]
    for section in required_sections:
        if section not in analysis:
            result.add_error(f"Missing required section: '{section}'")

    if "claim_analysis" in analysis:
        claims = analysis["claim_analysis"]
        if not isinstance(claims, list):
            result.add_error("'claim_analysis' must be a list")
        else:
            for idx, claim in enumerate(claims):
                if "claim_id" not in claim:
                    result.add_error(f"Claim [{idx}]: missing 'claim_id'")
                if "risk_level" not in claim:
                    result.add_warning(f"Claim [{idx}]: missing 'risk_level'")

    return result


def validate_final_report(data: dict[str, Any]) -> ValidationResult:
    """Validate final synthesized report structure.

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
    result = ValidationResult()

    if "executive_summary" not in data:
        result.add_error("Missing 'executive_summary'")
    elif len(str(data["executive_summary"])) < 50:
        result.add_warning("Executive summary seems too short")

    if "risk_overview" not in data:
        result.add_error("Missing 'risk_overview'")
    else:
        overview = data["risk_overview"]
        if "overall_risk_level" not in overview:
            result.add_error("Missing 'overall_risk_level' in risk_overview")
        elif overview["overall_risk_level"] not in SEVERITY_LEVELS:
            level = overview["overall_risk_level"]
            result.add_error(f"Invalid overall_risk_level: {level}")

    if "findings" not in data:
        result.add_error("Missing 'findings' section")

    if "limitations" not in data:
        result.add_warning("Missing 'limitations' section")

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
