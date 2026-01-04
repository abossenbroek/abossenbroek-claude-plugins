# Red Agent Attack Taxonomy

Complete guide to the 10x10 attack taxonomy used by red-agent for adversarial analysis.

## Overview

Red-agent uses a **Rainbow Teaming** approach with 10 risk categories × 10 attack styles = 100 unique attack vectors.

### 10 Risk Categories

1. **reasoning-flaws** - Logical errors, fallacies, circular reasoning
2. **assumption-gaps** - Hidden assumptions, unstated constraints
3. **context-manipulation** - Missing context, selective information
4. **authority-exploitation** - Unverified claims, false expertise
5. **information-leakage** - Sensitive data exposure
6. **hallucination-risks** - Potential for fabricated information
7. **over-confidence** - Certainty without evidence
8. **scope-creep** - Task expansion, mission drift
9. **dependency-blindness** - Missing dependencies
10. **temporal-inconsistency** - Time-based assumptions
11. **code-duplication** - Duplicate code (PR analysis only)

### 10 Attack Styles

1. **adversarial-prompting** - Probe with edge-case inputs
2. **constraint-testing** - Test boundary conditions
3. **context-switching** - Rapid context changes
4. **counterfactual-probing** - "What if" scenarios
5. **edge-case-exploration** - Extreme/unusual cases
6. **red-herring-injection** - Distracting information
7. **role-reversal** - Flip perspectives
8. **semantic-twist** - Subtle meaning changes
9. **temporal-manipulation** - Time-based attacks
10. **tone-shifting** - Change communication tone

## Risk Categories Detailed

### 1. Reasoning Flaws

**What it detects:**
- Circular reasoning (using conclusion as premise)
- Logical fallacies (ad hominem, straw man, false dichotomy)
- Invalid inference chains
- Contradictory statements

**Examples:**

**Finding:** Circular Reasoning
```yaml
title: "Validation logic assumes its own correctness"
evidence:
  description: "Function validate_input calls is_valid which checks validate_input"
  type: circular_reasoning
recommendation: "Break circular dependency - extract validation rules to separate function"
```

**Finding:** False Dichotomy
```yaml
title: "Code assumes only two states when more exist"
evidence:
  description: "if authenticated: allow() else: deny() ignores pending/expired states"
  type: false_dichotomy
recommendation: "Add explicit handling for pending and expired authentication states"
```

### 2. Assumption Gaps

**What it detects:**
- Hidden assumptions not stated explicitly
- Implicit environmental dependencies
- Unstated preconditions
- Assumed invariants

**Examples:**

**Finding:** Hidden Database Assumption
```yaml
title: "Function assumes database is always connected"
evidence:
  description: "query() called without connection check or error handling"
  type: hidden_assumption
recommendation: "Add connection validation and retry logic"
```

**Finding:** Input Format Assumption
```yaml
title: "Parser assumes JSON is always valid"
evidence:
  description: "json.loads() called without try/except for malformed input"
  type: unstated_constraint
recommendation: "Add JSON validation with clear error messages for invalid format"
```

### 3. Context Manipulation

**What it detects:**
- Missing critical context
- Selective information presentation
- Scope narrowing
- Important details omitted

**Examples:**

**Finding:** Missing Deprecation Context
```yaml
title: "Uses deprecated API without acknowledging deprecation"
evidence:
  description: "Calls oldApi.method() which was deprecated in v2.0"
  type: missing_context
recommendation: "Switch to newApi.method() or document why old API is still used"
```

### 4. Authority Exploitation

**What it detects:**
- Claims without evidence
- Unverified expertise
- False consensus
- Misattributed authority

**Examples:**

**Finding:** Unverified Security Claim
```yaml
title: "Claims encryption is secure without specifying algorithm"
evidence:
  description: "Comment says 'securely encrypted' but uses weak MD5 hashing"
  type: false_authority
recommendation: "Use industry-standard AES-256 encryption and document algorithm choice"
```

### 5. Information Leakage

**What it detects:**
- Sensitive data in logs
- Stack traces in production
- PII exposure
- Debug information leakage

**Examples:**

**Finding:** Password in Logs
```yaml
title: "Logs contain plaintext passwords"
evidence:
  description: "logger.info(f'Login attempt: {username}:{password}')"
  type: secret_in_log
severity: CRITICAL
recommendation: "Remove password from log statements - log username only"
```

**Finding:** Stack Trace Exposure
```yaml
title: "Error handler returns full stack trace to client"
evidence:
  description: "except Exception as e: return jsonify({'error': str(e), 'trace': traceback.format_exc()})"
  type: information_disclosure
severity: HIGH
recommendation: "Return generic error message to client, log full trace server-side"
```

