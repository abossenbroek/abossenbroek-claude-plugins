# Red Agent Usage Guide

Complete guide to using the red-agent plugin for adversarial analysis and code review.

## Table of Contents

- [Basic Commands](#basic-commands)
- [Conversation Analysis](#conversation-analysis)
- [PR Analysis](#pr-analysis)
- [Fix Orchestration](#fix-orchestration)
- [Analysis Modes](#analysis-modes)
- [Understanding Reports](#understanding-reports)

## Basic Commands

### Conversation Analysis

Analyze the current conversation for potential issues:

```bash
# Standard analysis with 5-6 attack vectors
/redteam

# Quick surface-level analysis (2-3 vectors, no grounding)
/redteam quick

# Deep comprehensive analysis (all vectors, full grounding)
/redteam deep

# Focus on specific risk category
/redteam focus:reasoning-flaws
/redteam focus:security-vulnerabilities
```

**Available focus categories:**
- `reasoning-flaws` - Logical gaps, circular reasoning, false premises
- `assumption-gaps` - Hidden assumptions, unstated constraints
- `context-manipulation` - Missing context, selective information
- `authority-exploitation` - Unverified claims, false expertise
- `information-leakage` - Sensitive data exposure risks
- `hallucination-risks` - Potential for fabricated information
- `over-confidence` - Certainty without evidence
- `scope-creep` - Task expansion, mission drift
- `dependency-blindness` - Missing dependencies, environmental assumptions
- `temporal-inconsistency` - Time-based assumptions, race conditions
- `code-duplication` - Duplicate code, DRY violations (PR analysis only)

### PR Analysis

Analyze code changes in pull requests:

```bash
# Analyze staged changes (git add)
/redteam-pr:staged

# Analyze working directory changes (uncommitted)
/redteam-pr:working

# Analyze diff between branches
/redteam-pr:diff

# Analyze current branch vs main
/redteam-pr:branch
```

**With analysis modes:**
```bash
# Quick PR analysis
/redteam-pr:staged quick

# Deep PR analysis with full grounding
/redteam-pr:diff deep

# Standard PR analysis (default)
/redteam-pr:branch standard
```

### Fix Orchestration

Generate and apply fixes for identified issues:

```bash
# Interactive fix orchestration (CLI mode)
/redteam-fix-orchestrator

# GitHub integration mode (for CI/CD)
/redteam-fix-orchestrator --mode github
```

**Fix workflow:**
1. Review findings from previous red-team analysis
2. Select findings to fix
3. Get 1-3 fix options per finding
4. Choose preferred fix
5. Agent implements fix
6. Review and commit changes

## Analysis Modes

### Quick Mode

**Best for:** Rapid feedback, early development, prototyping

**Characteristics:**
- 2-3 attack vectors (high-priority only)
- No grounding validation
- Fastest execution (30-60 seconds)
- Higher false positive rate

**When to use:**
- Quick sanity checks
- Iterative development
- Early stage code review

**Example:**
```bash
/redteam quick
/redteam-pr:staged quick
```

### Standard Mode (Default)

**Best for:** Regular development, balanced analysis

**Characteristics:**
- 5-6 attack vectors
- Basic grounding validation
- Moderate execution time (2-5 minutes)
- Balanced accuracy/speed

**When to use:**
- Daily code reviews
- Feature development
- Standard PR analysis

**Example:**
```bash
/redteam
/redteam-pr:diff
```

### Deep Mode

**Best for:** Critical code, production deployments, security-sensitive changes

**Characteristics:**
- All attack vectors (10+ categories)
- Full grounding validation
- Meta-analysis layer
- Slowest execution (5-15 minutes)
- Lowest false positive rate

**When to use:**
- Production deployments
- Security-critical changes
- High-stakes decisions
- Final review before merge

**Example:**
```bash
/redteam deep
/redteam-pr:branch deep
```

## PR Analysis Details

### PR Commands Explained

#### `/redteam-pr:staged`
Analyzes changes that have been staged with `git add`:
```bash
git add src/auth/login.py
/redteam-pr:staged
```

**Use case:** Review changes before committing

#### `/redteam-pr:working`
Analyzes all uncommitted changes in working directory:
```bash
# Make changes to files
/redteam-pr:working
```

**Use case:** Quick feedback during development

#### `/redteam-pr:diff`
Analyzes diff between current branch and base branch:
```bash
git checkout feature/new-auth
/redteam-pr:diff
```

**Use case:** Full PR review before creating pull request

#### `/redteam-pr:branch`
Analyzes all changes in current branch vs main:
```bash
git checkout feature/api-redesign
/redteam-pr:branch
```

**Use case:** Comprehensive branch analysis

### PR Analysis Workflow

**Step-by-step example:**

1. **Create feature branch:**
```bash
git checkout -b feature/add-caching
```

2. **Make changes:**
```bash
# Edit files...
git add .
```

3. **Quick analysis of staged changes:**
```bash
/redteam-pr:staged quick
```

4. **Address any critical issues**

5. **Commit changes:**
```bash
git commit -m "Add caching layer"
```

6. **Full analysis before PR:**
```bash
/redteam-pr:diff standard
```

7. **Review findings and fix issues:**
```bash
/redteam-fix-orchestrator
```

8. **Final deep analysis:**
```bash
/redteam-pr:branch deep
```

9. **Create pull request:**
```bash
gh pr create --title "Add caching layer" --body "..."
```

### Large PR Handling

For PRs with 50+ changed files, the coordinator automatically cascades analysis:

**Cascade behavior:**
- Splits large PRs into chunks of ~40 files
- Analyzes each chunk separately
- Aggregates findings
- Prevents context overflow

**Example output:**
```
Analyzing large PR (87 files changed)
Cascading into 3 analysis chunks...

Chunk 1/3: 40 files (src/api/*)
Chunk 2/3: 40 files (src/services/*)
Chunk 3/3: 7 files (tests/*)

Aggregating findings...
```

## Understanding Reports

### Report Structure

Every red-team report contains:

1. **Executive Summary**
   - Overall risk assessment
   - Key findings count
   - Recommended actions

2. **Findings by Severity**
   - CRITICAL: Immediate action required
   - HIGH: Address before merge
   - MEDIUM: Address soon
   - LOW: Optional improvements

3. **Detailed Findings**
   - Finding ID (e.g., CD-001, SV-002)
   - Category and severity
   - Evidence and impact
   - Recommendation
   - Confidence score

4. **Patterns Detected**
   - Cross-cutting issues
   - Systemic problems
   - Architectural concerns

5. **Grounding Assessment** (standard/deep modes)
   - Evidence strength
   - Alternative explanations
   - Confidence calibration

### Finding Categories

#### Conversation Analysis Categories

| Category | Description | Example |
|----------|-------------|---------|
| reasoning-flaws | Logical errors, circular reasoning | "Assumes conclusion in premise" |
| assumption-gaps | Hidden assumptions | "Assumes database is always available" |
| context-manipulation | Missing critical context | "Ignores recent deprecation" |
| authority-exploitation | Unverified claims | "Claims without citation" |
| information-leakage | Sensitive data risks | "May expose API keys in logs" |
| hallucination-risks | Potential fabrication | "Invents non-existent API" |
| over-confidence | Unjustified certainty | "Claims 100% accuracy without testing" |
| scope-creep | Task expansion | "Adds features not requested" |
| dependency-blindness | Missing dependencies | "Ignores external service dependency" |
| temporal-inconsistency | Time-based issues | "Race condition in concurrent access" |

#### PR Analysis Categories

| Category | Description | Example |
|----------|-------------|---------|
| logic-errors | Code logic issues | "Off-by-one error in loop" |
| assumption-gaps | Implicit assumptions | "Assumes input is always valid" |
| edge-case-handling | Missing edge cases | "Doesn't handle empty array" |
| breaking-changes | API contract violations | "Changes function signature" |
| dependency-violations | Dependency issues | "Uses deprecated API" |
| api-contract-changes | Interface changes | "Removes required field" |
| security-vulnerabilities | Security issues | "SQL injection vulnerability" |
| input-validation | Validation gaps | "Missing input sanitization" |
| information-disclosure | Data leakage | "Logs sensitive data" |
| scope-creep | Unintended changes | "Modifies unrelated code" |
| unintended-side-effects | Unexpected impacts | "Breaks existing feature" |
| test-coverage-gaps | Missing tests | "No tests for error path" |
| code-duplication | Duplicate code | "Same logic in 3 files" |

### Severity Guidelines

**CRITICAL:**
- Security vulnerabilities (SQL injection, XSS)
- Data loss risks
- System crashes
- Breaking changes in production code

**HIGH:**
- Logic errors affecting core functionality
- Significant security issues
- Major breaking changes
- High-impact bugs

**MEDIUM:**
- Moderate logic issues
- Code quality concerns
- Maintainability problems
- Minor breaking changes

**LOW:**
- Style issues
- Minor improvements
- Optional refactoring
- Documentation gaps

### Confidence Scores

Each finding includes a confidence score (0.0-1.0):

- **0.9-1.0:** Very confident, almost certain
- **0.7-0.9:** Confident, likely accurate
- **0.5-0.7:** Moderate confidence, may have false positives
- **0.3-0.5:** Low confidence, needs verification
- **0.0-0.3:** Speculative, high false positive risk

**Use confidence scores to prioritize:**
- Always review HIGH/CRITICAL findings with 0.8+ confidence
- Investigate MEDIUM findings with 0.7+ confidence
- Triage LOW findings with 0.6+ confidence

## Best Practices

### When to Run Analysis

**During Development:**
- `/redteam-pr:working quick` - After each feature implementation
- `/redteam quick` - After significant conversation exchanges

**Before Committing:**
- `/redteam-pr:staged standard` - Before git commit
- Review and fix CRITICAL/HIGH findings

**Before PR:**
- `/redteam-pr:diff standard` - Before creating pull request
- Use fix orchestrator for batch fixes
- `/redteam-pr:branch deep` - Final check for critical PRs

**During PR Review:**
- `/redteam-pr:diff deep` - For reviewer's analysis
- Focus on HIGH/CRITICAL findings
- Verify fix implementations

### Workflow Integration

**Local Development:**
```bash
# 1. Feature development
git checkout -b feature/new-feature

# 2. Quick checks during development
/redteam-pr:working quick

# 3. Before committing
git add .
/redteam-pr:staged standard

# 4. Fix issues
/redteam-fix-orchestrator

# 5. Commit
git commit -m "Add new feature"

# 6. Final check before PR
/redteam-pr:diff deep

# 7. Create PR
gh pr create
```

**CI/CD Integration:**
See [GitHub Integration Guide](./github-integration.md) for automated workflows.

## Troubleshooting

### "No findings detected"

**Possible causes:**
- Code is actually clean (good!)
- Analysis mode too quick (try standard/deep)
- Changes too small to detect issues

**Solutions:**
- Run deeper analysis: `/redteam-pr:diff deep`
- Check if changes were staged/committed correctly
- Review git diff manually to verify changes exist

### "Too many findings"

**Possible causes:**
- Large PR (refactoring, migration)
- First-time analysis of legacy code
- High false positive rate (quick mode)

**Solutions:**
- Use fix orchestrator to batch-fix: `/redteam-fix-orchestrator`
- Focus on CRITICAL/HIGH findings first
- Run deep mode for better accuracy
- Split large PRs into smaller chunks

### "Analysis timeout"

**Possible causes:**
- Very large PR (100+ files)
- Deep mode on huge codebase
- Complex analysis requiring many sub-agents

**Solutions:**
- Let cascade mechanism handle large PRs automatically
- Use standard mode instead of deep
- Analyze smaller change sets (staged vs diff)

### "jscpd not available"

**For duplicate code detection:**
```bash
cd red-agent/
npm install
```

See [Installation Guide](../README.md#optional-jscpd-duplicate-code-detection)

## Next Steps

- **Attack Taxonomy:** Learn about all attack categories in [Attack Taxonomy Guide](./attack-taxonomy.md)
- **Fix Orchestration:** Master the fix workflow in [Fix Orchestrator Guide](./fix-orchestrator.md)
- **GitHub Integration:** Automate analysis in [GitHub Integration Guide](./github-integration.md)
- **Security:** Understand security measures in [Security Documentation](./jscpd-security.md)
