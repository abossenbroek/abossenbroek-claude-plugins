# Red-Agent Implementation Examples

This reference shows how the red-agent plugin implements SOTA multi-agent collaboration patterns. Use these as concrete examples when designing similar systems.

## Overview: Red-Agent Architecture

The red-agent plugin implements a **hierarchical pattern with firewall isolation**:

```
Main Session (user-facing)
    |
    v
red-team-coordinator (FIREWALL - only entry point)
    |
    +-- Phase 1: context-analyzer (FULL context)
    |
    +-- Phase 2: attack-strategist (MINIMAL context)
    |
    +-- Phase 3: attackers (SELECTIVE context, parallel)
    |       +-- reasoning-attacker
    |       +-- context-attacker
    |       +-- hallucination-prober
    |       +-- scope-analyzer
    |
    +-- Phase 4: grounding agents (FILTERED context, batched)
    |       +-- evidence-checker
    |       +-- proportion-checker
    |       +-- alternative-explorer
    |       +-- calibrator
    |
    +-- Phase 5: insight-synthesizer (METADATA only)
            |
            v
        Final Report (sanitized, returns to main session)
```

## Example 1: Hierarchical Coordinator as Thin Router

The `red-team-coordinator` demonstrates the **thin router pattern** - it orchestrates but does not analyze.

### What Coordinator Does

```yaml
coordinator_responsibilities:
  does:
    - route_data_between_sub_agents
    - enforce_context_tiers
    - aggregate_outputs
    - track_phase_completion

  does_not:
    - perform_analysis
    - modify_findings
    - synthesize_results  # That's insight-synthesizer's job
    - interact_with_users
```

### Phase Execution with Context Tiers

```yaml
phase_1_analysis:
  agent: context-analyzer
  context_tier: FULL
  rationale: "Only agent that needs complete picture to establish baseline"

  receives:
    snapshot:
      mode: deep
      target: conversation
      conversational_arc: [...]     # Full history
      claims: [...]                 # All extracted claims
      files_read: [...]             # All files
      tools_invoked: [...]          # All tool calls
      high_risk_claims: [...]       # Pre-filtered claims

  returns:
    analysis_summary:
      claim_count: 15
      high_risk_count: 4
      patterns_detected: [inductive_leap, authority_appeal]
      risk_surface:
        reasoning-flaws: HIGH
        assumption-gaps: HIGH
        context-manipulation: MEDIUM
        authority-exploitation: LOW
        # ... all 10 categories

phase_2_strategy:
  agent: attack-strategist
  context_tier: MINIMAL
  rationale: "Routing decision only - doesn't analyze content directly"

  receives:
    mode: deep
    analysis_summary:
      claim_count: 15
      high_risk_count: 4
      patterns: [inductive_leap, authority_appeal]
      top_risks:
        - category: reasoning-flaws
          level: HIGH
        - category: assumption-gaps
          level: HIGH

  # NOT received:
  # - full_snapshot
  # - individual_claims
  # - conversational_arc

  returns:
    attack_vectors:
      - category: reasoning-flaws
        style: socratic-questioning
        targets: [C1, C3, C7]
      - category: assumption-gaps
        style: assumption-inversion
        targets: [C2, C5]
      # ... up to 10 vectors in deep mode
```

## Example 2: Parallel Swarm Execution (Attackers)

Phase 3 demonstrates the **swarm pattern** with parallel execution and selective context.

### Parallel Launch

```yaml
phase_3_attack_execution:
  pattern: parallel_swarm
  agents:
    - reasoning-attacker:
        categories: [reasoning-flaws, assumption-gaps]
    - context-attacker:
        categories: [context-manipulation, authority-exploitation, temporal-inconsistency]
    - hallucination-prober:
        categories: [hallucination-risks, over-confidence, information-leakage]
    - scope-analyzer:
        categories: [scope-creep, dependency-blindness]

  execution:
    mode: parallel  # All 4 attackers run simultaneously
    context_tier: SELECTIVE
    isolation: true  # Each attacker only sees own domain

  context_per_attacker:
    receives:
      - context_analysis        # From Phase 1
      - own_attack_vectors      # Only for THIS attacker
      - filtered_claims         # Only claims relevant to own categories
      - mode
      - target

    not_received:
      - full_snapshot
      - files_read_list
      - tools_invoked_list
      - conversational_arc
      - other_attackers_vectors
      - claims_for_other_categories
```

### Per-Attacker Context Example

```yaml
# Context for reasoning-attacker (not other attackers)
reasoning_attacker_input:
  context_analysis:
    summary: "Conversation involves authentication recommendation..."
    risk_surface:
      reasoning-flaws: HIGH
      assumption-gaps: HIGH

  attack_vectors:
    - category: reasoning-flaws
      style: socratic-questioning
      targets: [C1, C3, C7]
    - category: assumption-gaps
      style: assumption-inversion
      targets: [C2, C5]

  claims:
    high_risk:
      - id: C1
        text: "JWT is more secure than OAuth for this use case"
        risk_score: 0.85
      - id: C3
        text: "The implementation will handle edge cases"
        risk_score: 0.72
    count: 15

  mode: deep
  target: conversation

# NOTE: reasoning-attacker does NOT receive:
# - context-attacker's vectors
# - hallucination-prober's filtered claims
# - scope-analyzer's targets
```

