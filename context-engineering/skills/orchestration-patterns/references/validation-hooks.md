# Validation Hooks

Detailed guide to implementing PostToolUse validation with Pydantic models.

## Core Concept

Hooks intercept sub-agent outputs and validate before coordinator proceeds:

```
Sub-Agent Completes
        │
        ▼
┌─────────────────────┐
│   PostToolUse Hook  │
│   ┌───────────────┐ │
│   │ Parse YAML    │ │
│   │ Validate vs   │ │
│   │ Pydantic      │ │
│   │ Schema        │ │
│   └───────────────┘ │
└─────────────────────┘
        │
   ┌────┴────┐
   │         │
Valid    Invalid
   │         │
   ▼         ▼
Continue   Block
           + Error
           Details
```

## Hook Configuration

### Basic PostToolUse Hook

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "tool_name": "Task"
      },
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Validate the sub-agent output against expected schema..."
        }
      ]
    }
  ]
}
```

### Targeted Hook (Agent Pattern)

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "tool_name": "Task",
        "agent_pattern": "coordinator-internal/*"
      },
      "hooks": [
        {
          "type": "prompt",
          "prompt": "..."
        }
      ]
    }
  ]
}
```

### Multiple Hooks

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "tool_name": "Task",
        "agent_pattern": "coordinator-internal/grounding/*"
      },
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Validate grounding output..."
        }
      ]
    },
    {
      "event": "PostToolUse",
      "matcher": {
        "tool_name": "Task",
        "agent_pattern": "coordinator-internal/*-analyzer.md"
      },
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Validate analysis output..."
        }
      ]
    }
  ]
}
```

## Validation Prompt Pattern

### Structure

```
Validate the sub-agent output against the expected schema.

## Expected Schema

[Schema description with required fields]

## Validation Rules

1. [Required field 1]: [constraints]
2. [Required field 2]: [constraints]
...

## On Valid Output

Return: VALID

## On Invalid Output

Return: INVALID
Errors:
- [field_path]: [error description]

Provide specific field-level errors that can be used for retry.
```

### Example: Improvement Output Validation

```
Validate the sub-agent output against ContextImprovement schema.

## Expected Schema

The output should be a YAML structure with:
- improvements: list of improvement objects

Each improvement must have:
- id: Format CTX-NNN or ORCH-NNN or HO-NNN
- file: String path
- improvement_type: One of TIER_SPEC, NOT_PASSED, REFERENCE_PATTERN, etc.
- description: Non-empty string
- estimated_reduction: Float 0.0-1.0 (optional)
- priority: One of HIGH, MEDIUM, LOW

## Validation Rules

1. id: Must match pattern [A-Z]+-[0-9]{3}
2. improvement_type: Must be valid enum value
3. estimated_reduction: If present, must be 0.0-1.0
4. code_change: If present, must have 'before' and 'after'

## On Valid Output

Return: VALID

## On Invalid Output

Return: INVALID
Errors:
- ('improvements', 0, 'id'): ID 'bad-id' does not match pattern
- ('improvements', 1, 'estimated_reduction'): Value 1.5 exceeds maximum 1.0
```

## Pydantic Integration

### Define Models

```python
# models/improvement_outputs.py
from pydantic import BaseModel, Field, field_validator

class ContextImprovement(BaseModel):
    id: str
    file: str
    improvement_type: str
    description: str
    estimated_reduction: float | None = Field(default=None, ge=0.0, le=1.0)
    priority: str = "MEDIUM"

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        import re
        if not re.match(r"^[A-Z]+-\d{3}$", v):
            raise ValueError(f"ID '{v}' must match pattern XXX-NNN")
        return v

    @field_validator("improvement_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"TIER_SPEC", "NOT_PASSED", "REFERENCE_PATTERN", ...}
        if v not in valid_types:
            raise ValueError(f"Type '{v}' not in {valid_types}")
        return v
```

### Validation Script

```python
# scripts/validate_improvement_output.py
import yaml
from models import ContextImprovement

def validate(output_text: str) -> tuple[bool, list[str]]:
    """Validate sub-agent output."""
    try:
        data = yaml.safe_load(output_text)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    errors = []
    improvements = data.get("improvements", [])

    for i, imp in enumerate(improvements):
        try:
            ContextImprovement(**imp)
        except ValidationError as e:
            for error in e.errors():
                path = ("improvements", i) + tuple(error["loc"])
                errors.append(f"{path}: {error['msg']}")

    return len(errors) == 0, errors
```

## Coordinator Retry Pattern

### When Validation Blocks

```markdown
# In coordinator agent

## Automatic Output Validation

A PostToolUse hook automatically validates all sub-agent outputs.

### When Validation Blocks

If a sub-agent's output fails validation:
1. Retry the sub-agent with error context
2. Maximum 2 retries per sub-agent
3. After 2 failed retries, log to report and continue

### Retry Prompt Pattern

```
Previous output failed validation:
- ('improvements', 0, 'id'): ID must match pattern XXX-NNN

Please regenerate with corrected format.

[Original prompt here]
```
```

### Implementation

```yaml
# Coordinator logic
retry_on_validation_failure:
  max_retries: 2

  on_failure:
    attempt: 1
    action: |
      Retry with error context:
      "Previous output failed: [errors]
       Please fix and regenerate."

    attempt: 2
    action: |
      Same retry pattern

    attempt: 3
    action: |
      Log to limitations:
      "Sub-agent X failed validation after 2 retries"
      Continue with other agents
```

## Schema Reference

### Common Validation Rules

| Field Type | Validation |
|------------|------------|
| ID | Regex pattern XXX-NNN |
| Severity | Enum: CRITICAL, HIGH, MEDIUM, LOW |
| Confidence | Float 0.0-1.0 |
| Priority | Enum: HIGH, MEDIUM, LOW |
| Context Tier | Enum: FULL, SELECTIVE, FILTERED, MINIMAL, METADATA |

### Required vs Optional

```python
class Output(BaseModel):
    # Required (no default)
    id: str
    description: str

    # Optional (has default)
    confidence: float = 0.8
    notes: str | None = None
    items: list[str] = Field(default_factory=list)
```

## Debugging Hooks

### Issue: Hook Not Triggering

Check matcher pattern:
```json
{
  "matcher": {
    "tool_name": "Task",  # Must match exactly
    "agent_pattern": "coordinator-internal/*"  # Glob pattern
  }
}
```

### Issue: False Positives

Make validation more permissive:
```python
# Allow unknown fields
class Model(BaseModel):
    class Config:
        extra = "allow"

# Make fields optional
field: str | None = None
```

### Issue: Unhelpful Errors

Improve error messages:
```python
@field_validator("id")
@classmethod
def validate_id(cls, v):
    if not valid:
        raise ValueError(
            f"ID '{v}' invalid. Expected format: XXX-NNN "
            f"(e.g., CTX-001, ORCH-002)"
        )
```
