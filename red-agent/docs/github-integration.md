# GitHub Integration Guide

Complete guide for integrating red-agent with GitHub workflows and Claude Code agents for automated code review and fixes.

## Table of Contents

- [Overview](#overview)
- [Basic Setup](#basic-setup)
- [Claude Code Agent Integration](#claude-code-agent-integration)
- [GitHub Actions Workflows](#github-actions-workflows)
- [PR Review Automation](#pr-review-automation)
- [Automated Fixes](#automated-fixes)
- [Security Considerations](#security-considerations)
- [Advanced Patterns](#advanced-patterns)

## Overview

Red-agent can integrate with GitHub in multiple ways:

1. **Local CLI** - Manual analysis and fixes
2. **Pre-commit hooks** - Catch issues before commit
3. **GitHub Actions** - Automated PR analysis
4. **Claude Code Agent** - Autonomous code review agent
5. **Fix automation** - Automated fix PRs

## Basic Setup

### Prerequisites

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Install GitHub CLI
brew install gh  # macOS
# or
apt-get install gh  # Linux

# Authenticate
gh auth login
```

### Repository Setup

```bash
# Clone repository
git clone https://github.com/yourorg/yourrepo
cd yourrepo

# Verify red-agent is available
claude code "/help"
# Should show /redteam commands

# Install jscpd for duplicate detection
cd .claude/plugins/red-agent  # or wherever red-agent is located
npm install
cd -
```

## Claude Code Agent Integration

### Agent Architecture

Claude Code agents are autonomous AI agents that can:
- Monitor pull requests
- Run analyses automatically
- Create fix PRs
- Comment on code
- Manage GitHub issues

### Basic Agent Setup

Create `.github/claude-agent.yml`:

```yaml
name: Red Team Code Review Agent

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main, develop]

agent:
  model: claude-3-5-sonnet-20241022

  permissions:
    pull_requests: write
    contents: write
    issues: write

  tools:
    - git
    - github
    - red-agent

  workflow:
    - name: Analyze PR
      run: |
        # Get PR details
        PR_NUMBER=${{ github.event.pull_request.number }}

        # Run red-agent analysis
        claude code -m "/redteam-pr:diff standard"

    - name: Post Results
      if: findings_detected
      run: |
        # Post findings as PR comment
        claude code -m "Create PR comment with red-team findings"

    - name: Create Fix PR
      if: critical_findings
      run: |
        # Create automated fix PR
        claude code -m "/redteam-fix-orchestrator --mode github"
        gh pr create --title "🤖 Automated security fixes" --base ${{ github.head_ref }}
```

### Autonomous Agent Mode

For fully autonomous operation:

```yaml
# .github/claude-agent-auto.yml
name: Autonomous Red Team Agent

agent:
  mode: autonomous

  objectives:
    - Monitor all PRs for security issues
    - Apply automated fixes for CRITICAL findings
    - Create follow-up PRs for HIGH findings
    - Comment on MEDIUM/LOW findings
    - Track fix success rate

  decision_making:
    # Agent autonomously decides when to:
    auto_fix_threshold: CRITICAL  # Auto-fix critical issues
    auto_comment_threshold: HIGH  # Comment on high+ issues
    create_issues_for: [MEDIUM, LOW]  # Create issues for medium/low

  safety:
    require_human_approval:
      - Changes to authentication
      - Database migrations
      - API contract changes

    max_changes_per_pr: 10
    max_auto_prs_per_day: 5
```

### Agent Personality Configuration

Customize agent behavior:

```yaml
# .github/claude-agent-config.yml
agent:
  personality:
    name: "Red Team Reviewer"
    role: "Security-focused code reviewer"

    communication_style:
      tone: professional
      detail_level: comprehensive
      emoji_usage: minimal

    review_style:
      - Prioritize security issues
      - Explain vulnerabilities clearly
      - Provide code examples
      - Link to documentation

    interaction_rules:
      - Never approve PRs with CRITICAL findings
      - Request human review for HIGH complexity fixes
      - Auto-approve LOW complexity security fixes
      - Tag @security-team for critical issues
```

## GitHub Actions Workflows

### Important: Two Approaches

There are **two ways** to use red-agent in GitHub Actions:

1. **Claude Code Action** (Recommended) - Uses `anthropics/claude-code-action@v1`
   - Claude receives a prompt and autonomously runs commands
   - More flexible, can handle complex multi-step workflows
   - Requires ANTHROPIC_API_KEY in secrets
   - Claude posts results as PR comments

2. **Direct CLI** - Install Claude Code CLI and run commands directly
   - More predictable, explicit command execution
   - Easier to parse output and integrate with other steps
   - Can save outputs to files for processing
   - More control over error handling

**Key difference**: The Action gives Claude a goal (e.g., "analyze this PR"), while CLI runs specific commands (e.g., `/redteam-pr:branch`).

### Prerequisites

Before setting up workflows, you need to:

1. **Install Claude Code GitHub App** at https://github.com/apps/claude
   - Grant permissions: Contents (Read & Write), PRs (Read & Write), Issues (Read & Write)

2. **Add API Key to Repository Secrets**
   - Go to Settings → Secrets and variables → Actions
   - Add `ANTHROPIC_API_KEY` with your Claude API key
   - **Alternative**: Use AWS Bedrock or Google Vertex AI credentials

3. **Ensure red-agent plugin is available**
   - **Option A**: Check plugin into your repository at `.claude/plugins/red-agent/`
   - **Option B**: Install during workflow with `git submodule` or `git clone`

### Basic PR Analysis Workflow

**Using Claude Code Action (Recommended)**

```yaml
# .github/workflows/red-agent-analysis.yml
name: Red Agent PR Analysis

on:
  pull_request:
    types: [opened, synchronize]
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for branch comparison

      - name: Install red-agent plugin
        run: |
          # Option A: If plugin checked into repo
          cd red-agent && npm ci && cd ..

          # Option B: Clone plugin from separate repo
          # git clone https://github.com/your-org/red-agent-plugin .claude/plugins/red-agent
          # cd .claude/plugins/red-agent && npm ci && cd -

      - name: Run red-agent analysis
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          prompt: |
            Please run a red-team security analysis on this PR using the red-agent plugin:

            1. Run: /redteam-pr:branch main standard
            2. Review all findings with CRITICAL or HIGH severity
            3. Post a summary comment on the PR with your findings
            4. If CRITICAL findings exist, explain why they must be fixed before merge

            Focus especially on:
            - Security vulnerabilities
            - Code duplication issues
            - Breaking changes
            - Input validation gaps

            Use the red-agent documentation for guidance on interpreting findings.
          claude_args: "--max-turns 10"

      - name: Check for blocking findings
        run: |
          # Claude's analysis will be in the PR comments
          # Optionally parse output and fail workflow
          echo "Review Claude's PR comment for findings"
```

**Alternative: Direct CLI Approach**

```yaml
# .github/workflows/red-agent-cli.yml
name: Red Agent PR Analysis (CLI)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Claude Code CLI
        run: npm install -g @anthropic-ai/claude-code

      - name: Install red-agent dependencies
        run: |
          cd red-agent  # or wherever plugin is located
          npm ci
          cd ..

      - name: Run analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Use Claude Code CLI directly with plugin available
          claude code --print --anthropic-api-key "$ANTHROPIC_API_KEY" \
            "/redteam-pr:branch main standard" > analysis.md

      - name: Post results
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const analysis = fs.readFileSync('analysis.md', 'utf8');

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## 🔍 Red Agent Analysis\n\n${analysis}`
            });

            // Check for CRITICAL findings
            if (analysis.includes('Severity: CRITICAL') || analysis.includes('CRITICAL Issues')) {
              core.setFailed('❌ CRITICAL security findings must be addressed');
            }
```

### Automated Fix Workflow

**Using Claude Code Action**

```yaml
# .github/workflows/red-agent-autofix.yml
name: Red Agent Automated Fixes

on:
  pull_request:
    types: [labeled]
    # Trigger when 'auto-fix' label is added

jobs:
  autofix:
    if: github.event.label.name == 'auto-fix'
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0

      - name: Install red-agent plugin
        run: |
          cd red-agent && npm ci && cd ..

      - name: Run analysis and apply fixes
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          prompt: |
            Please analyze this PR and apply automated fixes using red-agent:

            1. Run: /redteam-pr:branch main standard
            2. Review all HIGH and CRITICAL findings
            3. For each finding with LOW or MEDIUM complexity fix:
               - Run: /redteam-fix-orchestrator --mode github
               - Apply the fix
               - Create a commit
            4. Push all fix commits to this PR branch
            5. Post a comment summarizing what was fixed

            Safety rules:
            - NEVER fix HIGH complexity issues without human review
            - Create separate commits per finding
            - Include finding ID in commit message
            - Run tests after each fix if available

            After fixing, comment on the PR with:
            - Number of findings fixed
            - Number requiring human review
            - Instructions for reviewing the fixes
          claude_args: "--max-turns 20"

      - name: Notify on completion
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.removeLabel({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              name: 'auto-fix'
            });

            await github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: ['auto-fix-applied']
            });
```

**Alternative: Direct CLI with Fix Orchestrator**

```yaml
# .github/workflows/red-agent-autofix-cli.yml
name: Red Agent Automated Fixes (CLI)

on:
  pull_request:
    types: [labeled]

jobs:
  autofix:
    if: github.event.label.name == 'auto-fix'
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0

      - name: Install Claude Code CLI
        run: npm install -g @anthropic-ai/claude-code

      - name: Install red-agent dependencies
        run: |
          cd red-agent && npm ci && cd ..

      - name: Configure git
        run: |
          git config user.name "Red Agent Bot"
          git config user.email "red-agent@users.noreply.github.com"

      - name: Run analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          claude code --print "/redteam-pr:branch main standard" > findings.json

      - name: Apply automated fixes
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Fix orchestrator will create commits
          claude code --print "/redteam-fix-orchestrator --mode github"

      - name: Push fixes
        run: |
          if git log origin/${{ github.head_ref }}..HEAD --oneline | grep -q "fix:"; then
            git push
            echo "fix_applied=true" >> $GITHUB_ENV
          else
            echo "fix_applied=false" >> $GITHUB_ENV
          fi

      - name: Comment on PR
        if: env.fix_applied == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `✅ **Automated fixes applied**

              Red Agent has analyzed the PR and applied fixes for LOW and MEDIUM complexity issues.

              **Next steps:**
              1. Review the fix commits
              2. Run tests locally
              3. Check if any HIGH complexity findings still need manual attention

              See individual commits for details on each fix.`
            });
```

### Scheduled Security Audits

```yaml
# .github/workflows/security-audit.yml
name: Weekly Security Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:  # Manual trigger

jobs:
  audit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Audit main branch
        run: |
          claude code -m "/redteam-pr:branch deep"

      - name: Create audit report issue
        if: findings_detected
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('audit-report.md', 'utf8');

            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `🔐 Weekly Security Audit - ${new Date().toISOString().split('T')[0]}`,
              body: report,
              labels: ['security', 'audit']
            });
