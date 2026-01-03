# The Four Laws of Context Management

Detailed explanations and implementation patterns for each law.

## Law 1: Selective Projection

**Principle**: Pass only the fields each agent needs, not full data structures.

### The Problem

```yaml
# BAD: Full snapshot everywhere
prompt_to_analyzer:
  snapshot: {...20KB...}

prompt_to_validator:
  snapshot: {...20KB...}  # Same 20KB again!

prompt_to_synthesizer:
  snapshot: {...20KB...}  # And again!
```

Each agent receives the full context even though they only need specific parts.

### The Solution

```yaml
# GOOD: Selective projection per role
prompt_to_analyzer:
  mode: deep
  target_files:
    - file: "[path]"
      content: "[content]"
  # Only what analyzer needs

prompt_to_validator:
  findings_to_validate:
    - id: "[ID]"
      claim: "[claim]"
  # Only what validator needs

prompt_to_synthesizer:
  validated_findings: [...]
  scope_stats:
    total_analyzed: 15
  # Only what synthesizer needs
```

### Implementation Steps

1. **Identify role requirements**: What does this agent actually need?
2. **Extract relevant fields**: Pull only those fields from the source
3. **Document exclusions**: Add "NOT PASSED" section

### Typical Reduction: 30-50%

---

## Law 2: Tiered Context Fidelity

**Principle**: Define explicit tiers based on agent role in the workflow.

### Tier Definitions

| Tier | What's Included | When to Use |
|------|-----------------|-------------|
| **FULL** | Complete data, all details | Initial analysis, first agent |
| **SELECTIVE** | Relevant subset, filtered fields | Domain-specific workers |
| **FILTERED** | Criteria-matched items only | Validators, grounding agents |
| **MINIMAL** | Counts, modes, identifiers | Routing, strategy decisions |
| **METADATA** | Summary statistics only | Final synthesis |

### Example Workflow

```
coordinator (THIN ROUTER - no data processing)
    │
    ├──[FULL]──> analyzer
    │               └──> Returns structured analysis
    │
    ├──[SELECTIVE]──> improver
    │                   └──> Returns specific improvements
    │
    ├──[FILTERED]──> validator
    │                  └──> Returns validation results
    │
    └──[METADATA]──> synthesizer
                       └──> Returns final report
```

### Implementation Pattern

In agent files, explicitly state the tier:

```yaml
## Context Management

This agent receives SELECTIVE context.

## Input

You receive (SELECTIVE context):
- analysis_summary: Key findings from analyzer
- focus_area: This agent's specialty
- relevant_files: Only files for this focus

**NOT provided** (tier: SELECTIVE excludes):
- Full plugin contents
- Other focus areas
- Raw analysis data
```

### Typical Reduction: 40-60%

---

## Law 3: Reference vs Embedding

**Principle**: For large data, pass reference instead of full structure.

### The Problem

```yaml
# BAD: Embedding large arrays
prompt:
  all_findings:
    - {...finding 1...}
    - {...finding 2...}
    # ... 40+ findings, each 200+ tokens
  # Total: 8000+ tokens
```

### The Solution

```yaml
# GOOD: Reference pattern
prompt:
  findings_summary:
    total: 45
    by_severity:
      CRITICAL: 3
      HIGH: 12
      MEDIUM: 20
      LOW: 10
    # Agent fetches specific findings on-demand

  # If agent needs specific findings:
  high_severity_findings:
    - {...only CRITICAL and HIGH...}
  # 15 findings instead of 45
```

### When to Use References

| Data Size | Strategy |
|-----------|----------|
| < 500 tokens | Embed directly |
| 500-2000 tokens | Consider reference |
| > 2000 tokens | Always reference |

### Reference Patterns

**Summary with on-demand fetch**:
```yaml
findings_available:
  total: 45
  fetch_by: "severity or ID"
  # Agent requests specific items
```

**Grouped by relevance**:
```yaml
high_priority:
  - {...}  # Only what's needed
others_count: 35
# Skip low-priority details
```

### Typical Reduction: 50-80%

---

## Law 4: Lazy Loading

**Principle**: Load data on-demand, not upfront.

### The Problem

```yaml
# BAD: Loading everything upfront
initial_context:
  all_agents: [...every agent file...]
  all_skills: [...every skill...]
  all_commands: [...every command...]
  full_analysis: [...complete analysis...]
  # Most of this won't be used
```

### The Solution

```yaml
# GOOD: Lazy loading
initial_context:
  scope:
    agent_count: 14
    skill_count: 2
    command_count: 4
  available_data:
    - name: agent_files
      fetch: "by name or pattern"
    - name: analysis
      fetch: "by category"

# Agent requests what it needs:
# "Fetch agent files matching 'grounding/*'"
# "Fetch analysis for 'context' category"
```

### Implementation Strategies

**1. Scope-first pattern**:
```yaml
# Pass scope info, not full data
scope:
  items: 45
  categories: [A, B, C]
  # Details fetched on-demand
```

**2. Progressive loading**:
```yaml
# Phase 1: Overview
overview:
  summary: "..."
  item_count: 45

# Phase 2: If needed, drill down
# Agent decides what to fetch
```

**3. Conditional loading**:
```yaml
# Only load if condition met
if_mode_deep:
  fetch: full_analysis
else:
  use: summary_only
```

### Typical Reduction: 30-50%

---

## Combined Impact

When all four laws are applied:

| Scenario | Before | After | Reduction |
|----------|--------|-------|-----------|
| 10-agent workflow | 100K tokens | 25K tokens | 75% |
| Analysis pipeline | 50K tokens | 15K tokens | 70% |
| Validation chain | 30K tokens | 8K tokens | 73% |

## Quick Checklist

For each agent handoff, verify:

- [ ] Only required fields passed (Law 1)
- [ ] Context tier documented (Law 2)
- [ ] Large data uses references (Law 3)
- [ ] Data loaded on-demand where possible (Law 4)
- [ ] "NOT PASSED" section present
