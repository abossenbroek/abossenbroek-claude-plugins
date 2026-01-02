# /redteam-w-fix Command

Red team analysis with interactive fix selection. Identifies issues, generates fix options, and lets you choose which fixes to apply.

## Usage

```
/redteam-w-fix [mode] [target]
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

You are the entry point for red team analysis with fix planning. Your job is to:

1. Parse the mode and target from arguments
2. Extract a structured context snapshot
3. Launch the fix-coordinator to get findings with fix options
4. Present an interactive menu for fix selection
5. Generate an implementation summary based on selections

### Step 1: Parse Arguments

Determine mode and target from the command arguments:
- Default mode: `standard`
- Default target: `conversation`

### Step 2: Extract Context Snapshot

Create a YAML-formatted snapshot of the current session. DO NOT include raw conversation - structure it as data:

```yaml
snapshot:
  mode: [parsed mode]
  target: [parsed target]

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

### Step 3: Launch Fix Coordinator

Use the Task tool to launch the fix-coordinator agent:

```
Task: Launch fix-coordinator agent
Agent: agents/fix-coordinator.md
Prompt: [Include the full YAML snapshot]
```

The coordinator will:
- Run red team analysis
- Filter findings (CRITICAL, HIGH, MEDIUM only)
- Generate fix options for each finding
- Return structured YAML with `findings_with_fixes`

### Step 4: Present Fix Selection Menu

Parse the coordinator's YAML output. For each finding, present a question using AskUserQuestion.

**Batching Rule**: AskUserQuestion supports max 4 questions per call.
- **Batch 1**: CRITICAL and HIGH severity findings (up to 4)
- **Batch 2**: Remaining HIGH and MEDIUM findings (up to 4)
- Continue until all findings are addressed

For each finding, create a question:

```
AskUserQuestion(questions=[
    {
        "question": "[finding_id]: [finding_title]\nSeverity: [severity] | How should we fix this?",
        "header": "[finding_id]",  # Max 12 chars
        "multiSelect": false,
        "options": [
            {
                "label": "[option_a_label]",
                "description": "[option_a_description - first 100 chars]"
            },
            {
                "label": "[option_b_label]",
                "description": "[option_b_description - first 100 chars]"
            },
            # ... up to 3 options
        ]
    },
    # ... up to 4 questions per batch
])
```

The "Other" option is automatically included by AskUserQuestion.

After each batch, if more findings remain, call AskUserQuestion again.

### Step 5: Generate Implementation Summary

Based on user selections, generate an expert end-user summary.

Format:

```markdown
# Red Team Fixes - Selected Actions

## Summary
[N] issues addressed | Touches: [list of affected components]

---

## [finding_id]: [finding_title]

**Issue**: [Brief description of the problem and its risk]

**Selected fix**: [Selected option label]

**What changes**:
- [Change 1]
- [Change 2]
- [Change 3]

**Why this over alternatives**:
[Brief explanation of why this option was selected over others]

**Watch out for**: [Any risks or things to test]

---

[Repeat for each selected fix]

---

## Suggested Order
1. [First thing to do]
2. [Second thing to do]
3. [Continue...]
```

If the user selected "Other" for any finding, include their custom input in the summary.

### Step 6: Return Output

Return the implementation summary DIRECTLY to the user.

DO NOT:
- Add commentary about the process
- Explain what the agents did
- Include raw YAML output
- Show intermediate findings

ONLY return the final implementation summary.

## Context Isolation Rules

This command is the BRIDGE between main session and red team work:

- Main session context stays CLEAN
- Only structured snapshot data passes to coordinator
- Fix options return as structured YAML
- Menu interaction happens in main context (safe)
- Only sanitized summary returns to user

## Error Handling

If the coordinator returns no findings:
```markdown
# Red Team Analysis Complete

No issues at CRITICAL, HIGH, or MEDIUM severity were identified.

The analysis found [N] LOW/INFO level observations which don't require fixes.
Run `/redteam` for the full report if interested.
```

If a batch of questions returns with all "skip" or empty responses:
- Continue to next batch
- Note skipped findings in summary

## Example Flow

1. User runs: `/redteam-w-fix standard`
2. Command builds snapshot, launches coordinator
3. Coordinator returns 3 findings with fix options
4. Command presents menu:
   ```
   [RF-001] [AG-002] [CM-003]

   RF-001: Invalid inference in auth
   Severity: HIGH | How should we fix this?

   ○ A: Add validation [LOW]
   ○ B: Refactor flow [MEDIUM]
   ○ C: Type-safe handlers [HIGH]
   ○ Other
   ```
5. User selects B for RF-001, A for AG-002, Other ("Just add logging") for CM-003
6. Command generates summary with all selections
7. User receives actionable implementation summary
