# Context Tiers

Detailed guide to context tier selection and implementation.

## Tier Definitions

### FULL Context

**What it includes**: Complete, unfiltered data from the source.

**When to use**:
- First agent in a pipeline (needs complete picture)
- Initial analysis phases
- When no prior analysis exists

**Typical size**: 5,000-20,000 tokens

**Example**:
```yaml
# FULL context for initial analyzer
You receive (FULL context):
- plugin_manifest: Complete plugin.json
- agent_files: All agent files with full content
- skill_files: All skill files
- hooks_config: Complete hooks.json
- additional_files: CLAUDE.md, scripts, etc.
```

---

### SELECTIVE Context

**What it includes**: Relevant subset filtered by role or domain.

**When to use**:
- Domain-specific workers
- Agents focusing on one aspect
- When prior analysis identified relevant items

**Typical size**: 1,000-5,000 tokens

**Example**:
```yaml
# SELECTIVE context for context-optimizer
You receive (SELECTIVE context):
- analysis_summary: Key findings from analyzer
- focus_area: context
- relevant_files: Only files with context issues
- violations_to_address: Only context-related violations

**NOT provided** (focus is context only):
- Files without context issues
- Orchestration analysis
- Handoff analysis
```

---

### FILTERED Context

**What it includes**: Items matching specific criteria.

**When to use**:
- Validators checking specific items
- Grounding agents verifying subset
- Severity-batched processing

**Typical size**: 500-2,000 tokens

**Example**:
```yaml
# FILTERED context for pattern-checker
You receive (FILTERED context):
- improvements_to_check: Only HIGH priority improvements
- focus_area: context
- improvement_count: 5 (total for context)

**NOT provided** (filtered by priority):
- LOW/MEDIUM priority improvements
- Full analysis results
- Original plugin contents
```

---

### MINIMAL Context

**What it includes**: Mode settings, counts, identifiers only.

**When to use**:
- Routing decisions
- Strategy selection
- When only metadata needed for decision

**Typical size**: 100-500 tokens

**Example**:
```yaml
# MINIMAL context for strategy selection
You receive (MINIMAL context):
- mode: deep
- counts:
    agents: 14
    violations: 8
    opportunities: 12
- focus_area: all
- priority_distribution:
    HIGH: 3
    MEDIUM: 5
    LOW: 4

**NOT provided** (minimal = counts only):
- Actual violation details
- File contents
- Code samples
```

---

### METADATA Context

**What it includes**: Summary statistics for final reporting.

**When to use**:
- Final synthesis
- Report generation
- When only aggregate numbers needed

**Typical size**: 50-200 tokens

**Example**:
```yaml
# METADATA context for synthesizer
You receive (METADATA context):
- scope_metadata:
    plugin_name: "red-agent"
    files_analyzed: 14
    improvements_available: 12
    improvements_selected: 5
- selected_improvements: [IDs and descriptions only]
- grounding_summary: [pass/fail counts only]

**NOT provided** (metadata = stats only):
- Full analysis results
- Rejected improvements
- Original plugin contents
- Intermediate agent outputs
```

---

## Tier Selection Guide

### Decision Tree

```
Is this the first agent in the pipeline?
├── YES → FULL
└── NO → Does this agent need to see raw data?
         ├── YES → Does it need ALL raw data?
         │         ├── YES → FULL
         │         └── NO → SELECTIVE
         └── NO → Does it need specific items?
                  ├── YES → FILTERED
                  └── NO → Does it need counts/modes?
                           ├── YES → MINIMAL
                           └── NO → METADATA
```

### By Agent Role

| Role | Typical Tier | Rationale |
|------|--------------|-----------|
| Initial Analyzer | FULL | Needs complete picture |
| Domain Worker | SELECTIVE | Only their specialty |
| Validator | FILTERED | Specific items to check |
| Router/Coordinator | MINIMAL | Just needs counts/modes |
| Synthesizer | METADATA | Only aggregates for report |

### By Workflow Phase

| Phase | Tier | What's Passed |
|-------|------|---------------|
| Phase 1: Analysis | FULL | Everything |
| Phase 2: Work | SELECTIVE | Relevant subset |
| Phase 3: Grounding | FILTERED | Priority-batched |
| Phase 4: Selection | MINIMAL | Options + counts |
| Phase 5: Synthesis | METADATA | Stats + selections |

---

## Implementation Patterns

### Documenting Tiers

Always document the tier in the agent's Input section:

```yaml
## Context Management

This agent receives SELECTIVE context.

## Input

You receive (SELECTIVE context):
- [list what IS passed]

**NOT provided** (tier: SELECTIVE):
- [list what is NOT passed]
```

### Tier Transitions

When passing from one agent to another, reduce the tier:

```
FULL → SELECTIVE → FILTERED → MINIMAL → METADATA
```

Never increase tier in downstream agents:
- BAD: MINIMAL → FULL (fetching more data downstream)
- GOOD: FULL → SELECTIVE → FILTERED (progressive reduction)

### Tier Enforcement

Add to coordinator prompts:

```yaml
## Context Tiers (ENFORCE)

Each sub-agent receives a specific tier:
- plugin-analyzer: FULL (initial analysis)
- context-optimizer: SELECTIVE (focus area only)
- pattern-checker: FILTERED (priority batch only)
- synthesizer: METADATA (stats only)

DO NOT pass higher-tier data to lower-tier agents.
```

---

## Common Mistakes

### Mistake 1: Over-sharing

```yaml
# BAD: FULL when SELECTIVE would suffice
prompt_to_optimizer:
  all_files: [...everything...]
  full_analysis: [...everything...]

# GOOD: SELECTIVE for domain worker
prompt_to_optimizer:
  focus_area: context
  relevant_files: [...only context-related...]
  relevant_violations: [...only context violations...]
```

### Mistake 2: Under-specifying

```yaml
# BAD: No tier documented
## Input
You receive:
- data

# GOOD: Tier explicitly stated
## Input
You receive (SELECTIVE context):
- data: [relevant subset]

**NOT provided**:
- [explicit exclusions]
```

### Mistake 3: Tier Escalation

```yaml
# BAD: Fetching more data downstream
minimal_agent:
  # Has MINIMAL context
  # Then fetches FULL data from somewhere

# GOOD: Work with what you have
minimal_agent:
  # Has MINIMAL context
  # Makes decisions based on counts/modes only
```
