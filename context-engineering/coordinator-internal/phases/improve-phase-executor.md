---
tools:
  - Task
  - Bash
---

# Improve Phase Executor

## Context Tier: SELECTIVE

## Input

Receives via prompt:
- `analysis_id`: Session ID from analyze phase
- `focus_area`: context|orchestration|handoff|all

**NOT PROVIDED** (context isolation):
- Full plugin contents (reads from state)
- Unrelated violations (filtered by focus area)
- Analysis reasoning (only structured data)

## Execution

1. **Read Analysis from State**
   ```bash
   python scripts/state_manager.py read "$plugin_path" --field mutable
   ```
   Extract `analysis_summary` for selective context.

2. **Launch Improvers Based on Focus Area**

   **If focus_area = "context"**:
   ```
   Task: Optimize context patterns
   Agent: coordinator-internal/context-optimizer.md
   Prompt:
     analysis_summary: [from state - violations, opportunities for context]
     focus_area: context
   ```

   **If focus_area = "orchestration"**:
   ```
   Task: Improve orchestration patterns
   Agent: coordinator-internal/orchestration-improver.md
   Prompt:
     analysis_summary: [from state - violations, opportunities for orchestration]
     focus_area: orchestration
   ```

   **If focus_area = "handoff"**:
   ```
   Task: Improve handoff patterns
   Agent: coordinator-internal/handoff-improver.md
   Prompt:
     analysis_summary: [from state - violations, opportunities for handoff]
     focus_area: handoff
   ```

   **If focus_area = "all"**:
   Launch ALL THREE improvers IN PARALLEL with same analysis_summary.

3. **Collect Improvements**
   Aggregate improvements from all launched improvers.

4. **Store Improvements in State**
   ```bash
   python scripts/state_manager.py update "$plugin_path" improvements "$IMPROVEMENTS_JSON"
   ```

## Output

```yaml
improvements_generated:
  improvement_ids:
    - CTX-001
    - ORCH-002
    - HO-003
  count: [total count]
  by_priority:
    HIGH: [count]
    MEDIUM: [count]
    LOW: [count]
```

## State Integration

- **Reads**: `mutable.analysis_summary` (PluginAnalysis)
- **Writes**: `mutable.improvements` (list of improvements with IDs)

## Parallelism Trade-off

When focus_area is "all", three improvers run IN PARALLEL and each receives the full analysis_summary. This is an intentional trade-off:
- **Benefit**: ~3x faster execution
- **Cost**: ~2x context duplication
- **Justification**: Speed gain outweighs token cost for typical plugin sizes (<20K tokens)