```

## PR Review Automation

### Intelligent Review Bot

```yaml
# .github/workflows/intelligent-review.yml
name: Intelligent PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Analyze PR complexity
        id: complexity
        run: |
          FILES_CHANGED=$(gh pr view ${{ github.event.pull_request.number }} --json files --jq '.files | length')
          echo "files_changed=$FILES_CHANGED" >> $GITHUB_OUTPUT

      - name: Choose analysis mode
        id: mode
        run: |
          FILES=${{ steps.complexity.outputs.files_changed }}

          if [ $FILES -lt 5 ]; then
            echo "mode=quick" >> $GITHUB_OUTPUT
          elif [ $FILES -lt 20 ]; then
            echo "mode=standard" >> $GITHUB_OUTPUT
          else
            echo "mode=deep" >> $GITHUB_OUTPUT
          fi

      - name: Run adaptive analysis
        run: |
          claude code -m "/redteam-pr:diff ${{ steps.mode.outputs.mode }}"

      - name: Post findings with context
        uses: actions/github-script@v7
        with:
          script: |
            const mode = '${{ steps.mode.outputs.mode }}';
            const filesChanged = ${{ steps.complexity.outputs.files_changed }};

            let comment = `## 🤖 Intelligent Review (${mode} mode)\n\n`;
            comment += `Analyzed ${filesChanged} changed files\n\n`;
            comment += fs.readFileSync('analysis-report.md', 'utf8');

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: comment
            });
