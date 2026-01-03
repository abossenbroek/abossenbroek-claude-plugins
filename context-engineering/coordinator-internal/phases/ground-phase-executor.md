---
tools:
  - Task
  - Bash
---

# Ground Phase Executor

## Context Tier: FILTERED

## Input

Receives via prompt:
- `plugin_path`: Path to plugin directory
- `categorized_improvements`: Priority batches (HIGH/MEDIUM/LOW)

**NOT PROVIDED** (context isolation):
- Full analysis (not needed for grounding)
- Rejected improvements (filtered out)
- Plugin contents (grounding agents get only improvement text)

## Execution

1. **Read Categorized Improvements from State**
   ```bash
   python scripts/state_manager.py read "$plugin_path" --field mutable
   ```
   Extract `categorized_improvements`.

2. **Apply Severity-Based Batching**

   **For HIGH priority improvements**:
   Launch ALL 4 grounding agents IN PARALLEL:
   ```
   Task: Check pattern compliance
   Agent: coordinator-internal/grounding/pattern-checker.md
   Prompt:
     improvements_to_check: [HIGH improvements]
     focus_area: [from state]
   ```
   ```
   Task: Estimate token impact
   Agent: coordinator-internal/grounding/token-estimator.md
   Prompt:
     improvements_to_check: [HIGH improvements]
     focus_area: [from state]
   ```
   ```
   Task: Check consistency
   Agent: coordinator-internal/grounding/consistency-checker.md
   Prompt:
     improvements_to_check: [HIGH improvements]
     focus_area: [from state]
   ```
   ```
   Task: Assess risks
   Agent: coordinator-internal/grounding/risk-assessor.md
   Prompt:
     improvements_to_check: [HIGH improvements]
     focus_area: [from state]
   ```

   **For MEDIUM priority improvements**:
   Launch 2 grounding agents IN PARALLEL:
   - `pattern-checker.md`
   - `token-estimator.md`

   **For LOW priority improvements**:
   Launch 1 grounding agent:
   - `pattern-checker.md` only

3. **Collect Grounding Results**
   Aggregate assessments from all grounding agents.

4. **Store Grounding Results in State**
   ```bash
   python scripts/state_manager.py update "$plugin_path" grounding_results "$GROUNDING_JSON"
   ```

## Output

```yaml
grounding_complete:
  grounded_improvements:
    - improvement_id: CTX-001
      priority: HIGH
      grounding:
        pattern_compliant: true
        token_estimate:
          before: 5000
          after: 3500
          reduction_percent: 30
        consistency_check: PASS
        risk_level: LOW
    - improvement_id: ORCH-002
      priority: MEDIUM
      grounding:
        pattern_compliant: true
        token_estimate:
          before: 2000
          after: 1600
          reduction_percent: 20
  total_grounded: [count]
```

## State Integration

- **Reads**: `mutable.categorized_improvements` (priority batches)
- **Writes**: `mutable.grounding_results` (assessments for each improvement)

## Efficiency Gains

Severity-based batching reduces grounding operations:
- Typical improvement set: 10 improvements (3 HIGH, 4 MEDIUM, 3 LOW)
- Without batching: 40 grounding operations (10 × 4 agents)
- With batching: 19 grounding operations (3×4 + 4×2 + 3×1)
- **Reduction**: 52% fewer grounding operations