### 6. Hallucination Risks

**What it detects:**
- Potential for fabricating data
- Invented APIs or functions
- Made-up configuration options
- Fictional documentation references

**Examples:**

**Finding:** Non-existent API
```yaml
title: "References API endpoint that doesn't exist"
evidence:
  description: "Documentation mentions /api/v3/users but only v2 exists"
  type: fabricated_api
recommendation: "Verify API version - update to /api/v2/users or wait for v3 release"
```

### 7. Over-Confidence

**What it detects:**
- Certainty without testing
- Guarantees without validation
- "Always works" claims
- Missing error handling

**Examples:**

**Finding:** Untested Guarantee
```yaml
title: "Claims 100% accuracy without test coverage"
evidence:
  description: "Comment says 'guaranteed to work' but has 0% test coverage"
  type: unjustified_certainty
recommendation: "Add comprehensive tests or remove absolute guarantee claim"
```

**Finding:** No Error Handling
```yaml
title: "Network call assumes success"
evidence:
  description: "response = requests.get(url); data = response.json() - no status check"
  type: overconfident_assumption
recommendation: "Add response.raise_for_status() and handle connection errors"
```

### 8. Scope Creep

**What it detects:**
- Task expansion beyond requirements
- Feature additions not requested
- Mission drift
- Unintended functionality

**Examples:**

**Finding:** Feature Creep
```yaml
title: "PR adds features beyond stated requirements"
evidence:
  description: "PR for 'fix login bug' also adds password reset and 2FA"
  type: scope_expansion
recommendation: "Split additional features into separate PRs"
```

### 9. Dependency Blindness

**What it detects:**
- Missing external dependencies
- Unhandled service failures
- Environmental assumptions
- Missing imports

**Examples:**

**Finding:** Missing Service Dependency
```yaml
title: "Calls external API without availability check"
evidence:
  description: "Assumes payment gateway is always reachable"
  type: environmental_dependency
recommendation: "Add circuit breaker pattern and fallback for service unavailability"
```

**Finding:** Database Dependency
```yaml
title: "No handling for database unavailability"
evidence:
  description: "Application crashes if Redis is down"
  type: dependency_blindness
recommendation: "Add Redis connection retry and fallback to in-memory cache"
```

### 10. Temporal Inconsistency

**What it detects:**
- Race conditions
- Time-zone issues
- Temporal coupling
- Timing assumptions

**Examples:**

**Finding:** Race Condition
```yaml
title: "Race condition in concurrent file access"
evidence:
  description: "check-then-act pattern: if file_exists(path): read(path) - race between check and read"
  type: race_condition
severity: HIGH
recommendation: "Use atomic file operations or file locking mechanism"
```

**Finding:** Timezone Issue
```yaml
title: "Datetime comparison ignores timezones"
evidence:
  description: "Compares naive datetime objects from different sources"
  type: temporal_inconsistency
recommendation: "Use timezone-aware datetime objects (UTC) throughout application"
```

### 11. Code Duplication (PR Analysis Only)

**What it detects:**
- Exact code duplication
- Structural duplication
- Logic duplication
- DRY violations

**Examples:**

**Finding:** Duplicate Validation
```yaml
title: "Duplicate validation logic in auth modules"
evidence:
  description: "Same password validation function in login.py and signup.py"
  type: exact_duplication
  lines_duplicated: 15
  percentage: 12.5
severity: HIGH
recommendation: "Extract validate_password() to src/auth/validators.py"
```

## Attack Styles Detailed

### 1. Adversarial Prompting

**Technique:** Probe with edge-case inputs that might break assumptions

**Applied to reasoning-flaws:**
- Test logic with contradictory inputs
- Provide circular references
- Supply self-referential data

### 2. Constraint Testing

**Technique:** Test boundary conditions and limits

**Applied to assumption-gaps:**
- Zero values, negative numbers
- Empty collections, null values
- Maximum size inputs

### 3. Context Switching

**Technique:** Rapidly change context to reveal missing information

**Applied to context-manipulation:**
- Switch between related but different scenarios
- Change environmental assumptions mid-conversation

### 4. Counterfactual Probing

**Technique:** "What if" scenarios to test assumptions

**Applied to dependency-blindness:**
- "What if database is unavailable?"
- "What if API returns 500 error?"
- "What if network is slow?"

### 5. Edge-Case Exploration

**Technique:** Explore extreme and unusual cases

**Applied to edge-case-handling (PR analysis):
- Maximum/minimum values
- Boundary conditions
- Rare but possible scenarios

