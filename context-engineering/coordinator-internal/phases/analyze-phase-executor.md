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

### Phase 1a: Initialize State

```bash
python scripts/state_manager.py init "$plugin_path" --focus "$focus_area" --mode standard
```

### Phase 1b: File Discovery (I/O Phase)

Launch file-discovery-executor to discover files and load priorities:

```
Task: Discover plugin files and load priorities
Agent: coordinator-internal/phases/file-discovery-executor.md
Prompt:
  plugin_path: [path]
  patterns: ["**/*.md", "**/*.json"]
```

This executor:
- Discovers all plugin files (via Glob)
- Registers file references in cache
- Loads priority files (plugin.json, CLAUDE.md, entry agents)
- Returns file_refs summary

### Phase 1c: Analysis (Pure Analysis Phase)

Launch analysis-executor to analyze cached data:

```
Task: Analyze plugin structure from cache
Agent: coordinator-internal/phases/analysis-executor.md
Prompt:
  plugin_path: [path]
  focus_area: [focus]
```

This executor:
- Accesses files from cache only (NO direct I/O)
- Lazy loads additional files as needed
- Launches plugin-analyzer for deep analysis
- Stores results in state

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
