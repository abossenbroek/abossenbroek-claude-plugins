# Context Engineering Reference

This reference provides comprehensive patterns for managing context flow between agents in multi-agent systems. These patterns achieve 78%+ reduction in context overhead while maintaining analysis quality.

## The Four Laws of Context Management

### Law 1: Selective Projection (Not Full Embedding)

Pass only fields each agent actually needs, not full data structures.

**Anti-pattern**:
```yaml
# BAD: Full 20KB snapshot to every sub-agent
snapshot:
  conversational_arc: [...]      # 5KB
  claims: [...]                  # 8KB
  files_read: [...]              # 3KB
  tools_invoked: [...]           # 2KB
  high_risk_claims: [...]        # 2KB
```

**Pattern**:
```yaml
# GOOD: Selective projection - only what this agent needs
context:
  mode: deep
  target: conversation
  claims_analyzed: 15
  high_risk_summary:
    count: 4
    categories: [reasoning-flaws, assumption-gaps]
```

### Law 2: Tiered Context Fidelity

Different agents need different levels of detail. Define tiers explicitly.

| Fidelity | Description | When to Use |
|----------|-------------|-------------|
| FULL | Complete data structure | First-pass analysis, initial context building |
| SELECTIVE | Relevant subset of fields | Domain-specific workers with focused scope |
| FILTERED | Data matching specific criteria | Downstream processors handling subsets |
| MINIMAL | Mode, counts, metadata only | Strategy/routing decisions |
| METADATA | Scope stats only | Final synthesis, report generation |

**Implementation matrix**:
```yaml
context_tiers:
  # FULL: Agent needs complete picture to establish baseline
  context-analyzer:
    fidelity: FULL
    receives:
      - complete_snapshot
      - all_claims
      - full_history
    rationale: "First pass - must see everything to identify patterns"

  # MINIMAL: Only needs mode and summary to select strategy
  attack-strategist:
    fidelity: MINIMAL
    receives:
      - mode
      - analysis_summary.claim_count
      - analysis_summary.high_risk_count
      - analysis_summary.patterns
    rationale: "Routing decision - doesn't analyze content directly"

  # SELECTIVE: Needs analysis + own domain data
  attackers:
    fidelity: SELECTIVE
    receives:
      - context_analysis
      - relevant_attack_vectors  # Only for THIS attacker
      - filtered_claims          # Only claims relevant to attack type
      - mode
      - target
    not_provided:
      - full_snapshot
      - files_read_list
      - tools_invoked_list
      - conversational_arc
      - claims_for_other_attack_types
    rationale: "Focused analysis - only needs own attack domain"

  # FILTERED: Processes subset based on criteria
  grounding:
    fidelity: FILTERED
    receives:
      - findings_for_severity_tier  # Based on batching rules
    rationale: "Severity-based routing - different tiers get different agents"

  # METADATA: Only scope stats for final synthesis
  synthesizer:
    fidelity: METADATA
    receives:
      - mode
      - scope_metadata.message_count
      - scope_metadata.files_analyzed
      - scope_metadata.claims_count
      - aggregated_findings
      - grounding_adjustments
    not_provided:
      - full_snapshot
      - individual_claims
      - raw_conversation
    rationale: "Report generation - needs counts and processed findings only"
```

### Law 3: Reference vs Embedding

When data is large, pass a reference (count, ID, summary) instead of embedding the full structure.

**Embedding (expensive)**:
```yaml
raw_findings:
  - id: RF-001
    severity: CRITICAL
    title: "Invalid inference in auth flow"
    evidence:
      quote: "The authentication should work..."
      description: "The assistant assumed..."
    # ... 40-60 findings in deep mode, each 500+ bytes
```

**Reference (efficient)**:
```yaml
findings_summary:
  total: 45
  by_severity:
    CRITICAL: 3
    HIGH: 12
    MEDIUM: 20
    LOW: 10
  ids: [RF-001, RF-002, AG-001, ...]
  # Agent requests specific finding only if needed
```

**Decision matrix**:
| Data Size | Downstream Needs Full Data? | Pattern |
|-----------|----------------------------|---------|
| < 1KB | Always | Embed |
| 1-5KB | Yes, for analysis | Embed |
| 1-5KB | No, just for reference | Reference |
| > 5KB | Partial | Reference + on-demand fetch |
| > 5KB | Yes | Split into chunks, process in phases |

### Law 4: Lazy Loading

