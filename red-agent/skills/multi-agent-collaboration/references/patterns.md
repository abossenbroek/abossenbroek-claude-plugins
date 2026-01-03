# Architectural Patterns Reference

This reference details SOTA architectural patterns for multi-agent systems, with YAML examples and trade-off analysis for each.

## Pattern Selection Framework

| Pattern | Use When | Trade-offs |
|---------|----------|------------|
| Hierarchical | Clear task decomposition, need auditability | Central bottleneck, sequential latency |
| Swarm | Parallel exploration, diverse perspectives | Coordination overhead, emergent unpredictability |
| Graph-Based | Complex dependencies, conditional flows | Design complexity, rigid topology |
| Hybrid | Multiple coordination needs | Implementation complexity |

## Hierarchical Pattern (Coordinator-Worker)

A central coordinator decomposes tasks, delegates to specialized workers, and aggregates results.

### Architecture

```
Coordinator (thin router)
    |
    +-- Phase 1: Analyzer (FULL context)
    |       |
    |       v returns analysis
    |
    +-- Phase 2: Strategist (MINIMAL context)
    |       |
    |       v returns strategy
    |
    +-- Phase 3: Workers (SELECTIVE context, parallel)
    |       |
    |       v return results
    |
    +-- Phase 4: Validators (FILTERED context, batched)
    |       |
    |       v return validations
    |
    +-- Phase 5: Synthesizer (METADATA only)
            |
            v returns final output
```

### YAML Definition

```yaml
hierarchical_workflow:
  coordinator:
    role: thin_router
    responsibilities:
      - route_data_between_agents
      - enforce_context_tiers
      - aggregate_outputs
    not_responsible_for:
      - performing_analysis
      - modifying_outputs
      - synthesizing_results

  phases:
    - name: analysis
      agent: context-analyzer
      context_tier: FULL
      input:
        - complete_snapshot
      output:
        - analysis_summary
        - high_risk_items
        - patterns_detected

    - name: strategy
      agent: attack-strategist
      context_tier: MINIMAL
      depends_on: [analysis]
      input:
        - mode
        - analysis_summary.item_count
        - analysis_summary.high_risk_count
        - analysis_summary.patterns
      output:
        - selected_vectors
        - worker_assignments

    - name: execution
      agents:
        - reasoning-worker
        - context-worker
        - verification-worker
        - scope-worker
      context_tier: SELECTIVE
      depends_on: [strategy]
      parallel: true
      input_per_agent:
        - analysis_summary
        - assigned_vectors_only
        - filtered_items
      output:
        - findings_per_worker

    - name: validation
      agents:
        - evidence-checker
        - proportion-checker
        - alternative-explorer
        - calibrator
      context_tier: FILTERED
      depends_on: [execution]
      batching: by_severity
      input:
        - findings_for_severity_tier
      output:
        - validation_results

    - name: synthesis
      agent: insight-synthesizer
      context_tier: METADATA
      depends_on: [validation]
      input:
        - scope_metadata_only
        - aggregated_findings
        - validation_adjustments
      output:
        - final_report
```

### When to Use

- Enterprise workflows requiring audit trails
- Multi-domain tasks with distinct specialist agents
- Systems where predictability outweighs throughput
- Compliance-sensitive environments

### Trade-offs

| Advantage | Disadvantage |
|-----------|--------------|
| Clear chain of responsibility | Central bottleneck at scale |
| Transparent reasoning chains | Latency increases with depth |
| Easy debugging and observability | Limited parallelism |
| Predictable behavior | Difficult for truly autonomous collaboration |

## Swarm Pattern (Parallel Exploration)

Agents operate in parallel, sharing a common workspace and collectively refining solutions.

### Architecture

```
         Shared Context Pool
              /  |  \
             /   |   \
            v    v    v
    Worker-A  Worker-B  Worker-C
    (creative) (critical) (analytical)
            \   |   /
             \  |  /
              v v v
           Aggregator
```

### YAML Definition

