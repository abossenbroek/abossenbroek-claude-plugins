# /improve-plugin Command

Improve an existing Claude Code plugin with SOTA context engineering patterns.

## Usage

```
/improve-plugin [focus] [path]
```

## Arguments

**focus** (optional):
- `all` - Full improvement pass (context + orchestration + handoff) (default)
- `context` - Optimize context management (Four Laws)
- `orchestration` - Improve agent hierarchy and coordination
- `handoff` - Optimize agent-to-agent data transfer

**path** (optional):
- Path to plugin directory (default: auto-detect in current workspace)

## Instructions

You are the MINIMAL entry point for plugin improvement. Your ONLY job is to:

1. Parse focus and path arguments
2. Locate the plugin to improve
3. Launch the improve-coordinator agent
4. Return the coordinator's output directly

### Step 1: Parse Arguments

Determine focus area and plugin path:
- Default focus: `all`
- Default path: Look for `.claude-plugin/plugin.json` in workspace

### Step 2: Locate Plugin

If no path provided:
1. Search for `.claude-plugin/plugin.json` files
2. If multiple found, ask user to specify
3. If none found, ask user to provide path

Verify the plugin exists by checking for `plugin.json`.

### Step 3: Launch Coordinator

Use the Task tool to launch the improve-coordinator agent:

```
Task: Improve plugin with SOTA patterns
Agent: agents/improve-coordinator.md
Prompt:
  plugin_path: [resolved plugin directory]
  focus_area: [parsed focus: all|context|orchestration|handoff]
```

The coordinator will:
1. Analyze the plugin structure
2. Generate improvements based on focus area
3. Ground improvements (pattern check, token estimate, risk)
4. Present options for user selection
5. Generate final improvement report

### Step 4: Return Output

Return the coordinator's improvement report DIRECTLY to the user.

DO NOT:
- Add commentary about the process
- Explain what the coordinator did
- Include intermediate analysis
- Modify the report in any way

ONLY return the final improvement report.

## Context Isolation Rules

This command is the FIREWALL between main session and improvement work:

- Main session context stays CLEAN
- Only plugin path and focus pass to coordinator
- Only the final improvement report returns to user
- No intermediate analysis enters main context

## Examples

```
/improve-plugin
# Runs full improvement pass on auto-detected plugin

/improve-plugin context
# Focus on context management improvements only

/improve-plugin orchestration ./my-plugin
# Improve agent hierarchy for specific plugin

/improve-plugin handoff
# Optimize handoffs in auto-detected plugin
```

## What Gets Improved

### Context Focus
- Add context tier specifications to agents
- Add "NOT PASSED" documentation sections
- Convert large embeddings to references
- Implement lazy loading patterns

### Orchestration Focus
- Add firewall coordinator architecture
- Split monolithic agents into phases
- Extract reusable sub-agents
- Align with SOTA patterns

### Handoff Focus
- Generate YAML handoff schemas
- Create Pydantic validation models
- Add PostToolUse validation hooks
- Minimize data transfer between agents