Load data on-demand, not upfront.

**Eager (wasteful)**:
```yaml
# Agent receives everything at start
full_context:
  snapshot: {...}           # 20KB - might not need
  all_findings: [...]       # 15KB - might need subset
  grounding_results: [...]  # 10KB - might not need
  historical_data: [...]    # 25KB - rarely needed
```

**Lazy (efficient)**:
```yaml
# Initial context is minimal
initial_context:
  mode: deep
  scope: {message_count: 45, files: 8}
  available_data:
    - name: findings
      count: 45
      fetch: "request findings by severity or ID"
    - name: grounding
      count: 120
      fetch: "request by finding_id"

# Agent requests what it needs
agent_request:
  fetch: findings
  filter: {severity: [CRITICAL, HIGH]}
  # Returns only 15 findings instead of 45
```

## Implementation Patterns

### Pattern A: Attacker Context Projection

Attackers probe for vulnerabilities. They do NOT need:
- Full conversation history
- Files not relevant to their category
- Tool invocation logs (usually)
- Claims for other attack types

**Minimal attacker context**:
```yaml
context_analysis:
  summary: "..."            # From Phase 1
  risk_surface: {...}       # Relevant patterns

attack_vectors:
  - category: reasoning-flaws
    style: socratic-questioning
    targets: [C1, C3, C7]   # Only relevant claim IDs
  - category: assumption-gaps
    style: assumption-inversion
    targets: [C2, C5]

claims:
  high_risk:
    - id: C1
      text: "The authentication should..."
      risk_score: 0.8
    - id: C3
      text: "This approach ensures..."
      risk_score: 0.7
  count: 15

mode: deep
```

**Removed from attacker context**:
```yaml
# NOT passed to attackers:
snapshot.conversational_arc  # Only needed by context-analyzer
snapshot.files_read          # Full list not needed
snapshot.tools_invoked       # Full list not needed
claims_for_other_attackers   # Each attacker gets own subset
```

### Pattern B: Severity-Based Grounding Batches

Instead of all grounding agents processing all findings, batch by severity.

**Deep Mode Batching**:
```
CRITICAL findings (3)  -> all 4 grounding agents
HIGH findings (12)     -> evidence-checker + proportion-checker
MEDIUM findings (20)   -> evidence-checker only
LOW/INFO findings (10) -> skip grounding entirely
```

**Standard Mode Batching**:
```
CRITICAL + HIGH findings -> evidence-checker + proportion-checker
MEDIUM findings          -> evidence-checker only
LOW/INFO findings        -> skip grounding
```

**Quick Mode**:
```
All findings -> skip grounding entirely
```

**Result**: 60-70% fewer grounding operations in deep mode.

**Implementation**:
```yaml
grounding_batches:
  - severity_tier: CRITICAL
    agents:
      - evidence-checker
      - proportion-checker
      - alternative-explorer
      - calibrator
    findings: [RF-001, RF-002, RF-003]

  - severity_tier: HIGH
    agents:
      - evidence-checker
      - proportion-checker
    findings: [RF-004, RF-005, ...]  # 12 findings

  - severity_tier: MEDIUM
    agents:
      - evidence-checker
    findings: [RF-016, RF-017, ...]  # 20 findings

  - severity_tier: [LOW, INFO]
    agents: []  # Skip grounding
    findings: [RF-036, ...]
```

### Pattern C: Synthesizer Scope Metadata

The insight-synthesizer generates reports. It only needs:
1. Message count (for limitations section)
2. Files analyzed count
3. Mode (for methodology note)
4. Processed findings with confidence adjustments

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

findings:
  - id: RF-001
    severity: CRITICAL
    title: "..."
    original_confidence: 0.85
    adjusted_confidence: 0.78
    grounding_notes: "Evidence strong but alternative exists"
  # ... processed findings only

grounding_summary:
  total_processed: 35
  confidence_adjustments: 12
  downgrades: 3
  upgrades: 2
```

**Not passed to synthesizer**:
```yaml
# NOT needed for report generation:
snapshot.conversational_arc
snapshot.claims           # Already processed into findings
snapshot.files_read       # Just need count
raw_grounding_outputs     # Only need summaries
```

### Pattern D: Fix Planner Minimal Context

Each fix-planner receives ONLY:
1. The specific finding it's fixing
2. Affected files/components (not all files)
3. Relevant patterns (not all patterns)

**Optimized fix-planner input**:
```yaml
finding:
  id: RF-001
  title: "Invalid inference in authentication flow"
  severity: CRITICAL
  evidence:
    quote: "The authentication should work because..."
    description: "Assumes OAuth always returns valid token"
  recommendation: "Add token validation before use"

