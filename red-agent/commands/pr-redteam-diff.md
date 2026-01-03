# /redteam-pr:diff Command

Adversarial red team analysis of a diff file for PR review.

## Usage

```
/redteam-pr:diff <diff_file> [mode]
```

## Arguments

**diff_file** (required):
- Path to a diff or patch file to analyze
- Example: `/redteam-pr:diff changes.patch`

**mode** (optional):
- `quick` - Fast 2-3 vector analysis, skip grounding
- `standard` - Balanced 5-6 vectors with basic grounding (default)
- `deep` - All categories + meta-analysis with full grounding
- `focus:[category]` - Deep dive on specific category (e.g., `focus:reasoning-flaws`)

## Instructions

You are the MINIMAL entry point for PR red team analysis of diff files. Your ONLY job is to:

1. Read the diff file from the provided path
2. Check PAL MCP availability (optional enhancement)
3. Parse diff content and build structured snapshot
4. Launch the pr-analysis-coordinator agent with the snapshot
5. Return the coordinator's output directly to the user

### Step 1: Read Diff File

Use the Read tool to get the diff content from the provided file path.

If the file does not exist or cannot be read, inform the user and exit.

### Step 2: Check PAL Availability (Non-Blocking)

Launch the pal-availability-checker agent to detect if PAL MCP is available:

```
Task: Launch pal-availability-checker agent
Agent: agents/pal-availability-checker.md
Prompt: Check if PAL MCP is available and list models
```

Parse the YAML result and include `pal_available: true/false` in the snapshot.
This step is NON-BLOCKING - continue regardless of result. PAL is optional.

### Step 3: Parse Mode

Determine mode from command arguments:
- Default mode: `standard`

### Step 4: Parse Diff Content

Parse the diff file to build structured metadata:

**From unified diff format:**
- Extract file paths from `--- a/...` and `+++ b/...` lines
- Count additions (lines starting with `+`, excluding `+++`)
- Count deletions (lines starting with `-`, excluding `---`)
- Classify change_type: added, modified, deleted, renamed

**Calculate risk_score per file:**
- Base score: 0.0
- Authentication/security files (auth, security, permission in path): +0.4
- Large changes (>100 lines added/deleted): +0.3
- Test files (test, spec in path): -0.3
- Clamp to [0.0, 1.0]

**Classify pr_size:**
- tiny: 1-2 files, <50 lines
- small: 3-5 files, <200 lines
- medium: 6-15 files, <500 lines
- large: 16-30 files, <1000 lines
- massive: >30 files or >1000 lines

### Step 5: Build YAML Snapshot

Create a YAML-formatted snapshot with structured data:

```yaml
snapshot:
  mode: [parsed mode]
  git_operation: "diff_file"
  source_file: [path to diff file]
  pal_available: [true/false from Step 2]
  pal_models: [list of models if available, empty if not]

  diff_metadata:
    pr_size: [tiny/small/medium/large/massive]
    files_changed:
      - path: [file path]
        additions: [number]
        deletions: [number]
        change_type: [added/modified/deleted/renamed]
        risk_score: [0.0-1.0]
    total_additions: [sum]
    total_deletions: [sum]
    total_files: [count]

  diff_output: |
    [Full content of the diff file]
```

### Step 6: Launch Coordinator

Use the Task tool to launch a SINGLE agent:

```
Task: Launch pr-analysis-coordinator agent
Agent: agents/pr-analysis-coordinator.md
Prompt: [Include the full YAML snapshot]
```

### Step 7: Return Output

Return the coordinator's markdown report DIRECTLY to the user.

DO NOT:
- Add commentary about the process
- Explain what the coordinator did
- Include any "I attacked X" reasoning
- Show intermediate findings

ONLY return the final sanitized markdown report.

## Context Isolation Rules

This command is the FIREWALL between main session and PR analysis work:

- Main session context stays CLEAN
- Only structured snapshot data passes to coordinator
- Only sanitized markdown report returns to user
- No adversarial prompts or attack reasoning enters main context
