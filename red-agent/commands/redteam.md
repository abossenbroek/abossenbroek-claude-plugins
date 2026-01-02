# /redteam Command

Adversarial red team analysis of the current conversation or specified target.

## Usage

```
/redteam [mode] [target]
```

## Arguments

**mode** (optional):
- `quick` - Fast 2-3 vector analysis, skip grounding
- `standard` - Balanced 5-6 vectors with basic grounding (default)
- `deep` - All categories + meta-analysis with full grounding
- `focus:[category]` - Deep dive on specific category (e.g., `focus:reasoning-flaws`)

**target** (optional):
- `conversation` - Current conversation context (default)
- `file:path` - Analyze specific file
- `code` - Analyze recent git changes

## Instructions

You are the MINIMAL entry point for red team analysis. Your ONLY job is to:

1. Check PAL MCP availability (optional enhancement)
2. Parse the mode and target from arguments
3. Extract a structured context snapshot
4. Launch the red-team-coordinator agent with the snapshot
5. Return the coordinator's output directly to the user

### Step 1: Check PAL Availability (Non-Blocking)

Launch the pal-availability-checker agent to detect if PAL MCP is available:

```
Task: Launch pal-availability-checker agent
Agent: agents/pal-availability-checker.md
Prompt: Check if PAL MCP is available and list models
```

Parse the YAML result and include `pal_available: true/false` in the snapshot.
This step is NON-BLOCKING - continue regardless of result. PAL is optional.

### Step 2: Parse Arguments

Determine mode and target from the command arguments:
- Default mode: `standard`
- Default target: `conversation`

### Step 3: Extract Context Snapshot

Create a YAML-formatted snapshot of the current session. DO NOT include raw conversation - structure it as data:

```yaml
snapshot:
  mode: [parsed mode]
  target: [parsed target]
  pal_available: [true/false from Step 1]
  pal_models: [list of models if available, empty if not]

  conversational_arc:
    message_count: [count of messages in conversation]
    phases:
      - phase: "[phase name]"
        messages: [range]
        summary: "[what happened in this phase]"
    key_transitions:
      - from_msg: [number]
        to_msg: [number]
        note: "[what changed and why]"
    early_assumptions_carried_forward:
      - assumption: "[assumption text]"
        introduced_at: [message number]
        still_active: [true/false]

  claims:
    - id: C[N]
      text: "[factual claim made by assistant]"
      speaker: assistant
      confidence: [stated_as_fact|hedged|uncertain]
      message_num: [source message number]

  files_read:
    - path: [file path]
      summary: "[brief description of content/purpose]"

  tools_invoked:
    - tool: [tool name]
      command: "[command or action]"
      outcome: "[result summary]"

  decisions:
    - decision: "[decision made]"
      rationale: "[stated reason]"

  assumptions_explicit:
    - "[explicitly stated assumption]"
```

### Step 4: Launch Coordinator

Use the Task tool to launch a SINGLE agent:

```
Task: Launch red-team-coordinator agent
Agent: agents/red-team-coordinator.md
Prompt: [Include the full YAML snapshot]
```

### Step 5: Return Output

Return the coordinator's markdown report DIRECTLY to the user.

DO NOT:
- Add commentary about the process
- Explain what the coordinator did
- Include any "I attacked X" reasoning
- Show intermediate findings

ONLY return the final sanitized markdown report.

## Context Isolation Rules

This command is the FIREWALL between main session and red team work:

- Main session context stays CLEAN
- Only structured snapshot data passes to coordinator
- Only sanitized markdown report returns to user
- No adversarial prompts or attack reasoning enters main context
