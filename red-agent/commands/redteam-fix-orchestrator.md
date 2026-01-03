# /redteam-fix-orchestrator Command

Red team analysis fix orchestration with automated execution. Takes findings from red team analysis, interactively selects fixes to apply (CLI mode) or auto-applies based on policy (GitHub hook mode), then orchestrates parallel fix execution through a 6-stage pipeline.

## Usage

```
/redteam-fix-orchestrator [findings-source] [options]
```

## Arguments

**findings-source** (optional):
- `last` - Use findings from most recent `/redteam` run (default)
- `file:path` - Load findings from YAML file at specified path

**options** (optional):
- `--auto` - Force automated mode even in CLI (use default policy)
- `--max-parallel=N` - Limit concurrent fix phases (default: 4)
- `--commit-strategy=per-fix|per-phase` - Git commit granularity (default: per-fix)

## Instructions

You are the entry point for red team fix orchestration. Your job is to:

1. Check PAL MCP availability (optional enhancement)
2. Detect execution mode (interactive CLI vs GitHub hook)
3. Load findings from source
4. Launch the fix-orchestrator agent
5. Handle interactive fix selection (if CLI mode)
6. Return execution summary

### Step 1: Check PAL Availability (Non-Blocking)

Launch the pal-availability-checker agent to detect if PAL MCP is available:

```
Task: Launch pal-availability-checker agent
Agent: agents/pal-availability-checker.md
Prompt: Check if PAL MCP is available and list models
```

Parse the YAML result and extract `pal_available: true/false`.

**This step is NON-BLOCKING** - if PAL check fails or times out, continue with `pal_available: false`. PAL is optional enhancement, not required.

### Step 2: Detect Execution Mode

Check the `CLAUDE_CODE_REMOTE` environment variable to determine execution mode:

**Interactive CLI Mode**:
- `CLAUDE_CODE_REMOTE` is unset or empty
- Use AskUserQuestion for fix selection
- Return implementation summary

**GitHub Hook Mode**:
- `CLAUDE_CODE_REMOTE` equals "true"
- Load policy from `.claude/fix-policy.yaml`
- Auto-select fixes based on policy
- Return summary formatted for PR comment
- **CRITICAL**: Create local commits only, do NOT push to remote

If `--auto` flag is provided, force GitHub Hook Mode regardless of environment variable.

### Step 3: Load Fix Policy (GitHub Hook Mode Only)

If in GitHub Hook Mode, attempt to load fix policy:

**Policy file path**: `.claude/fix-policy.yaml`

Expected format:
```yaml
fix_policy:
  auto_fix:
    CRITICAL: "balanced"  # Which option to auto-apply: minimal | balanced | comprehensive
    HIGH: "minimal"
    MEDIUM: "skip"
    LOW: "skip"

  constraints:
    max_files_per_fix: 5
    max_total_fixes: 10
    require_tests: true

  commit_strategy: "per-fix"  # per-fix | per-phase
```

**If policy file doesn't exist**, use default policy:
```yaml
fix_policy:
  auto_fix:
    CRITICAL: "balanced"
    HIGH: "minimal"
    MEDIUM: "skip"
    LOW: "skip"
  constraints:
    max_files_per_fix: 5
    max_total_fixes: 10
    require_tests: true
  commit_strategy: "per-fix"
```

### Step 4: Load Findings from Source

Parse the `findings-source` argument:

**If "last" (default)**:
- Look for most recent findings in session context
- Findings should be from previous `/redteam` command output
- Parse the markdown report to extract findings with IDs, titles, severity, evidence

**If "file:path"**:
- Read YAML file at specified path
- Expected format:
  ```yaml
  findings:
    - id: RF-001
      title: "Finding title"
      severity: CRITICAL
      category: reasoning-flaws
      evidence: "Evidence text"
      impact: "Impact description"
      recommendation: "Recommendation"
  ```

**Error handling**:
- If no findings found, return:
  ```markdown
  # Red Team Fix Orchestrator

  No findings available to fix. Please run `/redteam` first to generate findings.
  ```

### Step 5: Launch Fix Orchestrator Agent