```yaml
swarm_workflow:
  shared_context:
    type: message_pool
    access: read_write
    conflict_resolution: last_write_wins

  workers:
    - agent: creative-explorer
      focus: novel_approaches
      style: divergent
      categories: [innovation, edge-cases]

    - agent: critical-analyzer
      focus: potential_flaws
      style: convergent
      categories: [risks, assumptions]

    - agent: analytical-verifier
      focus: evidence_validation
      style: systematic
      categories: [verification, grounding]

  execution:
    mode: parallel
    coordination: peer_to_peer
    termination:
      condition: consensus_or_timeout
      timeout_ms: 30000
      min_iterations: 1
      max_iterations: 5

  aggregation:
    agent: swarm-aggregator
    strategy: weighted_consensus
    weights:
      evidence_strength: 0.4
      confidence: 0.3
      novelty: 0.2
      feasibility: 0.1
```

### When to Use

- Brainstorming and ideation tasks
- Complex reasoning requiring multiple perspectives
- Exploration of solution space
- Problems without clear decomposition

### Trade-offs

| Advantage | Disadvantage |
|-----------|--------------|
| Diverse perspectives | Communication overhead scales quadratically |
| Parallel exploration | Emergent behavior unpredictability |
| No single point of failure | Convergence not guaranteed |
| Good for open-ended problems | Harder to debug |

## ReAct Pattern (Reasoning + Acting)

Interleave reasoning steps with action execution in tight loops.

### Architecture

```
       +------------------+
       |                  |
       v                  |
    THOUGHT --> ACTION --> OBSERVATION
       ^                        |
       |                        |
       +------------------------+
       (repeat until final answer)
```

### YAML Definition

```yaml
react_workflow:
  loop:
    - step: thought
      description: "Analyze current state, verbalize reasoning"
      output:
        - current_understanding
        - next_action_rationale

    - step: action
      description: "Select and execute tool based on thought"
      input:
        - thought_output
        - available_tools
      output:
        - tool_name
        - tool_input
        - execution_result

    - step: observation
      description: "Incorporate tool result into understanding"
      input:
        - action_output
        - previous_thoughts
      output:
        - updated_understanding
        - is_final: boolean

  termination:
    conditions:
      - is_final == true
      - max_iterations_reached
      - confidence_threshold_met
    max_iterations: 10

  tools:
    - name: search
      description: "Query knowledge sources"
    - name: calculate
      description: "Perform computations"
    - name: verify
      description: "Check claims against sources"
```

### When to Use

- Tasks requiring dynamic adaptation
- Tool-heavy workflows
- Exploratory problem solving
- When next step depends on previous result

### Trade-offs

| Advantage | Disadvantage |
|-----------|--------------|
| Highly adaptive | Myopic decision-making |
| Natural tool integration | May meander without global plan |
| Transparent reasoning | Higher latency per decision |
| Good for unknown problem structure | Less efficient for known workflows |

## Plan-and-Execute Pattern

Separate planning phase from execution phase.

### Architecture

```
    PLANNING PHASE              EXECUTION PHASE

    Analyze Task               Execute Subtask 1
         |                           |
         v                           v
    Decompose into             Execute Subtask 2
    Subtasks                         |
         |                           v
         v                     Execute Subtask N
    Create Plan with                 |
    Dependencies                     v
         |                     Process Results
         v                           |
    Validate Plan                    v
         |                     Adjust if Needed
         v
    [Ready to Execute] ---------> [Begin Execution]
```

### YAML Definition

```yaml
plan_execute_workflow:
  planning_phase:
    steps:
      - name: analyze_task
        input: [user_request, context]
        output: [task_objectives, constraints]

      - name: decompose
        input: [task_objectives]
        output:
          subtasks:
            - id: ST-1
              description: "..."
              dependencies: []
            - id: ST-2
              description: "..."
              dependencies: [ST-1]

      - name: create_plan
        input: [subtasks, constraints]
        output:
          execution_order: [ST-1, ST-2]
          parallel_groups: [[ST-3, ST-4]]
          checkpoints: [after_ST-2]

      - name: validate_plan
        input: [plan, constraints]
        output: [is_valid, issues]

  execution_phase:
    for_each_subtask:
      - execute_subtask
      - check_result
      - update_state

    on_failure:
      strategy: replan_from_checkpoint
      max_replans: 2

  checkpoints:
    save_state: true
    allow_human_review: true
```