```

### Review with Approval Gate

```yaml
# .github/workflows/review-gate.yml
name: Review Gate

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review-gate:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      checks: write

    steps:
      - uses: actions/checkout@v4

      - name: Red Agent Analysis
        id: analysis
        run: |
          claude code -m "/redteam-pr:diff standard" | tee analysis.log

          # Extract severity counts
          CRITICAL=$(grep -c "CRITICAL" analysis.log || echo 0)
          HIGH=$(grep -c "HIGH" analysis.log || echo 0)

          echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
          echo "high=$HIGH" >> $GITHUB_OUTPUT

      - name: Block PR if critical issues
        if: steps.analysis.outputs.critical > 0
        run: |
          gh pr edit ${{ github.event.pull_request.number }} \
            --remove-label "ready-to-merge" \
            --add-label "blocked-critical-issues"

          exit 1

      - name: Request review if high issues
        if: steps.analysis.outputs.high > 0
        run: |
          gh pr edit ${{ github.event.pull_request.number }} \
            --add-label "needs-security-review"

          # Tag security team
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "@security-team Please review HIGH severity findings"

      - name: Auto-approve if clean
        if: steps.analysis.outputs.critical == 0 && steps.analysis.outputs.high == 0
        run: |
          gh pr review ${{ github.event.pull_request.number }} \
            --approve \
            --body "✅ Red Agent found no critical or high severity issues"
