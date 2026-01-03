---
tools:
  - Task
  - Bash
---

# Analyze Phase Executor

## Context Tier: MINIMAL

## Input

Receives via prompt:
- `plugin_path`: Path to plugin directory (string only)
- `focus_area`: context|orchestration|handoff|all

**NOT PROVIDED** (context isolation):
- Plugin file contents (analyzer will fetch)
- Agent file contents (analyzer will fetch)
- Session history or previous analyses
- User's other plugins or projects

## Execution

1. **Initialize State**
   ```bash
   python scripts/state_manager.py init "$plugin_path" --focus "$focus_area" --mode standard
   ```

2. **Launch Plugin Analyzer**
   ```
   Task: Analyze plugin structure
   Agent: coordinator-internal/plugin-analyzer.md
   Prompt:
     plugin_path: [path]
     focus_area: [focus]
   ```

3. **Store Analysis Results**
   Extract from analyzer output:
   - `patterns_detected`: Current SOTA patterns in use
   - `violations`: Four Laws violations found
   - `opportunities`: Improvement opportunities by category
   - `metrics`: Agent count, tier compliance, etc.

   Store in state:
   ```bash
   python scripts/state_manager.py update "$plugin_path" analysis_summary "$ANALYSIS_JSON"
   ```

## Output

```yaml
analysis_complete:
  analysis_id: "[session_id from state]"
  summary:
    plugin_name: "[name]"
    violations_count: [count]
    opportunities_count: [count]
    metrics:
      agent_count: [count]
      tier_compliance: [0.0-1.0]
```

## State Integration

- **Reads**: Nothing (initializes state)
- **Writes**:
  - `immutable`: plugin_path, focus_area, session_id
  - `mutable.analysis_summary`: Full PluginAnalysis from analyzer
