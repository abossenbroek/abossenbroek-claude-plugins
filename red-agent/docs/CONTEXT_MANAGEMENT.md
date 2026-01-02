# Context Management Guidelines

This document defines SOTA patterns for minimal context handoff between agents.

## Core Principles

### 1. Selective Projection (Not Full Embedding)

**Anti-pattern**: Passing full 20KB snapshot to every sub-agent
**Pattern**: Pass only fields each agent actually needs

```yaml
# BAD: Full snapshot to every agent
snapshot: {...20KB of data...}

# GOOD: Selective projection
context:
  mode: deep
  target: conversation
  claims_analyzed: 15
  # Only include what this specific agent needs
```

### 2. Tiered Context Fidelity

Different agents need different levels of detail:

| Agent Type | Context Fidelity | What They Need |
|------------|------------------|----------------|
| context-analyzer | FULL | Complete snapshot (first pass) |
| attack-strategist | MINIMAL | mode + analysis summary |
| attackers | SELECTIVE | analysis + relevant vectors + claims |
| grounding | FILTERED | findings for their severity tier |
| synthesizer | METADATA | scope stats + aggregated findings |

### 3. Reference vs Embedding

When data is large, pass a reference instead of embedding:

```yaml
# Embedding (expensive)
raw_findings:
  - {full finding 1}
  - {full finding 2}
  # ... 40-60 findings in deep mode

# Reference (efficient)
findings_summary:
  total: 45
  by_severity: {CRITICAL: 3, HIGH: 12, MEDIUM: 20, LOW: 10}
  ids: [RF-001, RF-002, AG-001, ...]
# Agent fetches full finding only if needed
```

### 4. Lazy Loading

Load data on-demand, not upfront:

1. Pass minimal context initially
2. Agent requests specific data if needed
3. Coordinator provides targeted response

## Implementation Patterns

### Pattern A: Attacker Context Projection

Attackers need to find vulnerabilities. They do NOT need:
- Full conversation history
- Files not relevant to their category
- Tool invocation logs (usually)

**Minimal attacker context**:
```yaml
context_analysis: [from Phase 1 - required]
attack_vectors: [relevant vectors only]
claims:
  high_risk: [filtered claims for this attack type]
  count: 15
mode: deep
```

**Removed from attacker context**:
```yaml
# These are NOT passed to attackers:
snapshot.conversational_arc  # Only needed by context-analyzer
snapshot.files_read          # Full list not needed
snapshot.tools_invoked       # Full list not needed
```

### Pattern B: Severity-Based Grounding Batches

Instead of all grounding agents processing all findings:

**Deep Mode Batching**:
```
CRITICAL findings (3) → all 4 grounding agents
HIGH findings (12)    → evidence-checker + proportion-checker
MEDIUM findings (20)  → evidence-checker only
LOW/INFO findings     → skip grounding
```

**Standard Mode Batching**:
```
CRITICAL + HIGH findings → evidence-checker + proportion-checker
MEDIUM findings          → evidence-checker only
LOW/INFO findings        → skip grounding
```

**Context reduction**: 60-70% fewer grounding operations in deep mode

### Pattern C: Synthesizer Scope Metadata

The insight-synthesizer only uses 3 fields from snapshot:
1. Message count (for limitations section)
2. Files analyzed count
3. Mode (for methodology note)

**Optimized synthesizer input**:
```yaml
mode: deep
scope_metadata:
  message_count: 45
  files_analyzed: 8
  claims_count: 15
  categories_covered: 10
  grounding_enabled: true
  grounding_agents_used: 4

findings: [aggregated findings with confidence adjustments]
grounding_adjustments: [{finding_id, original_confidence, adjusted_confidence}]
```

**Removed from synthesizer context**:
```yaml
# NOT passed to synthesizer:
snapshot.conversational_arc
snapshot.claims  # Already in findings
snapshot.files_read  # Just need count
```

### Pattern D: Fix Planner Minimal Context

Each fix-planner only needs:
1. The specific finding it's fixing
2. Affected files/components (not all files)
3. Relevant patterns (not all patterns)

**Optimized fix-planner input**:
```yaml
finding:
  id: RF-001
  title: "Invalid inference"
  severity: CRITICAL
  evidence: "..."
  recommendation: "..."

affected_context:
  files: ["auth.py", "validator.py"]  # Only relevant files
  pattern: "authentication"

# NOT passed:
# - Full snapshot
# - Other findings
# - Unrelated files
```