```

## Automated Fixes

### Progressive Fix Strategy

```yaml
# .github/workflows/progressive-fixes.yml
name: Progressive Automated Fixes

on:
  pull_request:
    types: [labeled]
    # Trigger with 'progressive-fix' label

jobs:
  progressive-fix:
    if: github.event.label.name == 'progressive-fix'
    runs-on: ubuntu-latest

    strategy:
      matrix:
        severity: [critical, high, medium]

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}

      - name: Fix ${{ matrix.severity }} issues
        run: |
          claude code -m "/redteam-pr:diff standard"

          # Filter by severity and apply fixes
          claude code -m "Fix only ${{ matrix.severity }} severity findings"

      - name: Run tests
        run: |
          npm test  # or your test command

      - name: Commit if tests pass
        if: success()
        run: |
          git add .
          git commit -m "fix(${{ matrix.severity }}): automated fixes for ${{ matrix.severity }} issues"
          git push

      - name: Rollback if tests fail
        if: failure()
        run: |
          git reset --hard HEAD~1

          gh pr comment ${{ github.event.pull_request.number }} \
            --body "⚠️ Automated ${{ matrix.severity }} fixes failed tests - manual review needed"
```

### Safe Auto-Fix with Validation

```yaml
# .github/workflows/safe-autofix.yml
name: Safe Automated Fixes

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  safe-fix:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}

      - name: Create fix branch
        run: |
          git checkout -b auto-fix/${{ github.head_ref }}

      - name: Apply fixes
        run: |
          claude code -m "/redteam-fix-orchestrator --mode github --safe-mode"

      - name: Run validation suite
        id: validate
        run: |
          # Run comprehensive validation
          npm run lint
          npm run test
          npm run type-check
          npm run security-scan

      - name: Push if validation passes
        if: success()
        run: |
          git push -u origin auto-fix/${{ github.head_ref }}

          # Create fix PR
          gh pr create \
            --title "🤖 Safe automated fixes for #${{ github.event.pull_request.number }}" \
            --body "Automated fixes with full validation" \
            --base ${{ github.head_ref }} \
            --label "automated-fix"

      - name: Report validation failure
        if: failure()
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "❌ Automated fixes failed validation - manual review required"
```

## Security Considerations

### Protecting Sensitive Operations

```yaml
# .github/workflows/secure-review.yml
name: Secure Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Check for sensitive files
        id: sensitive
        run: |
          SENSITIVE_FILES=$(git diff --name-only origin/main | grep -E "(auth|security|crypto|password|secret)" || echo "")

          if [ -n "$SENSITIVE_FILES" ]; then
            echo "detected=true" >> $GITHUB_OUTPUT
            echo "files=$SENSITIVE_FILES" >> $GITHUB_OUTPUT
          fi

      - name: Deep analysis for sensitive changes
        if: steps.sensitive.outputs.detected == 'true'
        run: |
          echo "Sensitive files detected: ${{ steps.sensitive.outputs.files }}"
          claude code -m "/redteam-pr:diff deep focus:security-vulnerabilities"

      - name: Require security team approval
        if: steps.sensitive.outputs.detected == 'true'
        run: |
          gh pr edit ${{ github.event.pull_request.number }} \
            --add-label "requires-security-approval"

          gh pr review ${{ github.event.pull_request.number }} \
            --request-reviewer security-team \
            --comment "🔐 Sensitive files modified - security team review required"
