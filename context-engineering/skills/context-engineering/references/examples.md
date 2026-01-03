# Production Examples

Real-world patterns from the red-agent plugin implementation.

## Example 1: Coordinator Context Isolation

From `red-agent/agents/red-team-coordinator.md`:

### Phase-Based Context Tiers

```yaml
# Phase 1: FULL context to analyzer
Task: Analyze context snapshot
Agent: coordinator-internal/context-analyzer.md
Prompt: [Pass the full snapshot YAML received from command]

# Phase 2: MINIMAL context to strategist
Task: Select attack vectors
Agent: coordinator-internal/attack-strategist.md
Prompt:
  mode: [mode from snapshot]
  analysis_summary:
    claim_count: [from analysis]
    high_risk_claims_count: [count of high_risk_claims]
    patterns: [patterns_detected]
    top_risks: [risk_surface_summary]

# Phase 3: SELECTIVE context to attackers
Each attacker receives SELECTIVE context (NOT full snapshot):
  context_analysis: [from Phase 1]
  attack_vectors: [relevant vectors for THIS attacker only]
  claims:
    high_risk: [high_risk_claims relevant to this attack type]
    total_count: [claim_count]
  mode: [mode from snapshot]
```

### Explicit NOT PASSED

```yaml
**DO NOT pass**: Full snapshot, files_read list, tools_invoked list, conversational_arc
```

This explicit exclusion list prevents accidental context leakage.

---

## Example 2: Severity-Based Batching

From `red-agent/agents/red-team-coordinator.md`:

### Batching Configuration

```yaml
findings_by_severity:
  CRITICAL: [list of CRITICAL findings]
  HIGH: [list of HIGH findings]
  MEDIUM: [list of MEDIUM findings]
  LOW_INFO: [list of LOW and INFO findings]
```

### Mode-Based Routing

```yaml
quick mode: SKIP grounding entirely

standard mode:
- CRITICAL + HIGH → evidence-checker + proportion-checker
- MEDIUM → evidence-checker only
- LOW/INFO → SKIP grounding

deep mode:
- CRITICAL → ALL 4 grounding agents IN PARALLEL
- HIGH → evidence-checker + proportion-checker
- MEDIUM → evidence-checker only
- LOW/INFO → SKIP grounding
```

### Impact

- **60-70% fewer grounding operations** in standard mode
- **Quality maintained** - high-priority items still fully validated

---

## Example 3: Grounding Agent Input

From `red-agent/coordinator-internal/grounding/evidence-checker.md`:

### FILTERED Context

```yaml
## Input

You receive (FILTERED context - NOT all findings):
- `findings_to_ground`: Only findings assigned to this agent based on severity batching
  - In **deep mode**: CRITICAL, HIGH, and MEDIUM findings
  - In **standard mode**: CRITICAL, HIGH, and MEDIUM findings
  - LOW/INFO findings are NEVER sent to grounding
- `mode`: Analysis mode (quick|standard|deep)
- `claim_count`: Total claims analyzed (for context)

**NOT provided** (to minimize context):
- Full snapshot
- Unrelated findings (outside severity batch)
- Full conversational_arc
```

### Key Pattern

The grounding agent:
1. Receives only findings it should validate
2. Knows the mode (for calibration)
3. Has count for context (without full data)
4. Explicitly lists what it does NOT receive

---

## Example 4: Synthesizer Metadata

From `red-agent/coordinator-internal/insight-synthesizer.md`:

### METADATA Input

```yaml
Task: Generate final report
Agent: coordinator-internal/insight-synthesizer.md
Prompt:
  mode: [mode]
  scope_metadata:
    message_count: [from snapshot.conversational_arc or estimate]
    files_analyzed: [count of snapshot.files_read]
    claims_analyzed: [claim_count from analysis]
    categories_covered: [count of attack vectors executed]
    grounding_enabled: [true if not quick mode]
    grounding_agents_used: [count based on mode]
  raw_findings: [from attackers]
  grounding_results: [from grounding agents, or null if quick mode]
```

### Key Pattern

The synthesizer:
1. Gets **counts**, not full data
2. Gets **findings and results** (its actual work input)
3. Does NOT get the original snapshot (just counts for limitations section)

---

## Example 5: Skill Progressive Disclosure

From `red-agent/skills/multi-agent-collaboration/SKILL.md`:

### Level 1: Always Loaded (SKILL.md header)

```yaml
---
name: Multi-Agent Collaboration
description: >
  This skill should be used when designing agent coordination...
---
```

~100 tokens, triggers skill loading.

### Level 2: On Trigger (SKILL.md body)

- Pattern selection framework table
- Four Laws quick reference
- Standard handoff protocol
- Anti-patterns checklist

~2000 tokens, loaded when skill invoked.

### Level 3: On Demand (references/)

```
references/
├── context-engineering.md   # Detailed patterns
├── patterns.md              # Full YAML definitions
└── examples.md              # Implementation examples
```

Loaded only when agent explicitly needs deep detail.

---

## Example 6: Output Validation Hook

From `red-agent/hooks/hooks.json`:

### PostToolUse Validation

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "tool_name": "Task"
      },
      "hooks": [
        {
          "type": "prompt",
          "prompt": "..."
        }
      ]
    }
  ]
}
```

### Validation Pattern

The hook:
1. Intercepts sub-agent outputs
2. Validates against Pydantic schema
3. Blocks and provides error if invalid
4. Allows coordinator to retry with error context

---

## Pattern Summary

| Pattern | Example | Impact |
|---------|---------|--------|
| Phase-based tiers | FULL→SELECTIVE→FILTERED→METADATA | 70% reduction |
| Explicit NOT PASSED | Document exclusions | Prevents leakage |
| Severity batching | HIGH→all, LOW→skip | 60-70% fewer ops |
| Metadata synthesis | Counts, not content | 80%+ reduction |
| Progressive disclosure | SKILL.md + references/ | On-demand loading |
| Output validation | PostToolUse hooks | Quality guardrails |