Create structured input for the fix-orchestrator agent:

```yaml
orchestrator_input:
  findings: [list of finding summaries]
  mode: interactive | auto
  pal_available: [true/false from Step 1]
  policy: [policy object if auto mode, omit if interactive]
  commit_strategy: [per-fix | per-phase from args or policy]
  max_parallel: [N from args or default 4]
```

Launch the orchestrator:

```
Task: Launch fix-orchestrator agent
Agent: agents/fix-orchestrator.md
Model: opus
Prompt: [YAML orchestrator_input]
```

The orchestrator will:
- Analyze dependencies
- Group findings into phases
- Either return question_batches (interactive) or execute immediately (auto)

### Step 6: Handle Interactive Fix Selection (CLI Mode Only)

If mode is interactive, the orchestrator returns `question_batches` for user selection.

For each batch in `question_batches`:

**Present questions using AskUserQuestion**:
- Max 4 questions per batch
- Grouped by severity (CRITICAL_HIGH first, then MEDIUM)
- Each question offers fix options A/B/C plus "Other"

```
AskUserQuestion(questions=[
    {
        "question": "[finding_id]: [finding_title]\nSeverity: [severity] | How should we fix this?",
        "header": "[finding_id]",
        "multiSelect": false,
        "options": [
            {
                "label": "A: [option_a_label]",
                "description": "[option_a_description]"
            },
            {
                "label": "B: [option_b_label]",
                "description": "[option_b_description]"
            },
            {
                "label": "C: [option_c_label]",
                "description": "[option_c_description]"
            }
        ]
    },
    # ... up to 4 questions per batch
])
```

**Process user selections**:
- Map question headers (finding IDs) to selected options
- If user selects "Other", use their custom input
- If user skips (no selection), exclude from fixes

After all batches are presented, send user selections back to orchestrator:

```yaml
user_selections:
  - finding_id: RF-001
    selected_option: B
  - finding_id: AG-003
    selected_option: A
    custom_input: null
  - finding_id: CM-005
    selected_option: skip
```

Orchestrator will proceed with fix execution for selected findings.

### Step 7: Return Execution Summary

After the orchestrator completes (either interactively or automatically), it returns an `execution_summary`:

```yaml
execution_summary:
  total_findings: 8
  selected_for_fix: 3
  phases_executed: 2
  successful_fixes:
    - finding_id: RF-001
      selected_option: B
      commit_hash: abc123f
      files_changed: [AuthController.ts, ValidationMiddleware.ts]
      validation: success
    - finding_id: AG-003
      selected_option: A
      commit_hash: def456a
      files_changed: [RoleMiddleware.ts]
      validation: success
  failed_fixes:
    - finding_id: CM-005
      selected_option: B
      error: "Validation failed after 2 retries: Type errors in contextProcessor.ts"
      revert_command: "git revert def456a"
  skipped_fixes:
    - finding_id: AG-007
      reason: "Severity MEDIUM below policy threshold"
  commits_created: [abc123f, def456a]
```

**Format output based on mode**:

#### Interactive CLI Mode:
```markdown
# Red Team Fix Orchestration Complete

## Summary
[N] findings analyzed | [M] fixes applied | [P] commits created

---

## Successfully Applied

### RF-001: Invalid inference in authentication (CRITICAL)
**Fix applied**: B: Input validation layer
**Files changed**: AuthController.ts, ValidationMiddleware.ts
**Commit**: `abc123f`
**Validation**: ✓ All checks passed

[Repeat for each successful fix]

---

## Failed Fixes

### CM-005: Context manipulation (MEDIUM)
**Attempted fix**: B: Context isolation
**Error**: Validation failed after 2 retries: Type errors in contextProcessor.ts
**Revert**: `git revert def456a`
**Next steps**: Review type errors manually

[Repeat for each failed fix]

---

## Skipped

- **AG-007**: Severity MEDIUM below policy threshold

---

**Next steps**:
1. Review commits: `git log --oneline -[P]`
2. Run full test suite: `npm test` (or appropriate command)
3. Review failed fixes manually if any
```

