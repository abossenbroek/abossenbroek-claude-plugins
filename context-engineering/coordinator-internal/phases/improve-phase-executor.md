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

2. **Filter File References by Focus Area**

   Before launching each improver, filter file_refs to pass only relevant files:

   ```bash
   python scripts/file_cache.py get_refs_by_focus "$plugin_path" "$focus_area"
   ```

   This reduces context duplication by ~2x by passing only files matching the focus area patterns.

3. **Launch Improvers Based on Focus Area**

   **If focus_area = "context"**:
   ```
   Task: Optimize context patterns
   Agent: coordinator-internal/context-optimizer.md
   Prompt:
     analysis_summary: [from state - violations, opportunities for context]
     focus_area: context
     file_refs: [filtered by "context" patterns]
   ```

   **If focus_area = "orchestration"**:
   ```
   Task: Improve orchestration patterns
   Agent: coordinator-internal/orchestration-improver.md
   Prompt:
     analysis_summary: [from state - violations, opportunities for orchestration]
     focus_area: orchestration
     file_refs: [filtered by "orchestration" patterns]
   ```

   **If focus_area = "handoff"**:
   ```
   Task: Improve handoff patterns
   Agent: coordinator-internal/handoff-improver.md
   Prompt:
     analysis_summary: [from state - violations, opportunities for handoff]
     focus_area: handoff
     file_refs: [filtered by "handoff" patterns]
   ```

   **If focus_area = "all"**:
   Launch ALL THREE improvers IN PARALLEL, each with focus-filtered file_refs.

4. **Collect Improvements**
   Aggregate improvements from all launched improvers.

5. **Store Improvements in State**
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

## Focus-Based Filtering (CM-001)

Each improver receives ONLY files relevant to its focus area:
- **context**: agents/*.md, coordinator-internal/*.md, skills/**/*.md
- **orchestration**: agents/*.md, coordinator-internal/*.md, hooks/*.json
- **handoff**: agents/*.md, hooks/*.json, coordinator-internal/*.md, scripts/*.py
- **all**: All three improvers run in parallel, each with their own filtered refs

This reduces context duplication by ~2x compared to passing all files to all improvers.
