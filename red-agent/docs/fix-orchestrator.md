# Fix Orchestrator Guide

Complete guide to using the fix orchestrator for automated issue remediation.

## Overview

The fix orchestrator is an interactive agent that:
1. Reviews findings from red-team analysis
2. Generates multiple fix options for each finding
3. Lets you choose preferred fixes
4. Implements fixes automatically
5. Creates commits with proper attribution

## Quick Start

### Basic Usage

```bash
# Run red-team analysis first
/redteam-pr:diff standard

# Then launch fix orchestrator
/redteam-fix-orchestrator
```

The orchestrator will:
1. Load findings from the previous analysis
2. Prioritize by severity (CRITICAL → HIGH → MEDIUM → LOW)
3. Present fix options for each finding
4. Wait for your selection
5. Implement chosen fixes
6. Create commit

### GitHub Integration Mode

```bash
/redteam-fix-orchestrator --mode github
```

**Differences in GitHub mode:**
- Non-interactive (automated)
- Uses intelligent defaults
- Creates separate commits per finding
- Prepares PR description
- Does NOT auto-push (manual review required)

## Interactive Mode Workflow

### Step 1: Finding Selection

Orchestrator presents findings by severity:

```
Found 5 findings from previous analysis:

CRITICAL Findings (1):
  [1] SV-001: SQL injection in user query handler

HIGH Findings (2):
  [2] CD-001: Duplicate validation logic in auth modules
  [3] LF-001: Off-by-one error in pagination

MEDIUM Findings (2):
  [4] IV-001: Missing input validation on API endpoint
  [5] TS-001: Insufficient test coverage for error paths

Select findings to fix (comma-separated, e.g., 1,2,5):
> 1,2,3
```

**Selection strategies:**
- Fix critical issues first: `1`
- Batch similar issues: `2,3,5`
- All issues: `all`
- Skip to next: `skip`

### Step 2: Fix Options

For each selected finding, orchestrator generates 1-3 fix options:

```
Finding SV-001: SQL injection in user query handler
Severity: CRITICAL
Location: src/api/users.py:45-50

Fix Options:

Option A (RECOMMENDED): Use parameterized queries
  Complexity: LOW
  Risk: MINIMAL
  Estimated time: 5 minutes

  Changes:
    - Replace string concatenation with parameterized query
    - Add query validation
    - Update tests

  Pros:
    + Industry best practice
    + Prevents all SQL injection
    + No performance impact

  Cons:
    - Requires changing query structure

Option B: Input sanitization
  Complexity: MEDIUM
  Risk: MODERATE
  Estimated time: 15 minutes

  Changes:
    - Add comprehensive input sanitization
    - Escape special characters
    - Add validation layer

  Pros:
    + Quick implementation
    + No query changes

  Cons:
    - More error-prone
    - Harder to maintain
    - May miss edge cases

Option C: Use ORM
  Complexity: HIGH
  Risk: MODERATE
  Estimated time: 1 hour

  Changes:
    - Replace raw SQL with SQLAlchemy ORM
    - Add ORM models
    - Update all related queries

  Pros:
    + Long-term solution
    + Better maintainability
    + Type safety

  Cons:
    - Large refactoring
    - Learning curve
    - More changes needed

Choose option (A/B/C) or skip:
> A
```

### Step 3: Implementation

Orchestrator implements the chosen fix:

```
Implementing fix for SV-001...

[1/3] Analyzing current code structure...
[2/3] Applying parameterized query pattern...
[3/3] Updating tests...

Fix applied successfully!

Files changed:
  M src/api/users.py (10 lines changed)
  M tests/test_users.py (5 lines added)

Proceed to next finding? (y/n)
> y
```

### Step 4: Commit Creation

After all fixes are applied:

```
All fixes applied successfully!

Summary:
  3 findings fixed
  2 files modified
  15 lines changed
  5 tests updated

Create commit? (y/n)
> y

Commit message:
fix: address critical security and code quality issues

- Fix SQL injection in user query handler (SV-001)
- Remove duplicate validation logic (CD-001)
- Fix off-by-one error in pagination (LF-001)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

Commit created: a3b7c9d
```

## GitHub Integration Mode

### Automated Workflow

GitHub mode is designed for CI/CD pipelines:

```bash
# In CI workflow
/redteam-pr:diff standard
/redteam-fix-orchestrator --mode github
```

**Behavior:**
1. Loads findings from previous analysis
2. Filters to CRITICAL and HIGH severity only
3. Generates fixes using intelligent defaults:
   - Chooses RECOMMENDED option automatically
   - For duplicate code: extracts to utility function
   - For security issues: uses industry best practices
   - For logic errors: applies safest fix
4. Creates separate commits per finding
5. Outputs PR description with fix summary