### When to Use

- Tasks with clear logical sequence
- Workflows requiring predictability
- Multi-step processes with dependencies
- When efficiency matters (fewer LLM reasoning calls)

### Trade-offs

| Advantage | Disadvantage |
|-----------|--------------|
| Structured execution | Less adaptive to surprises |
| Predictable behavior | Planning complexity for hard tasks |
| Efficient (plan once) | Requires replanning on failure |
| Easy progress tracking | May miss opportunities for shortcuts |

## Reflection Pattern (Self-Correction)

Generate -> Critique -> Improve loop for iterative refinement.

### Architecture

```
    GENERATE              CRITIQUE              IMPROVE
    (Actor)              (Evaluator)          (Self-Reflect)
       |                     |                     |
       v                     v                     v
    Output V1  ------>  Score/Feedback ------>  Output V2
                                                   |
       ^                                           |
       |                                           |
       +---------------- (if not good enough) ----+
```

### YAML Definition

```yaml
reflection_workflow:
  components:
    actor:
      role: generate_output
      input: [task, context, previous_feedback]
      output: [attempt, confidence]

    evaluator:
      role: score_output
      input: [attempt, criteria]
      output:
        score: 0.0-1.0
        feedback:
          - issue: "..."
            severity: high|medium|low
            suggestion: "..."
      strategies:
        - llm_as_judge
        - rule_based_heuristics
        - retrieval_verification

    self_reflection:
      role: generate_verbal_feedback
      input: [attempt, evaluation, history]
      output:
        - identified_issues
        - root_cause_analysis
        - improvement_plan
      memory:
        type: episodic
        window: 3  # Last 3 attempts

  loop:
    max_iterations: 5
    termination:
      conditions:
        - score >= 0.85
        - no_improvement_after: 2

    state:
      maintain_history: true
      track_improvements: true

  batching:
    # For multi-output reflection
    by_severity:
      CRITICAL: all_evaluators
      HIGH: [evidence_checker, proportion_checker]
      MEDIUM: [evidence_checker]
      LOW: skip
```

### When to Use

- Tasks requiring high quality output
- Code generation with testing
- Content creation with style guidelines
- Multi-step reasoning with verification

### Trade-offs

| Advantage | Disadvantage |
|-----------|--------------|
| Improved output quality | Reflection may be superficial |
| Self-correction without human | Risk of reinforcing bad patterns |
| Catches errors before delivery | Increased latency and cost |
| Good for complex reasoning | Distinguishing true insight from heuristic |

## Hybrid Pattern (Multi-Mode Coordination)

Combine multiple patterns based on task phase or characteristics.

### Architecture

```
    [Task Input]
         |
         v
    +--------------------+
    | PATTERN SELECTOR   |
    | (based on task)    |
    +--------------------+
         |
    +----+----+----+
    |    |    |    |
    v    v    v    v
  Hier Swarm ReAct Plan
    |    |    |    |
    +----+----+----+
         |
         v
    [Aggregated Output]
```

### YAML Definition

```yaml
hybrid_workflow:
  pattern_selector:
    criteria:
      - task_type
      - complexity_estimate
      - parallelization_potential
      - precision_requirements

    routing:
      - condition: "task.type == 'exploration'"
        pattern: swarm

      - condition: "task.type == 'sequential_analysis'"
        pattern: hierarchical

      - condition: "task.requires_tool_use"
        pattern: react

      - condition: "task.has_clear_steps"
        pattern: plan_execute

  phases:
    # Example: Hierarchical for analysis, Swarm for exploration,
    # Reflection for validation

    - phase: initial_analysis
      pattern: hierarchical
      agents: [context-analyzer]
      context_tier: FULL

    - phase: exploration
      pattern: swarm
      agents: [explorer-1, explorer-2, explorer-3]
      context_tier: SELECTIVE
      parallel: true

    - phase: validation
      pattern: reflection
      agents: [validator, calibrator]
      context_tier: FILTERED
      iterations: 3

    - phase: synthesis
      pattern: hierarchical
      agents: [synthesizer]
      context_tier: METADATA

  transitions:
    - from: initial_analysis
      to: exploration
      condition: "analysis.complexity > threshold"

    - from: exploration
      to: validation
      condition: "always"

    - from: validation
      to: exploration
      condition: "validation.score < 0.7"
      max_loops: 2
```

