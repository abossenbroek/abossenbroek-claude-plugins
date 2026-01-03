---
tools:
  - Bash
---

# Categorize Phase Executor

## Context Tier: MINIMAL

## Input

Receives via prompt:
- `plugin_path`: Path to plugin directory
- `improvement_ids`: List of improvement IDs to categorize

**NOT PROVIDED** (context isolation):
- Full analysis data (not needed for categorization)
- Plugin contents (not needed)
- Grounding results (done in next phase)

## Execution

1. **Read Improvements from State**
   ```bash
   python scripts/state_manager.py read "$plugin_path" --field mutable
   ```
   Extract `improvements` list.

2. **Categorize by Priority**

   Apply severity rules:
   - **HIGH**: estimated_reduction > 0.30 OR fixes pattern violation
   - **MEDIUM**: 0.10 <= estimated_reduction <= 0.30
   - **LOW**: estimated_reduction < 0.10

   Group improvements into priority batches:
   ```yaml
   improvements_by_priority:
     HIGH: [improvement_ids with HIGH priority]
     MEDIUM: [improvement_ids with MEDIUM priority]
     LOW: [improvement_ids with LOW priority]
   ```

3. **Store Categorization in State**
   ```bash
   python scripts/state_manager.py update "$plugin_path" categorized_improvements "$CATEGORIZED_JSON"
   ```

## Output

```yaml
categorization_complete:
  by_priority:
    HIGH:
      count: [count]
      ids: [list of IDs]
    MEDIUM:
      count: [count]
      ids: [list of IDs]
    LOW:
      count: [count]
      ids: [list of IDs]
  total_improvements: [count]
```

## State Integration

- **Reads**: `mutable.improvements` (list with estimated_reduction, priority fields)
- **Writes**: `mutable.categorized_improvements` (grouped by HIGH/MEDIUM/LOW)

## Priority Logic

This phase implements the severity-based batching strategy:
1. HIGH priority improvements get full grounding (all 4 agents)
2. MEDIUM priority get partial grounding (2 agents)
3. LOW priority get minimal grounding (1 agent)

This reduces grounding overhead by ~60% for typical improvement sets.
