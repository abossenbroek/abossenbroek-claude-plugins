# Severity-Based Batching

Detailed guide to routing items by priority for efficient validation.

## Core Concept

Not all items need the same level of validation. Route by priority:

```
High Impact Items    ──▶  Full validation (all validators)
Medium Impact Items  ──▶  Partial validation (key validators)
Low Impact Items     ──▶  Minimal validation (basic check)
Info/Skip Items      ──▶  No validation
```

## Why Batching?

### Without Batching

```yaml
items: 30
validators: 4

operations: 30 × 4 = 120
```

### With Batching

```yaml
items:
  CRITICAL: 2   →  4 validators  =  8 ops
  HIGH: 5       →  2 validators  = 10 ops
  MEDIUM: 10    →  1 validator   = 10 ops
  LOW: 8        →  0 validators  =  0 ops
  INFO: 5       →  0 validators  =  0 ops

total: 28 operations (vs 120)
reduction: 77%
```

## Batching Strategies

### Strategy 1: Severity-Based

Route by item severity/priority:

```yaml
routing:
  CRITICAL:
    validators: [all]
    rationale: "Must be thoroughly validated"

  HIGH:
    validators: [pattern-checker, token-estimator]
    rationale: "Need pattern and impact validation"

  MEDIUM:
    validators: [pattern-checker]
    rationale: "Basic pattern check sufficient"

  LOW:
    validators: []
    rationale: "Low impact, skip validation"

  INFO:
    validators: []
    rationale: "Informational only"
```

### Strategy 2: Mode-Based

Route by analysis mode:

```yaml
quick_mode:
  all_items: skip_grounding
  rationale: "Speed over thoroughness"

standard_mode:
  CRITICAL_HIGH: [checker, estimator]
  MEDIUM: [checker]
  LOW_INFO: skip
  rationale: "Balanced approach"

deep_mode:
  CRITICAL: [all_validators]
  HIGH: [checker, estimator]
  MEDIUM: [checker]
  LOW_INFO: skip
  rationale: "Thorough for high-impact"
```

### Strategy 3: Hybrid

Combine severity and mode:

```yaml
routing_matrix:
  deep_mode:
    CRITICAL: all_4_validators
    HIGH: 2_validators
    MEDIUM: 1_validator
    LOW: skip

  standard_mode:
    CRITICAL: 2_validators
    HIGH: 2_validators
    MEDIUM: 1_validator
    LOW: skip

  quick_mode:
    all: skip
```

## Implementation Pattern

### Step 1: Categorize Items

```yaml
# In coordinator
categorize_by_priority:
  improvements_by_priority:
    HIGH:
      - id: CTX-001
        description: "Add context tiers"
        estimated_reduction: 0.45
      - id: ORCH-001
        description: "Add firewall"
        estimated_reduction: 0.55

    MEDIUM:
      - id: CTX-002
        description: "Add NOT PASSED"
        estimated_reduction: 0.15

    LOW:
      - id: HO-001
        description: "Document handoff"
        estimated_reduction: 0.05
```

### Step 2: Route to Validators

```yaml
# HIGH batch → all validators (parallel)
high_batch:
  parallel: true
  validators:
    - agent: pattern-checker
      input: high_priority_improvements
    - agent: token-estimator
      input: high_priority_improvements
    - agent: consistency-checker
      input: high_priority_improvements
    - agent: risk-assessor
      input: high_priority_improvements

# MEDIUM batch → subset validators
medium_batch:
  parallel: true
  validators:
    - agent: pattern-checker
      input: medium_priority_improvements
    - agent: token-estimator
      input: medium_priority_improvements

# LOW batch → skip
low_batch:
  validators: []
  action: pass_through
```

### Step 3: Merge Results

```yaml
# Combine validation results
grounding_results:
  high_priority:
    - improvement_id: CTX-001
      pattern_check: pass
      token_estimate: -45%
      consistency: pass
      risk: LOW
    - improvement_id: ORCH-001
      pattern_check: pass
      token_estimate: -55%
      consistency: pass
      risk: MEDIUM

  medium_priority:
    - improvement_id: CTX-002
      pattern_check: pass
      token_estimate: -15%
      # No consistency/risk (not checked)

  low_priority:
    - improvement_id: HO-001
      # No validation (skipped)
```

## Validator Selection

### Which Validators for Which Batches

| Validator | CRITICAL | HIGH | MEDIUM | LOW |
|-----------|----------|------|--------|-----|
| Pattern Checker | Yes | Yes | Yes | No |
| Token Estimator | Yes | Yes | Optional | No |
| Consistency Checker | Yes | Optional | No | No |
| Risk Assessor | Yes | Optional | No | No |

### Rationale

- **Pattern Checker**: Always needed for quality
- **Token Estimator**: Needed for impact-based prioritization
- **Consistency Checker**: Only for complex/high-impact changes
- **Risk Assessor**: Only for potentially breaking changes

## Priority Assignment

### For Improvements

```yaml
priority_rules:
  HIGH:
    - estimated_reduction > 0.30  # >30% token reduction
    - fixes_pattern_violation: true
    - type: FIREWALL  # Architectural change

  MEDIUM:
    - estimated_reduction: 0.10-0.30
    - type: TIER_SPEC
    - type: NOT_PASSED

  LOW:
    - estimated_reduction < 0.10
    - type: documentation
    - purely_additive: true
```

### For Findings (red-agent style)

```yaml
priority_rules:
  CRITICAL:
    - security_impact: high
    - data_leak_risk: true

  HIGH:
    - confidence > 0.8
    - impact: significant

  MEDIUM:
    - confidence: 0.5-0.8
    - impact: moderate

  LOW:
    - confidence < 0.5
    - impact: minor

  INFO:
    - informational_only: true
```

## Efficiency Metrics

### Measuring Batching Effectiveness

```yaml
metrics:
  # Operation reduction
  without_batching:
    items: 30
    validators: 4
    operations: 120

  with_batching:
    high: {items: 5, validators: 4, ops: 20}
    medium: {items: 10, validators: 2, ops: 20}
    low: {items: 15, validators: 0, ops: 0}
    total_ops: 40

  reduction: 67%  # (120-40)/120

  # Quality maintained
  high_impact_fully_validated: true
  medium_impact_key_validated: true
  low_impact_passed_through: true
```

## Common Mistakes

### Mistake 1: Grounding Everything

```yaml
# BAD: All items to all validators
for item in all_items:
    for validator in all_validators:
        validate(item)
```

**Fix**: Batch by priority, skip low-impact items.

### Mistake 2: Skipping High-Impact

```yaml
# BAD: Quick mode skips critical items
quick_mode:
  all: skip_grounding  # Including CRITICAL!
```

**Fix**: Always validate CRITICAL items regardless of mode.

### Mistake 3: Wrong Priority Assignment

```yaml
# BAD: Everything is HIGH
priorities:
  - item_1: HIGH  # Actually low impact
  - item_2: HIGH  # Actually medium
  - item_3: HIGH  # Actually critical
```

**Fix**: Use clear criteria for priority assignment.
