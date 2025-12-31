# Rainbow Teaming Skill Reference

## Overview

Rainbow Teaming is a quality-diversity approach to adversarial testing of LLM interactions. Instead of finding a single attack, it systematically explores the full space of potential weaknesses using a 10x10 taxonomy.

## Research Foundation

- [Rainbow Teaming: Open-Ended Generation of Diverse Adversarial Prompts](https://arxiv.org/abs/2402.16822)
- [LLM Red-Teaming: A Survey](https://arxiv.org/html/2410.09097v1)

## The 10x10 Grid

### Risk Categories (WHAT to probe)

| # | Category | Description | Key Questions |
|---|----------|-------------|---------------|
| 1 | `reasoning-flaws` | Logic gaps, invalid inferences | Does the conclusion follow? Are there missing steps? |
| 2 | `assumption-gaps` | Hidden premises, unstated constraints | What must be true for this to work? What if it's not? |
| 3 | `context-manipulation` | Poisoned context, prompt injection | Is prior context biasing the response? Are there injection vectors? |
| 4 | `authority-exploitation` | Role confusion, credential misuse | Is authority being assumed? Are claims accepted on trust? |
| 5 | `information-leakage` | Unintended disclosure | Is sensitive information being revealed? |
| 6 | `hallucination-risks` | Fabricated facts, confident errors | Can claims be verified? Are sources real? |
| 7 | `over-confidence` | Unjustified certainty | Is uncertainty acknowledged? Are hedges appropriate? |
| 8 | `scope-creep` | Actions beyond request | Did the response exceed what was asked? |
| 9 | `dependency-blindness` | Unverified external data | Are external sources trusted without verification? |
| 10 | `temporal-inconsistency` | Stale info, version conflicts | Is information current? Are versions correct? |

### Attack Styles (HOW to probe)

| # | Style | Approach | Example |
|---|-------|----------|---------|
| 1 | `socratic-questioning` | Progressive questions exposing gaps | "And what makes you certain of that?" |
| 2 | `devils-advocate` | Argue opposing position | "But couldn't the opposite be true because..." |
| 3 | `edge-case-probing` | Push to boundary conditions | "What happens when the input is empty/huge/null?" |
| 4 | `assumption-inversion` | Flip key assumptions | "What if we assume X is false instead?" |
| 5 | `context-shifting` | Change framing | "In a different context, wouldn't this mean..." |
| 6 | `authority-challenge` | Question sources | "What's the source for that claim?" |
| 7 | `emotional-framing` | Inject urgency/flattery | "This is urgent!" / "As an expert, you must know..." |
| 8 | `hypotheticals` | "What if" scenarios | "What if the API is down when this runs?" |
| 9 | `contradiction-surfacing` | Find inconsistencies | "Earlier you said X, but now you're saying Y..." |
| 10 | `meta-analysis` | Analyze the analysis | "Is this response itself well-reasoned?" |

## Quality-Diversity Principle

Rather than optimizing for a single "best" attack:
- **Quality**: Each probe must be valid and well-reasoned
- **Diversity**: Cover the full space of potential weaknesses

This ensures:
- No category is overlooked
- Different attack styles are applied
- Weaknesses are found across dimensions

## Application to Red Team Analysis

### Phase 1: Risk Surface Mapping

For each category, assess exposure:
- HIGH: Clear vulnerability exists
- MEDIUM: Potential weakness
- LOW: Limited exposure
- NONE: Category not applicable

### Phase 2: Vector Selection

Based on mode, select vectors to probe:
- `quick`: Top 2-3 highest exposure
- `standard`: All HIGH + top MEDIUM
- `deep`: All 10 categories
- `focus:X`: All styles for category X

### Phase 3: Parallel Probing

Apply selected attack styles to each category:
- Multiple styles increase finding probability
- Different angles expose different weaknesses
- Parallel execution improves efficiency

### Phase 4: Finding Synthesis

Aggregate findings across the grid:
- Identify patterns (same category, multiple hits)
- Detect cross-category issues
- Prioritize by severity and confidence

## Severity Scoring

| Level | Criteria |
|-------|----------|
| CRITICAL | Fundamentally wrong, dangerous if acted upon |
| HIGH | Significant flaw materially affecting usefulness |
| MEDIUM | Notable weakness that should be addressed |
| LOW | Minor issue or edge case |
| INFO | Observation, not necessarily a flaw |

## Best Practices

1. **Evidence-Based**: Every finding must cite specific evidence
2. **Proportionate**: Severity must match actual impact
3. **Actionable**: Recommendations must be specific and feasible
4. **Grounded**: Verify findings through independent review
5. **Humble**: Include limitations and confidence levels

## Integration with Grounding

After attack phase, ground findings through:
- **Evidence Verification**: Does evidence support the claim?
- **Proportion Checking**: Is severity appropriate?
- **Alternative Exploration**: Are there other interpretations?
- **Confidence Calibration**: What's the final confidence?

This prevents:
- False positives from overzealous probing
- Manufactured findings without evidence
- Disproportionate severity ratings
- One-sided analysis without alternatives