### When to Use

- Complex workflows with varied sub-tasks
- Systems requiring both exploration and precision
- Adaptive systems that learn optimal patterns
- Enterprise systems with multiple use cases

### Trade-offs

| Advantage | Disadvantage |
|-----------|--------------|
| Best pattern for each phase | Implementation complexity |
| Highly flexible | Harder to debug |
| Optimal resource utilization | More configuration needed |
| Adaptable to task changes | Pattern transition overhead |

## Agent Handoff Protocols

### Agent-as-Tool Mode

Treat sub-agent as a function call - focused prompt, receive result, continue.

```yaml
agent_as_tool:
  invocation:
    type: function_call
    context_inheritance: none

  caller_provides:
    - specific_task_prompt
    - minimal_required_data

  callee_receives:
    - task_prompt
    - data_payload
    # NO conversation history
    # NO caller context

  callee_returns:
    - structured_result

  advantages:
    - token_efficient
    - clear_boundaries
    - predictable_behavior

  use_when:
    - specialized_single_task
    - need_context_isolation
    - optimizing_for_cost
```

### Agent Transfer Mode

Full control handoff where sub-agent inherits session view.

```yaml
agent_transfer:
  invocation:
    type: hierarchy_transfer
    context_inheritance: partial_or_full

  caller_provides:
    - control_token
    - session_state
    - task_context

  callee_receives:
    - session_view  # Configurable via include_contents
    - prior_messages_reframed  # "[For context]: Agent B said..."
    - task_authority

  callee_can:
    - call_own_tools
    - spawn_sub_agents
    - transfer_further
    - drive_workflow

  use_when:
    - complex_multi_step_tasks
    - need_full_context_access
    - dynamic_workflow_routing
```

### Standard Handoff Schema

```yaml
handoff:
  metadata:
    from_agent: context-analyzer
    to_agent: attack-strategist
    timestamp: "2024-01-15T10:30:00Z"
    handoff_id: "HO-001"

  context_level: MINIMAL  # FULL|SELECTIVE|FILTERED|MINIMAL|METADATA

  payload:
    mode: deep
    analysis_summary:
      item_count: 15
      high_risk_count: 4
      patterns: [pattern_1, pattern_2]

  instructions:
    task: "Select attack vectors based on analysis"
    constraints:
      - "Max 6 vectors for standard mode"
      - "Prioritize high-risk patterns"

  expected_output:
    format: yaml
    schema: attack_strategy_v1

  error_handling:
    on_failure: retry_with_context
    max_retries: 2
```

## Guardrails and Validation

### Layered Defense Architecture

```yaml
guardrails:
  input_layer:
    - pii_detection:
        type: regex
        patterns: [ssn, credit_card, email]
        action: redact_or_block

    - safety_classifier:
        type: ml_model
        detects: [jailbreak, prompt_injection]
        threshold: 0.85

    - relevance_checker:
        type: llm_classifier
        ensures: query_within_scope

  prompt_construction_layer:
    - prefix_prompts:
        content: "Detect and refuse attack patterns..."

    - domain_boundaries:
        role_reminder: true
        scope_constraints: true

    - rbac_injection:
        bind: [user_id, roles, permissions]

  output_layer:
    - content_policy:
        check: [brand_guidelines, safety_policies]

    - keyword_filter:
        blocklist: [...]
        action: redact

    - human_in_loop:
        trigger_on: high_stakes_decisions
```

### Output Validation Pattern

```yaml
validation:
  post_tool_use:
    hook: validate_output
    schema: pydantic_model

  on_invalid:
    action: block_and_retry
    inject_error_context: true
    max_retries: 2

  on_valid:
    action: continue
    log: true
```

## References

- Google ADK: Multi-agent patterns and context compilation
- Anthropic: Agent coordination and handoff protocols
- LangGraph: Graph-based workflow orchestration
- CrewAI: Role-based agent teams
- AutoGen: Conversation-driven agent interactions
- AWS Strands: Multi-agent collaboration patterns
