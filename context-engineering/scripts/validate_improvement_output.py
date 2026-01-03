#!/usr/bin/env python3
"""Validate context-engineering sub-agent outputs.

This script validates YAML outputs from context-engineering agents
against their Pydantic schemas.

Usage:
    python validate_improvement_output.py < output.yaml
    python validate_improvement_output.py --file output.yaml
    python validate_improvement_output.py --type analysis < output.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

if TYPE_CHECKING:
    from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from context_engineering.models import (
    ConsistencyCheck,
    ContextFlowMap,
    ContextImprovement,
    HandoffImprovement,
    ImprovementReport,
    OrchestrationImprovement,
    PatternCompliance,
    PluginAnalysis,
    RiskAssessment,
    TokenEstimate,
)

# Model mapping by output type
OUTPUT_MODELS = {
    # Analysis outputs
    "plugin_analysis": PluginAnalysis,
    "context_flow_map": ContextFlowMap,
    # Improvement outputs (lists)
    "context_improvements": ContextImprovement,
    "orchestration_improvements": OrchestrationImprovement,
    "handoff_improvements": HandoffImprovement,
    # Grounding outputs (lists)
    "pattern_check_results": PatternCompliance,
    "token_estimate_results": TokenEstimate,
    "consistency_check_results": ConsistencyCheck,
    "risk_assessment_results": RiskAssessment,
    # Synthesis outputs
    "improvement_report": ImprovementReport,
}


def detect_output_type(data: dict[str, Any]) -> str | None:
    """Detect output type from YAML structure."""
    for key in OUTPUT_MODELS:
        if key in data:
            return key
    return None


def validate_single(model_class: type, data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a single object against a model."""
    errors = []
    try:
        model_class(**data)
    except ValidationError as e:
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            errors.append(f"  {loc}: {error['msg']}")
    return len(errors) == 0, errors


def validate_list(
    model_class: type, items: list[dict[str, Any]], key: str
) -> tuple[bool, list[str]]:
    """Validate a list of objects against a model."""
    all_errors = []
    for i, item in enumerate(items):
        is_valid, errors = validate_single(model_class, item)
        if not is_valid:
            all_errors.append(f"  {key}[{i}]:")
            all_errors.extend(f"    {e}" for e in errors)
    return len(all_errors) == 0, all_errors


def validate_output(  # noqa: PLR0911
    yaml_content: str, output_type: str | None = None
) -> tuple[bool, list[str]]:
    """Validate YAML output against appropriate schema.

    Args:
        yaml_content: YAML string to validate
        output_type: Optional explicit output type

    Returns:
        Tuple of (is_valid, error_messages)
    """
    # Parse YAML
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return False, ["Output must be a YAML mapping"]

    # Detect or use provided output type
    detected_type = output_type or detect_output_type(data)
    if not detected_type:
        return False, [
            f"Unknown output type. Expected one of: {list(OUTPUT_MODELS.keys())}"
        ]

    model_class = OUTPUT_MODELS.get(detected_type)
    if not model_class:
        return False, [f"No model for output type: {detected_type}"]

    # Get the data to validate
    output_data = data.get(detected_type, data)

    # Handle list outputs (improvements, assessments)
    if detected_type.endswith("_improvements"):
        items_key = "improvements"
        items = output_data.get(items_key, [])
        if not items:
            return False, [f"No {items_key} found in output"]
        return validate_list(model_class, items, items_key)

    if detected_type.endswith("_results"):
        items_key = "assessments"
        items = output_data.get(items_key, [])
        if not items:
            return False, [f"No {items_key} found in output"]
        return validate_list(model_class, items, items_key)

    # Handle single object outputs
    return validate_single(model_class, output_data)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate context-engineering outputs")
    parser.add_argument("--file", "-f", help="YAML file to validate")
    parser.add_argument(
        "--type",
        "-t",
        choices=list(OUTPUT_MODELS.keys()),
        help="Explicit output type",
    )
    args = parser.parse_args()

    # Read input
    content = Path(args.file).read_text() if args.file else sys.stdin.read()

    # Validate
    is_valid, errors = validate_output(content, args.type)

    # Output result
    if is_valid:
        print("VALID")
        return 0

    print("INVALID")
    print("Errors:")
    for error in errors:
        print(error)
    return 1


if __name__ == "__main__":
    sys.exit(main())