#### GitHub Hook Mode:
```markdown
## Red Agent Fix Report

**Findings analyzed**: [N]
**Fixes applied**: [M]
**Commits created**: [P]

### Applied Fixes

#### ✓ RF-001: Invalid inference in authentication (CRITICAL)
- **Fix applied**: B: Input validation layer
- **Files changed**: AuthController.ts, ValidationMiddleware.ts
- **Commit**: `abc123f`
- **Tests**: ✓ Passed

[Repeat for each successful fix]

### Failed Fixes

#### ✗ CM-005: Context manipulation (MEDIUM)
- **Attempted fix**: B: Context isolation
- **Error**: Validation failed after 2 retries
- **Revert**: `git revert def456a`

[Repeat for each failed fix]

### Skipped Fixes

#### ⏭ AG-007: Hidden assumption (MEDIUM)
- **Reason**: Severity below auto-fix threshold per policy

---
Generated by [Claude Code Red Agent](https://github.com/anthropics/claude-code)
```

## Context Isolation Rules

This command is the BRIDGE between main session and fix orchestration:

- Main session context stays CLEAN
- Only structured snapshot data passes to orchestrator
- Fix execution isolated in orchestrator context
- Only sanitized summary returns to user
- No adversarial reasoning enters main session

## Error Handling

**If orchestrator returns no fixable findings**:
```markdown
# Red Team Fix Orchestrator

No fixable findings at CRITICAL, HIGH, or MEDIUM severity were identified.

Run `/redteam` with a different mode or target to generate findings.
```

**If orchestrator fails**:
```markdown
# Red Team Fix Orchestrator - Error

The fix orchestrator encountered an error: [error message]

Please check:
1. Findings source is valid
2. Policy file format is correct (if using GitHub hook mode)
3. Git working directory is clean

You can retry with: `/redteam-fix-orchestrator [args]`
```

**If policy file is malformed (GitHub hook mode)**:
```markdown
# Red Team Fix Orchestrator - Policy Error

Failed to load fix policy from `.claude/fix-policy.yaml`:
[Parse error details]

Using default policy instead.

[Continue with execution]
```

## Critical Rules

1. **NO DIRECT FIXING** - This command never applies fixes directly, only orchestrates
2. **MODE DETECTION** - Always check CLAUDE_CODE_REMOTE for execution mode
3. **NO AUTO-PUSH** - In GitHub hook mode, create local commits only, never push
4. **PAL OPTIONAL** - PAL availability check must not block execution
5. **CLEAN CONTEXT** - Keep main session context clean, pass structured data only
6. **PRESERVE FINDING IDS** - Use exact finding IDs from red team analysis
7. **COMPLETE SUMMARY** - Return full results including successful, failed, and skipped fixes

## Example Flows

### Example 1: Interactive CLI

User runs: `/redteam-fix-orchestrator last`

1. PAL check: available=true
2. Mode: interactive (CLAUDE_CODE_REMOTE not set)
3. Load findings from last `/redteam` run: 5 findings
4. Launch orchestrator with mode=interactive
5. Orchestrator returns 2 question batches
6. Present batch 1 (CRITICAL+HIGH): 3 questions
7. User selects: RF-001→B, AG-002→A, CM-003→skip
8. Present batch 2 (MEDIUM): 2 questions
9. User selects: RF-004→A, AG-005→Other("Add logging")
10. Send selections to orchestrator
11. Orchestrator executes: 4 fixes in 2 phases
12. Return summary: 3 successful, 1 failed, 1 skipped

### Example 2: GitHub Hook

GitHub Action runs: `/redteam-fix-orchestrator file:findings.yaml --auto`

1. PAL check: available=false (no MCP in CI)
2. Mode: auto (--auto flag)
3. Load policy from `.claude/fix-policy.yaml`
4. Load findings from findings.yaml: 8 findings
5. Launch orchestrator with mode=auto, policy
6. Orchestrator auto-selects based on policy
7. Orchestrator executes: 3 fixes in 2 phases
8. Creates commits: abc123f, def456a, ghi789c (local only, no push)
9. Return PR comment format summary
10. Separate GitHub Action step handles push (optional)