```

### Secret Scanning Integration

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scanning

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Red Agent secret scan
        run: |
          claude code -m "/redteam-pr:diff deep focus:information-leakage"

      - name: Check for hardcoded secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.pull_request.base.sha }}
          head: ${{ github.event.pull_request.head.sha }}

      - name: Block if secrets found
        if: secrets_detected
        run: |
          gh pr edit ${{ github.event.pull_request.number }} \
            --add-label "blocked-secrets-detected"

          exit 1
```

## Advanced Patterns

### Multi-Stage Review Pipeline

```yaml
# .github/workflows/multi-stage-review.yml
name: Multi-Stage Review Pipeline

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  stage-1-quick:
    name: "Stage 1: Quick Scan"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Quick scan
        run: claude code -m "/redteam-pr:diff quick"
      - name: Block if critical
        run: exit 1  # if critical found

  stage-2-standard:
    name: "Stage 2: Standard Analysis"
    needs: stage-1-quick
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Standard analysis
        run: claude code -m "/redteam-pr:diff standard"

  stage-3-deep:
    name: "Stage 3: Deep Analysis"
    needs: stage-2-standard
    if: github.event.pull_request.labels.*.name contains 'critical-pr'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deep analysis
        run: claude code -m "/redteam-pr:diff deep"

  stage-4-fixes:
    name: "Stage 4: Automated Fixes"
    needs: [stage-2-standard, stage-3-deep]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Apply fixes
        run: claude code -m "/redteam-fix-orchestrator --mode github"
```

### Continuous Learning System

```yaml
# .github/workflows/learning-system.yml
name: Continuous Learning

on:
  pull_request:
    types: [closed]  # After PR is merged

jobs:
  learn:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Analyze what was fixed
        run: |
          # Get red-agent findings from PR
          gh pr view ${{ github.event.pull_request.number }} --json comments \
            | jq '.comments[] | select(.body | contains("Red Agent"))' \
            > findings.json

          # Get actual changes made
          git diff ${{ github.event.pull_request.base.sha }} ${{ github.event.pull_request.head.sha }} \
            > changes.diff

      - name: Update patterns database
        run: |
          # Store successful fix patterns
          claude code -m "Analyze findings vs changes to improve future detection"

      - name: Generate metrics
        run: |
          # Track fix success rate, false positives, etc.
          echo "Generating metrics for continuous improvement"
```

## Best Practices

### DO

✅ Run quick analysis during development
✅ Use standard mode for PR reviews
✅ Reserve deep mode for critical PRs
✅ Validate automated fixes before merging
✅ Require human approval for security changes
✅ Track fix success rates
✅ Use labels for automation triggers

### DON'T

❌ Auto-merge without validation
❌ Skip testing after automated fixes
❌ Apply HIGH complexity fixes without review
❌ Ignore false positives (report them)
❌ Bypass security gates
❌ Auto-fix authentication/crypto code
❌ Run deep mode on every commit (too slow)

## Troubleshooting

See [Usage Guide - Troubleshooting](./usage-guide.md#troubleshooting) for common issues.

## Next Steps

- **Usage Guide:** Learn all commands in [Usage Guide](./usage-guide.md)
- **Attack Taxonomy:** Understand findings in [Attack Taxonomy](./attack-taxonomy.md)
- **Fix Orchestrator:** Master fixes in [Fix Orchestrator Guide](./fix-orchestrator.md)
- **Security:** Review security measures in [Security Documentation](./jscpd-security.md)