### Attacker Output Format

```yaml
attack_results:
  attack_type: reasoning-attacker
  categories_probed:
    - reasoning-flaws
    - assumption-gaps

  findings:
    - id: RF-001
      category: reasoning-flaws
      severity: CRITICAL
      title: "Invalid inference in JWT recommendation"

      target:
        claim_id: C1
        claim_text: "JWT is more secure than OAuth"
        message_num: 7

      evidence:
        type: logical_gap
        description: "Conclusion doesn't follow - JWT vs OAuth security depends on use case"
        quote: "JWT is more secure than OAuth for this use case"

      attack_applied:
        style: socratic-questioning
        probe: "What specific security properties make JWT superior here?"

      impact:
        if_exploited: "User may implement insecure auth based on flawed reasoning"
        affected_claims: [C1, C8]

      recommendation: "Compare specific security guarantees of each approach for this context"
      confidence: 0.85

  summary:
    total_findings: 8
    by_severity:
      critical: 1
      high: 3
      medium: 4
```

## Example 3: Severity-Based Batching (Grounding)

Phase 4 demonstrates **severity-based batching** to reduce grounding operations by 60-70%.

### Batching Rules

```yaml
grounding_batches:
  deep_mode:
    CRITICAL:
      agents: [evidence-checker, proportion-checker, alternative-explorer, calibrator]
      findings: [RF-001]  # 1 finding x 4 agents = 4 operations

    HIGH:
      agents: [evidence-checker, proportion-checker]
      findings: [RF-002, RF-003, RF-004]  # 3 findings x 2 agents = 6 operations

    MEDIUM:
      agents: [evidence-checker]
      findings: [RF-005, RF-006, RF-007, RF-008]  # 4 findings x 1 agent = 4 operations

    LOW_INFO:
      agents: []  # Skip grounding
      findings: [RF-009, RF-010]  # 0 operations

  # Total: 14 operations instead of 40 (8 findings x 5 potential agents)
  # Reduction: 65%

  standard_mode:
    CRITICAL_HIGH:
      agents: [evidence-checker, proportion-checker]
    MEDIUM:
      agents: [evidence-checker]
    LOW_INFO:
      agents: []

  quick_mode:
    all:
      agents: []  # Skip all grounding
```

### Grounding Agent Input (FILTERED)

```yaml
evidence_checker_input:
  # Only receives findings assigned to this agent
  findings_to_ground:
    - id: RF-001
      severity: CRITICAL
      title: "Invalid inference in JWT recommendation"
      evidence:
        quote: "JWT is more secure than OAuth for this use case"
        description: "Conclusion doesn't follow..."
      confidence: 0.85

    - id: RF-002
      severity: HIGH
      # ...

  mode: deep
  claim_context:
    # Minimal context to verify evidence
    relevant_claims: [C1, C3]

  # NOT received:
  # - Full snapshot
  # - LOW/INFO findings
  # - Other attackers' outputs
```

### Grounding Output Format

```yaml
grounding_results:
  agent: evidence-checker
  assessments:
    - finding_id: RF-001
      evidence_strength: 0.82
      verified: true
      notes: "Quote accurately represents conversation. Evidence directly supports finding."

    - finding_id: RF-002
      evidence_strength: 0.65
      verified: partial
      notes: "Quote taken slightly out of context. Surrounding messages provide nuance."
      suggested_adjustment: -0.1
```

## Example 4: Metadata-Only Synthesis

Phase 5 demonstrates the **METADATA tier** - synthesizer only needs counts and processed findings.

### Synthesizer Input

```yaml
insight_synthesizer_input:
  mode: deep

  scope_metadata:
    message_count: 45
    files_analyzed: 8
    claims_analyzed: 15
    categories_covered: 10
    grounding_enabled: true
    grounding_agents_used: 4

  # Aggregated findings (not raw)
  findings:
    - id: RF-001
      severity: CRITICAL
      title: "Invalid inference in JWT recommendation"
      original_confidence: 0.85
      adjusted_confidence: 0.78
      grounding_notes: "Evidence strong but alternative interpretation exists"

    - id: RF-002
      severity: HIGH
      # ...

  grounding_summary:
    total_processed: 8
    confidence_adjustments: 5
    downgrades: 2
    upgrades: 1

  # NOT received:
  # - full_snapshot
  # - raw_claims
  # - conversational_arc
  # - individual_grounding_outputs
```

### Why This Works