**Example commit sequence:**

```
Commit 1:
fix(security): parameterize SQL queries to prevent injection

Fixes SV-001: SQL injection in user query handler
Severity: CRITICAL
Confidence: 0.95

Changes:
- Replace string concatenation with parameterized queries
- Add query parameter validation
- Update related tests

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>

Commit 2:
refactor(auth): extract duplicate validation to shared utility

Fixes CD-001: Duplicate validation logic in auth modules
Severity: HIGH
Confidence: 0.92

Changes:
- Create src/auth/validators.py with validate_password()
- Update login.py to use shared validator
- Update signup.py to use shared validator
- Add validator tests

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

### PR Description Generation

GitHub mode also generates PR description:

```markdown
## Automated Security and Quality Fixes

This PR contains automated fixes for issues identified by red-agent analysis.

### Fixes Applied

#### CRITICAL Issues (1)

- **SV-001:** SQL injection in user query handler
  - **Fix:** Parameterized queries
  - **Confidence:** 95%
  - **Files:** src/api/users.py, tests/test_users.py

#### HIGH Issues (1)

- **CD-001:** Duplicate validation logic in auth modules
  - **Fix:** Extracted to shared utility
  - **Confidence:** 92%
  - **Files:** src/auth/validators.py, src/auth/login.py, src/auth/signup.py

### Test Coverage

All fixes include updated tests:
- 5 new tests added
- 3 existing tests updated
- 100% coverage for changed code

### Review Checklist

- [ ] Verify SQL queries use parameterized format
- [ ] Confirm validation logic works consistently
- [ ] Check test coverage for edge cases

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Fix Strategies by Category

### Security Vulnerabilities

**SQL Injection:**
- Option A: Parameterized queries (RECOMMENDED)
- Option B: Input sanitization
- Option C: ORM migration

**XSS:**
- Option A: Template escaping (RECOMMENDED)
- Option B: Input sanitization
- Option C: Content Security Policy

**Hardcoded Secrets:**
- Option A: Environment variables (RECOMMENDED)
- Option B: Config files with .gitignore
- Option C: Secret management service

### Code Duplication

**Exact Duplication:**
- Option A: Extract to function (RECOMMENDED)
- Option B: Extract to class
- Option C: Extract to utility module

**Structural Duplication:**
- Option A: Create base class (RECOMMENDED)
- Option B: Use composition
- Option C: Apply strategy pattern

**Logic Duplication:**
- Option A: Create shared utility (RECOMMENDED)
- Option B: Use dependency injection
- Option C: Refactor to microservice

### Logic Errors

**Off-by-One:**
- Option A: Fix boundary condition (RECOMMENDED)
- Option B: Add assertions
- Option C: Refactor algorithm

**Race Conditions:**
- Option A: Add locking mechanism (RECOMMENDED)
- Option B: Use atomic operations
- Option C: Refactor to eliminate shared state

**Null Pointer:**
- Option A: Add null checks (RECOMMENDED)
- Option B: Use Optional types
- Option C: Refactor to eliminate null

### Input Validation

**Missing Validation:**
- Option A: Add validation layer (RECOMMENDED)
- Option B: Use schema validation library
- Option C: Create validator service

**Insufficient Sanitization:**
- Option A: Add comprehensive sanitization (RECOMMENDED)
- Option B: Use allowlist approach
- Option C: Implement input transformation pipeline

## Complexity Levels

### LOW Complexity

**Characteristics:**
- Simple code changes
- No architectural impact
- Low risk of regression
- Quick to implement (< 15 minutes)

**Examples:**
- Add null checks
- Fix typos in logic
- Add missing validation
- Update single function

**Risk:** MINIMAL

### MEDIUM Complexity

**Characteristics:**
- Multiple file changes
- Moderate refactoring
- Some architectural impact
- Standard implementation time (15-60 minutes)

**Examples:**
- Extract duplicate code to utility
- Refactor function structure
- Update API contracts
- Add new module

**Risk:** MODERATE

### HIGH Complexity

**Characteristics:**
- Large-scale refactoring
- Significant architectural changes
- Multiple component impact
- Extended implementation time (> 1 hour)

**Examples:**
- Migrate to ORM
- Implement new design pattern
- Add dependency injection
- Create microservice

**Risk:** HIGH

## Best Practices

### When to Use Interactive Mode

**Use interactive mode when:**
- You want control over fix selection
- Multiple fix strategies are viable
- Complex architectural decisions needed
- Code review required before implementation

**Example workflow:**
```bash
/redteam-pr:diff deep
/redteam-fix-orchestrator  # Interactive
# Review each fix option
# Choose best approach
# Verify implementation
```

### When to Use GitHub Mode

