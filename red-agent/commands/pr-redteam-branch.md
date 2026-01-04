# /redteam-pr:branch Command

Adversarial red team analysis of branch comparison for PR review.

## Usage

```
/redteam-pr:branch <branch_spec> [mode]
```

## Arguments

**branch_spec** (required):
- Branch comparison specification
- Format: `base...feature` or `base..feature`
- Example: `/redteam-pr:branch main...feature-branch`

**mode** (optional):
- `quick` - Fast 2-3 vector analysis, skip grounding
- `standard` - Balanced 5-6 vectors with basic grounding (default)
- `deep` - All categories + meta-analysis with full grounding
- `focus:[category]` - Deep dive on specific category (e.g., `focus:reasoning-flaws`)

## Instructions

You are the MINIMAL entry point for PR red team analysis of branch comparisons. Your ONLY job is to:

1. Execute git operations to compare branches
2. Check PAL MCP availability (optional enhancement)
3. Extract diff metadata, commit context, and build structured snapshot
4. Launch the pr-analysis-coordinator agent with the snapshot
5. Return the coordinator's output directly to the user

### Step 1: Execute Git Operations

Use the Bash tool to get branch comparison data:

```bash
# Get file statistics for branch comparison
git diff <branch_spec> --numstat

# Get unified diff with 3 lines of context
git diff <branch_spec> -U3

# Get commit log for context
git log --oneline <branch_spec>
```

Replace `<branch_spec>` with the provided argument (e.g., `main...feature`).

If the branches do not exist or comparison fails, inform the user and exit.

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

### Step 4: Extract Diff Metadata

Parse the git output to build structured metadata:

**From `git diff <branch_spec> --numstat`:**
- Extract file paths, additions, deletions
- Classify change_type: added, modified, deleted, renamed

**From `git log --oneline <branch_spec>`:**
- Extract commit hashes and messages
- Count total commits in comparison

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
  git_operation: "branch_comparison"
  branch_spec: [the provided branch spec]
  pal_available: [true/false from Step 2]
  pal_models: [list of models if available, empty if not]

  commit_context:
    total_commits: [count]
    commits:
      - hash: [short hash]
        message: [commit message]

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
    [Full output from git diff <branch_spec> -U3]
```

### Step 6: User Scoping for Large PRs

If `pr_size` is "large" or "massive", use the AskUserQuestion tool to let the user scope the analysis:

```
Question: "This PR has {total_files} files with {total_additions + total_deletions} lines changed across {total_commits} commits. How would you like to proceed?"

Options:
1. label: "Analyze all files"
   description: "Complete analysis of all changes. May take 2-5 minutes for massive PRs."

2. label: "High-risk files only [RECOMMENDED]"
   description: "Focus on files with risk_score > 0.7. Faster and catches critical issues."

3. label: "Specific files/directories"
   description: "You choose which files or directories to analyze."

4. label: "By commit"
   description: "Analyze each commit individually instead of the full diff."
```

Based on the user's choice:
- **Option 1**: Use all files from `diff_metadata.files_changed`
- **Option 2**: Filter to only files where `risk_score > 0.7`
- **Option 3**: Ask follow-up question: "Which files or directories? (provide paths or globs like `src/auth/*`)", then filter `files_changed` to match
- **Option 4**: Change strategy to per-commit analysis:
  - For each commit in `commit_context.commits`, get individual diff: `git diff <commit>^ <commit>`
  - Launch coordinator separately for each commit with that commit's diff
  - Aggregate reports from all commits

For options 1-3, update `diff_metadata.files_changed` with the filtered list before proceeding.

### Step 7: Launch Coordinator

Use the Task tool to launch a SINGLE agent (or multiple for option 4):

```
Task: Launch pr-analysis-coordinator agent
Agent: agents/pr-analysis-coordinator.md
Prompt: [Include the full YAML snapshot]
```

### Step 8: Return Output

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