```yaml
synthesizer_needs:
  for_methodology_section:
    - mode              # "deep analysis"
    - categories_covered  # "all 10 categories"
    - grounding_agents_used  # "4 grounding agents"

  for_limitations_section:
    - message_count     # "Based on 45 messages"
    - files_analyzed    # "across 8 files"
    - grounding_enabled # "with grounding"

  for_findings_section:
    - aggregated_findings  # Already processed with confidence adjustments

synthesizer_does_not_need:
  - raw_conversation    # Already extracted into findings
  - individual_claims   # Already synthesized
  - grounding_details   # Only need adjustments
```

## Example 5: Fix Coordinator Chain

The `fix-coordinator` demonstrates **chained workflow** with minimal context per fix-planner.

### Workflow

```yaml
fix_coordinator_workflow:
  phase_a:
    action: run_red_team_analysis
    agent: red-team-coordinator
    output: findings_with_severity

  phase_b:
    action: filter_findings
    criteria: severity >= HIGH
    output: fixable_findings

  phase_c:
    action: spawn_fix_planners
    pattern: parallel
    context: MINIMAL_PER_FINDING

    for_each_finding:
      receives:
        - single_finding        # Just this one
        - affected_files        # Only relevant files
        - relevant_patterns     # Only matching patterns

      not_received:
        - full_snapshot
        - other_findings
        - all_files
        - all_patterns

  phase_d:
    action: aggregate_fix_options
    output: structured_menu_data
```

### Fix Planner Input Example

```yaml
fix_planner_input:
  finding:
    id: RF-001
    title: "Invalid inference in JWT recommendation"
    severity: CRITICAL
    category: reasoning-flaws
    evidence:
      quote: "JWT is more secure than OAuth for this use case"
      description: "Conclusion doesn't follow..."
    impact:
      if_exploited: "User may implement insecure auth"
    recommendation: "Compare specific security guarantees"

  affected_context:
    files: ["auth.py", "config.py"]  # Only relevant files
    pattern: "authentication"
    related_claims: [C1, C8]

  mode: deep

  # NOT received:
  # - full_snapshot (would be 20KB)
  # - other_findings (8+ findings)
  # - all_files_read (potentially 50+ files)
```

## Context Reduction Metrics

### Red-Agent Actual Measurements

```yaml
context_reduction:
  verbose_approach:
    phase_1: 20KB  # Full snapshot to analyzer
    phase_2: 25KB  # Full snapshot + analysis
    phase_3: 100KB # 4 attackers x 25KB each
    phase_4: 120KB # 4 grounding x 30KB each
    phase_5: 50KB  # Full outputs to synthesizer
    total: 315KB

  optimized_approach:
    phase_1: 20KB  # Full snapshot to analyzer (required)
    phase_2: 1KB   # MINIMAL context to strategist
    phase_3: 12KB  # 4 attackers x 3KB SELECTIVE each
    phase_4: 15KB  # Batched grounding
    phase_5: 2KB   # METADATA to synthesizer
    total: 50KB

  reduction: 84%

  operations:
    verbose_grounding: 40  # 8 findings x 5 agents
    optimized_grounding: 14  # Severity batching
    reduction: 65%
```

## Anti-Patterns Avoided in Red-Agent

### 1. Snapshot Broadcasting

```yaml
# AVOIDED: Passing full snapshot everywhere
bad_pattern:
  every_agent_receives: full_snapshot

# IMPLEMENTED: Tiered fidelity
good_pattern:
  context-analyzer: FULL
  attack-strategist: MINIMAL
  attackers: SELECTIVE
  grounding: FILTERED
  synthesizer: METADATA
```

### 2. Grounding Everything

```yaml
# AVOIDED: All findings to all grounding agents
bad_pattern:
  all_findings -> all_grounding_agents

# IMPLEMENTED: Severity batching
good_pattern:
  CRITICAL -> 4 agents
  HIGH -> 2 agents
  MEDIUM -> 1 agent
  LOW/INFO -> 0 agents
```

### 3. Verbose Findings

```yaml
# AVOIDED: Long-winded descriptions
bad_pattern:
  evidence:
    quote: "The user mentioned in message 5 that they wanted to
      implement authentication, and then in message 7 they discussed
      various options including OAuth and JWT, and the assistant
      recommended JWT without fully exploring the security implications
      of each approach or considering the specific requirements..."

# IMPLEMENTED: Concise findings
good_pattern:
  evidence:
    quote: "recommended JWT without fully exploring security implications"
    description: "Auth recommendation without discussing requirements"
```

## Key Takeaways

1. **Coordinator = Thin Router**: Route data, don't analyze
2. **Context Tiers**: FULL -> MINIMAL -> SELECTIVE -> FILTERED -> METADATA
3. **Parallel Where Possible**: Attackers run simultaneously
4. **Batch by Criteria**: Severity-based grounding reduces operations 60-70%
5. **Document What's NOT Passed**: Critical for maintaining discipline
6. **Concise Findings**: Field length limits enforced
7. **84% Context Reduction**: Achieved without sacrificing analysis quality