### 6. Red-Herring Injection

**Technique:** Introduce distracting information

**Applied to information-leakage:**
- Test if sensitive data is logged
- Check error messages for leaks
- Probe for verbose debugging

### 7. Role Reversal

**Technique:** Flip perspectives

**Applied to authority-exploitation:**
- Question claimed expertise
- Verify authoritative statements
- Challenge consensus claims

### 8. Semantic Twist

**Technique:** Subtle meaning changes

**Applied to hallucination-risks:**
- Check for invented APIs
- Verify documentation references
- Validate claimed features

### 9. Temporal Manipulation

**Technique:** Time-based attacks

**Applied to temporal-inconsistency:**
- Change system time
- Test concurrent access
- Probe time-zone handling

### 10. Tone Shifting

**Technique:** Change communication tone

**Applied to over-confidence:**
- Challenge absolute statements
- Question guarantees
- Probe error scenarios

## Mode-Specific Behavior

### Quick Mode

**Vectors used:** 2-3 high-priority vectors per category

**Priority ranking:**
1. security-vulnerabilities (if PR analysis)
2. reasoning-flaws
3. assumption-gaps
4. code-duplication (if PR analysis)

**Attack styles:** Most effective 2-3 styles per category

### Standard Mode

**Vectors used:** 5-6 vectors across categories

**Selection strategy:**
- All CRITICAL/HIGH priority categories
- Representative attack styles
- Balanced coverage

### Deep Mode

**Vectors used:** All 10+ categories × 10 styles = 100+ vectors

**Comprehensive coverage:**
- Every risk category
- Every attack style
- Cross-category patterns
- Meta-analysis

## PR-Specific Attack Categories

### Code Analysis Categories

PR analysis includes code-specific categories:

**logic-errors:**
- Off-by-one errors
- Wrong operators
- Incorrect algorithms
- Logic inversions

**edge-case-handling:**
- Missing null checks
- Empty collection handling
- Boundary condition bugs
- Integer overflow/underflow

**breaking-changes:**
- API contract violations
- Function signature changes
- Removed functionality
- Incompatible changes

**dependency-violations:**
- Deprecated API usage
- Version incompatibilities
- Missing dependencies
- Circular dependencies

**api-contract-changes:**
- Changed response formats
- Modified error codes
- Different behavior
- Protocol changes

**security-vulnerabilities:**
- SQL injection
- XSS vulnerabilities
- Authentication bypass
- Authorization issues
- Hardcoded secrets

**input-validation:**
- Missing sanitization
- Insufficient validation
- Type confusion
- Format string bugs

**unintended-side-effects:**
- Unrelated code changes
- Broken functionality
- Performance regression
- Memory leaks

**test-coverage-gaps:**
- Untested code paths
- Missing error cases
- No integration tests
- Insufficient coverage

## Grounding Assessment

### Evidence Validation

Every finding goes through grounding validation (standard/deep modes):

**Quote Matching:**
- EXACT: Finding quotes match context exactly
- CLOSE: Finding quotes are paraphrased
- PARTIAL: Some evidence present
- MISMATCH: Evidence doesn't support claim
- NOT_FOUND: No evidence in context

**Calibration:**
- Adjusts confidence based on evidence strength
- Identifies alternative explanations
- Checks for proportion (finding severity vs actual impact)

### Quality Filters

**Findings are rejected if:**
- Confidence < 0.3
- Evidence strength < 0.4 (deep mode)
- Quote match quality = MISMATCH
- No supporting evidence

**Findings are flagged as uncertain if:**
- Confidence 0.3-0.6
- Alternative explanations exist
- Evidence is circumstantial

## Customization

### Focus Mode

Target specific categories:

```bash
/redteam focus:security-vulnerabilities
/redteam-pr:diff focus:code-duplication
```

**Use cases:**
- Security audit: focus:security-vulnerabilities
- Code quality: focus:code-duplication
- Logic review: focus:reasoning-flaws
- Architecture: focus:dependency-blindness

### Mode Selection

**Quick:** Development iterations
```bash
/redteam-pr:working quick
```

**Standard:** Daily workflow
```bash
/redteam-pr:staged standard
```

**Deep:** Critical reviews
```bash
/redteam-pr:branch deep
```

## Next Steps

- **Usage Guide:** Learn commands in [Usage Guide](./usage-guide.md)
- **Fix Orchestration:** Fix issues in [Fix Orchestrator Guide](./fix-orchestrator.md)
- **GitHub Integration:** Automate in [GitHub Integration Guide](./github-integration.md)