affected_context:
  files: ["auth.py", "validator.py"]  # Only relevant files
  pattern: "authentication"
  related_claims: [C1, C3]

mode: deep
```

**Not passed**:
```yaml
# NOT passed to fix-planners:
full_snapshot
other_findings
unrelated_files
all_patterns
```

## Data Flow Comparison

### Verbose Approach (Anti-Pattern)

```
Command (builds 20KB snapshot)
    |
    v [20KB]
red-team-coordinator
    |
    +-- context-analyzer [20KB] -> returns 5KB analysis
    |
    +-- attack-strategist [20KB + 5KB = 25KB]
    |
    +-- 4 attackers [25KB each] = 100KB+ total
    |
    +-- 4 grounding agents [30KB each] = 120KB+ total
    |
    +-- synthesizer [50KB+ including all outputs]

Total context passed: ~320KB
```

### Optimized Approach (Pattern)

```
Command (builds 20KB snapshot)
    |
    v [20KB]
red-team-coordinator
    |
    +-- context-analyzer [20KB] -> returns 5KB analysis
    |
    +-- attack-strategist [1KB: mode + analysis summary]
    |
    +-- 4 attackers [3KB each] = 12KB total
    |
    +-- grounding [batched by severity] = 15KB total
    |
    +-- synthesizer [2KB: scope + findings summary]

Total context passed: ~55KB (83% reduction)
```

## Finding Conciseness Guidelines

Findings are passed to multiple downstream agents. Keep them brief.

### Target Field Lengths

| Field | Target | Guidance |
|-------|--------|----------|
| `title` | 5-10 words | Action-oriented, specific |
| `evidence.quote` | 1-2 sentences | Minimum needed to prove the point |
| `evidence.description` | 2-3 sentences | What's wrong and why |
| `probing_question` | 1 sentence | Single focused question |
| `impact.if_exploited` | 1-2 sentences | Concrete consequence |
| `recommendation` | 1-2 sentences | Specific, actionable fix |

### Writing Style

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

### Example Transformation

**Verbose (avoid)**:
```yaml
evidence:
  quote: "The user mentioned in message 5 that they wanted to
    implement authentication, and then in message 7 they discussed
    various options including OAuth and JWT, and the assistant
    recommended JWT without fully exploring the security implications
    of each approach or considering the specific requirements of the
    user's application context."
  description: "The assistant made a recommendation for JWT
    authentication without adequately considering all the factors
    that might influence this decision, including the user's specific
    security requirements, the nature of the application, and the
    potential trade-offs between different authentication approaches."
```

**Concise (preferred)**:
```yaml
evidence:
  quote: "the assistant recommended JWT without fully exploring the
    security implications"
  description: "Auth recommendation made without discussing user's
    security requirements or trade-offs between OAuth vs JWT."
```

## Anti-Patterns to Avoid

1. **Snapshot Broadcasting**
   - Passing full snapshot to every agent
   - Fix: Apply tiered fidelity

2. **Defensive Over-inclusion**
   - "Maybe they need this" -> they don't
   - Fix: Document what each agent DOES NOT receive

3. **Grounding Everything**
   - LOW/INFO findings don't need full grounding
   - Fix: Severity-based batching

4. **Embedding Large Lists**
   - Full arrays when counts suffice
   - Fix: Pass counts/summaries, fetch on-demand

5. **Repeated Context**
   - Same data passed multiple times in chain
   - Fix: Extract and pass once at appropriate tier

6. **Verbose Findings**
   - Over-explaining when concise suffices
   - Fix: Follow field length guidelines

## Metrics and Observability

Track these to validate optimization:

| Metric | Description | Target |
|--------|-------------|--------|
| Context Size | Total bytes passed between agents | < 100KB total |
| Redundancy Ratio | Duplicate data / unique data | < 0.1 |
| Grounding Efficiency | Findings processed / grounding operations | > 3:1 |
| Tier Compliance | Agents receiving correct fidelity | 100% |
| Finding Brevity | Avg chars per finding | < 1000 |

## References

- Google ADK: Context compilation pipelines
- Anthropic: Multi-agent coordination patterns
- LangChain: Memory optimization strategies
- CrewAI: Agent communication protocols
