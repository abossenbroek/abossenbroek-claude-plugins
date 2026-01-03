# /generate-handoffs Command

Generate handoff schemas and validation models for agent workflows.

## Usage

```
/generate-handoffs [agents]
```

## Arguments

**agents** (optional):
- Comma-separated list of agent file names (default: all agents in current plugin)
- Can also specify pairs: `agent1->agent2,agent2->agent3`

## Instructions

You are the MINIMAL entry point for handoff generation. Your ONLY job is to:

1. Identify agents to generate handoffs for
2. Launch the handoff-improver directly (no coordinator needed)
3. Return the generated artifacts directly

### Step 1: Identify Agents

If no agents provided:
1. Look for `.claude-plugin/plugin.json` in workspace
2. Extract all agents from manifest
3. Include `coordinator-internal/` agents

If agents provided:
1. Parse agent names or pairs from argument
2. Verify files exist

### Step 2: Analyze Flows

Use Glob to find agent files:
```
**/agents/*.md
**/coordinator-internal/**/*.md
```

Read agent files to identify:
- Task tool usage (which agents call which)
- Input/output sections
- Current handoff patterns

### Step 3: Launch Handoff Improver

Use the Task tool to launch the handoff-improver:

```
Task: Generate handoff schemas
Agent: coordinator-internal/handoff-improver.md
Prompt:
  agent_files:
    - file: [path]
      content: [agent content]
  transitions_to_generate:
    - from: [source agent]
      to: [target agent]
  generate_artifacts: true
```

The improver will:
1. Analyze transitions between agents
2. Determine optimal payloads
3. Generate YAML handoff schemas
4. Generate Pydantic models
5. Generate hook configurations

### Step 4: Return Output

Return the generated artifacts DIRECTLY to the user.

Include:
- YAML handoff schemas
- Pydantic model code
- Hook configuration JSON
- Implementation notes

DO NOT:
- Add commentary about the process
- Include intermediate analysis
- Modify the artifacts

## Examples

```
/generate-handoffs
# Generates handoffs for all agents in current plugin

/generate-handoffs coordinator,analyzer,validator
# Generates handoffs between specified agents

/generate-handoffs coordinator->analyzer,analyzer->validator
# Generates handoffs for specific transitions
```

## What Gets Generated

### YAML Handoff Schemas

For each transition:
```yaml
handoff:
  from_agent: improve-coordinator
  to_agent: plugin-analyzer
  context_level: FULL

  payload:
    plugin_manifest: "[plugin.json contents]"
    agent_files: "[list of agent files]"
    mode: "[focus area]"

  not_passed:
    - unrelated_files
    - build_artifacts
    - git_metadata

  expected_output:
    format: yaml
    schema: PluginAnalysis
```

### Pydantic Models

For each handoff:
```python
from pydantic import BaseModel, Field

class AnalyzerInput(BaseModel):
    """Input schema for plugin-analyzer."""
    plugin_manifest: dict
    agent_files: list[AgentFile]
    mode: str = "all"

class AgentFile(BaseModel):
    file: str
    content: str
```

### Hook Configurations

For validation:
```json
{
  "event": "PostToolUse",
  "matcher": {
    "tool_name": "Task",
    "agent_pattern": "coordinator-internal/*"
  },
  "hooks": [{
    "type": "prompt",
    "prompt": "Validate output..."
  }]
}
```

## Output Location

Generated files can be saved to:
- `templates/handoffs/` - YAML schemas
- `src/*/models/` - Pydantic models
- `hooks/` - Hook configurations

Or displayed inline for manual placement.