**Use GitHub mode when:**
- CI/CD automation required
- Standard fixes for common issues
- Batch processing of findings
- Consistent fix patterns

**Example workflow:**
```yaml
# .github/workflows/red-agent.yml
- name: Run red-agent analysis
  run: claude code "/redteam-pr:diff standard"

- name: Apply automated fixes
  run: claude code "/redteam-fix-orchestrator --mode github"

- name: Create PR
  run: gh pr create --title "Automated fixes" --body "$(cat pr-description.md)"
```

### Safety Guidelines

**Always:**
- Review generated code before committing
- Run tests after applying fixes
- Check for unintended side effects
- Verify fix addresses root cause

**Never:**
- Apply HIGH complexity fixes without review
- Skip testing after automated fixes
- Merge without human verification
- Trust confidence < 0.7 blindly

### Batch Processing

**Small batches (1-3 findings):**
```bash
# Select related issues
> 1,2,3
# Review and apply quickly
```

**Large batches (4+ findings):**
```bash
# Fix by severity
> 1  # Fix CRITICAL first
# Review, commit, then continue
> 2,3  # Fix HIGH batch
# Review, commit, then continue
> 4,5,6  # Fix MEDIUM batch
```

## Troubleshooting

### "No findings to fix"

**Cause:** Fix orchestrator didn't find previous analysis results

**Solution:**
```bash
# Run analysis first
/redteam-pr:diff standard

# Then run orchestrator (same session)
/redteam-fix-orchestrator
```

### "Fix failed to apply"

**Causes:**
- Merge conflict with recent changes
- File modified since analysis
- Syntax error in generated code

**Solutions:**
1. Re-run analysis: `/redteam-pr:diff standard`
2. Apply fixes manually using recommendation
3. Skip problematic fix and continue with others

### "Tests failed after fix"

**Cause:** Fix introduced regression or broke tests

**Solutions:**
1. Review fix implementation
2. Check if tests need updating
3. Verify fix addresses intended issue
4. Consider alternative fix option

### "Confidence score too low"

**When orchestrator shows:** "⚠️ Low confidence (0.45) - manual review recommended"

**Actions:**
1. Review finding evidence carefully
2. Check alternative explanations
3. Verify issue actually exists
4. Consider skipping if uncertain
5. Consult with team before applying

## Advanced Usage

### Custom Fix Strategies

You can guide the orchestrator:

```
Choose option (A/B/C) or custom:
> custom

Describe preferred fix strategy:
> Use strategy pattern instead of inheritance

Generating custom fix based on your preference...
```

### Partial Fixes

Fix only part of a finding:

```
Apply full fix or partial? (full/partial)
> partial

Select components to fix:
[X] Core logic fix
[ ] Test updates (skip)
[ ] Documentation (skip)

Applying partial fix...
```

### Fix Review

Request detailed explanation:

```
Choose option (A/B/C) or explain:
> explain A

Detailed explanation of Option A:

Current code:
  query = f"SELECT * FROM users WHERE name = '{user_input}'"

Problem:
  Direct string interpolation allows SQL injection

Fix approach:
  1. Convert to parameterized query
  2. Add parameter binding
  3. Update query execution

Result:
  query = "SELECT * FROM users WHERE name = ?"
  cursor.execute(query, (user_input,))

Why this works:
  Database driver handles escaping
  Special characters treated as literal
  Injection impossible

Would you like to proceed with this fix? (y/n)
> y
```

## Integration Examples

### Local Development

```bash
# Development workflow
git checkout -b fix/security-issues

# Analyze and fix
/redteam-pr:diff standard
/redteam-fix-orchestrator

# Review changes
git diff

# Commit (orchestrator creates commit)
# Push
git push -u origin fix/security-issues

# Create PR
gh pr create
```

### CI/CD Pipeline

```yaml
# .github/workflows/auto-fix.yml
name: Automated Security Fixes

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-and-fix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run red-agent analysis
        run: |
          claude code -m "/redteam-pr:diff standard"

      - name: Apply automated fixes
        run: |
          claude code -m "/redteam-fix-orchestrator --mode github"

      - name: Create fix PR
        if: ${{ steps.fix.outputs.fixes_applied == 'true' }}
        run: |
          git checkout -b auto-fix/${{ github.head_ref }}
          git push -u origin auto-fix/${{ github.head_ref }}
          gh pr create \
            --title "🤖 Automated fixes for ${{ github.head_ref }}" \
            --body-file pr-description.md \
            --label "automated-fix"
```

## Next Steps

- **Usage Guide:** Learn all commands in [Usage Guide](./usage-guide.md)
- **Attack Taxonomy:** Understand finding categories in [Attack Taxonomy](./attack-taxonomy.md)
- **GitHub Integration:** Full CI/CD setup in [GitHub Integration Guide](./github-integration.md)
