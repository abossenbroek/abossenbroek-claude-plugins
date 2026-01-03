# /audit-context Command

Audit a plugin or plan for context management inefficiencies.

## Usage

```
/audit-context [path]
```

## Arguments

**path** (optional):
- Path to plugin directory or plan file (default: auto-detect plugin in workspace)

## Instructions

You are the MINIMAL entry point for context auditing. Your ONLY job is to:

1. Determine the audit target
2. Launch the audit-coordinator agent
3. Return the coordinator's output directly

### Step 1: Determine Target

If no path provided:
1. Look for `.claude-plugin/plugin.json` in workspace
2. If not found, look for recent plans in `.claude/plans/`
3. If nothing found, ask user to specify

Determine if target is a plugin or plan based on structure.

### Step 2: Launch Coordinator

Use the Task tool to launch the audit-coordinator agent:

```
Task: Audit context management
Agent: agents/audit-coordinator.md
Prompt:
  target_path: [resolved path]
  target_type: plugin|plan
```

The coordinator will:
1. Analyze the target structure
2. Map context flows
3. Identify Four Laws violations
4. Calculate token waste estimates
5. Generate comprehensive audit report

### Step 3: Return Output

Return the coordinator's audit report DIRECTLY to the user.

DO NOT:
- Add commentary about the process
- Explain what the coordinator did
- Include intermediate analysis
- Modify the report

ONLY return the final audit report.

## Context Isolation Rules

This command is the FIREWALL between main session and audit work:

- Main session context stays CLEAN
- Only target path passes to coordinator
- Only the final audit report returns to user
- No intermediate analysis enters main context

## Examples

```
/audit-context
# Audits auto-detected plugin in workspace

/audit-context ./red-agent
# Audits specific plugin directory

/audit-context ~/.claude/plans/my-plan.md
# Audits specific plan file
```

## What Gets Audited

### Four Laws Compliance

| Law | Audit Check |
|-----|-------------|
| Selective Projection | Are full snapshots passed unnecessarily? |
| Tiered Fidelity | Do agents have appropriate tier specs? |
| Reference vs Embedding | Is large data embedded instead of referenced? |
| Lazy Loading | Is data loaded upfront when not needed? |

### Anti-Patterns

- Snapshot Broadcasting - Same data to every agent
- Defensive Inclusion - "Maybe they need this"
- Grounding Everything - Validating low-priority items

### Flow Issues

- Redundancy - Same data passed multiple times
- Missing Tiers - Agents without context tier specification
- Large Handoffs - >2000 tokens in single transfer

## Output Format

The audit report includes:
- Executive summary with overall health score
- Violations by severity (HIGH/MEDIUM/LOW)
- Estimated token waste per violation
- Specific fix recommendations
- Prioritized action items