## Data Flow Diagrams

### Current (Verbose)

```
Command (builds 20KB snapshot)
    ↓ [20KB]
red-team-coordinator
    ├─ context-analyzer [20KB] → returns 5KB analysis
    ├─ attack-strategist [20KB + 5KB]
    ├─ 4 attackers [20KB + 5KB + vectors each] = 100KB+ total
    ├─ 4 grounding [20KB + all findings each] = 80KB+ total
    └─ synthesizer [20KB + all outputs] = 50KB+

Total context passed: ~250KB+
```

### Optimized (Selective)

```
Command (builds 20KB snapshot)
    ↓ [20KB]
red-team-coordinator
    ├─ context-analyzer [20KB] → returns 5KB analysis
    ├─ attack-strategist [1KB: mode + analysis summary]
    ├─ 4 attackers [3KB each: analysis + vectors + claims] = 12KB total
    ├─ grounding [batched by severity] = 15KB total
    └─ synthesizer [2KB: scope + findings summary]

Total context passed: ~55KB (78% reduction)
```

## Implementation Checklist

### Phase 1: Coordinator Updates
- [ ] Update red-team-coordinator Phase 2 (strategist minimal context)
- [ ] Update red-team-coordinator Phase 3 (attacker selective context)
- [ ] Update red-team-coordinator Phase 4 (severity batching)
- [ ] Update red-team-coordinator Phase 5 (synthesizer scope metadata)

### Phase 2: Sub-Agent Updates
- [ ] Update attacker agents to document minimal input requirements
- [ ] Update grounding agents to handle filtered inputs
- [ ] Update insight-synthesizer to use scope_metadata

### Phase 3: Fix Coordinator
- [ ] Update fix-coordinator Phase C (minimal fix-planner context)
- [ ] Update fix-planner to document minimal input requirements

## Metrics

Track these to validate optimization:

1. **Context Size**: Total bytes passed between agents
2. **Agent Calls**: Number of sub-agent invocations
3. **Redundancy Ratio**: Duplicate data passed / unique data
4. **Grounding Efficiency**: Findings processed / grounding operations

## Finding Conciseness Guidelines

Findings are passed to multiple downstream agents (grounding, synthesizer). Keep them concise.

### Target Field Lengths

| Field | Target | Guidance |
|-------|--------|----------|
| `title` | 5-10 words | Action-oriented, specific |
| `evidence.quote` | 1-2 sentences | Minimum needed to prove the point |
| `evidence.description` | 2-3 sentences | What's wrong and why |
| `probing_question` | 1 sentence | Single focused question |
| `impact.if_exploited` | 1-2 sentences | Concrete consequence |
| `recommendation` | 1-2 sentences | Specific, actionable fix |

### Writing Style for Findings

**DO:**
- Lead with the most important information
- Use specific terms, not vague language
- One idea per field
- Assume reader has context from the title

**DON'T:**
- Repeat information across fields
- Include hedging ("might", "could potentially")
- Explain obvious implications
- Quote entire paragraphs when a phrase suffices

### Example: Verbose vs Concise

**Verbose (avoid):**
```yaml
evidence:
  quote: "The user mentioned in message 5 that they wanted to implement authentication, and then in message 7 they discussed various options including OAuth and JWT, and the assistant recommended JWT without fully exploring the security implications of each approach or considering the specific requirements of the user's application context."
  description: "The assistant made a recommendation for JWT authentication without adequately considering all the factors that might influence this decision, including the user's specific security requirements, the nature of the application, and the potential trade-offs between different authentication approaches."
```

**Concise (preferred):**
```yaml
evidence:
  quote: "the assistant recommended JWT without fully exploring the security implications"
  description: "Auth recommendation made without discussing user's security requirements or trade-offs between OAuth vs JWT."
```

## Anti-Patterns to Avoid

1. **Snapshot Broadcasting**: Passing full snapshot to every agent
2. **Defensive Over-inclusion**: "Maybe they need this" → they don't
3. **Grounding Everything**: LOW/INFO findings don't need full grounding
4. **Embedding Large Lists**: Pass counts/summaries, not full arrays
5. **Repeated Context**: Same data passed multiple times in chain
6. **Verbose Findings**: Over-explaining when concise would suffice

## References

- Claude Agent SDK: Minimal context patterns
- LangChain: Memory optimization strategies
- CrewAI: Agent communication protocols
