# /optimize-plan Command

Optimize a plan file for efficient context management and agent handoffs.

## Usage

```
/optimize-plan [path]
```

## Arguments

**path** (optional):
- Path to plan file (default: most recent plan in `.claude/plans/`)

## Instructions

You are the MINIMAL entry point for plan optimization. Your ONLY job is to:

1. Locate the plan file to optimize
2. Launch the plan-coordinator agent
3. Return the coordinator's output directly

### Step 1: Locate Plan

If no path provided:
1. Look in `.claude/plans/` for recent `.md` files
2. If multiple found, use most recently modified
3. If none found, ask user to provide path

Verify the plan exists by attempting to read it.

### Step 2: Launch Coordinator

Use the Task tool to launch the plan-coordinator agent:

```
Task: Optimize plan for context efficiency
Agent: agents/plan-coordinator.md
Prompt:
  plan_path: [resolved plan file path]
```

The coordinator will:
1. Analyze plan structure and phases
2. Map context flows between phases
3. Identify optimization opportunities
4. Present options for user selection
5. Generate optimized version with comparison

### Step 3: Return Output

Return the coordinator's output DIRECTLY to the user.

DO NOT:
- Add commentary about the process
- Explain what the coordinator did
- Include intermediate analysis
- Modify the output

ONLY return the final optimized plan and comparison.

## Context Isolation Rules

This command is the FIREWALL between main session and optimization work:

- Main session context stays CLEAN
- Only plan path passes to coordinator
- Only the final output returns to user
- No intermediate analysis enters main context

## Examples

```
/optimize-plan
# Optimizes most recent plan in .claude/plans/

/optimize-plan ~/.claude/plans/my-feature-plan.md
# Optimizes specific plan file
```

## What Gets Optimized

### Context Tiers
- Assign appropriate context tiers to each phase
- Identify phases using higher tier than needed
- Add explicit tier specifications

### Handoff Points
- Minimize data transfer between phases
- Document explicit exclusions
- Add "NOT PASSED" sections

### Flow Efficiency
- Identify redundant data passing
- Suggest reference patterns for large data
- Recommend lazy loading where applicable

## Output Format

The optimization output includes:
- Before/after comparison of context per phase
- Estimated token reduction
- Specific changes recommended
- Rewritten plan sections (optional)
