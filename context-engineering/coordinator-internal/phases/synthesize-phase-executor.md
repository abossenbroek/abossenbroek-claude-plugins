---
tools:
  - Task
  - Bash
---

# Synthesize Phase Executor

## Context Tier: METADATA

## Input

Receives via prompt:
- `plugin_path`: Path to plugin directory
- `selected_improvement_ids`: IDs of improvements user selected to apply

**NOT PROVIDED** (context isolation):
- Rejected improvements (filtered out by coordinator)
- Full analysis (not needed for synthesis)
- Intermediate reasoning (only final structured data)

## Execution

1. **Read Selected Improvements from State**
   ```bash
   python scripts/state_manager.py read "$plugin_path" --field mutable
   ```
   Extract:
   - `improvements` (filter to selected IDs)
   - `grounding_results` (filter to selected IDs)
   - `immutable` (for scope metadata)

2. **Prepare Synthesis Input**
   Build METADATA-tier input:
   ```yaml
   selected_improvements:
     - improvement_id: CTX-001
       description: [what was selected]
       code_change:
         before: [current code]
         after: [improved code]
       grounding_results:
         pattern_compliant: true
         token_estimate: [reduction data]
         risk_level: LOW
   scope_metadata:
     plugin_name: [from analysis]
     files_analyzed: [count]
     improvements_available: [total count from state]
     improvements_selected: [selected count]
     focus_area: [from immutable state]
   ```

3. **Launch Improvement Synthesizer**
   ```
   Task: Generate final improvement report
   Agent: coordinator-internal/improvement-synthesizer.md
   Prompt:
     selected_improvements: [metadata above]
     scope_metadata: [plugin context]
   ```

4. **Return Report Directly**
   Return the synthesizer's ImprovementReport UNCHANGED to coordinator.

## Output

```yaml
improvement_report:
  executive_summary:
    improvements_applied: [count]
    estimated_token_reduction: [total %]
    patterns_improved: [list]
  changes:
    - file: [path]
      change_type: [type]
      before: [code]
      after: [code]
  next_steps:
    - [actionable step]
```

## State Integration

- **Reads**:
  - `mutable.improvements` (selected subset)
  - `mutable.grounding_results` (selected subset)
  - `immutable` (plugin_path, focus_area, session_id)
- **Writes**: Nothing (final phase)

## Context Tier Justification

This phase operates at METADATA tier:
- Only selected improvements (rejected ones filtered)
- Only structured grounding results (no intermediate reasoning)
- Only scope metadata (plugin name, counts, focus area)
- Total context: ~200-500 tokens (vs 5-20K tokens in analyze phase)

This represents a **97% context reduction** from Phase 1 to Phase 6.
