# Red Agent Documentation

Complete documentation for the red-agent Claude Code plugin.

## 📚 Documentation Index

### Getting Started

**New to red-agent?** Start here:

1. **[Usage Guide](./usage-guide.md)** - Your complete reference
   - Learn all commands and workflows
   - Understand analysis modes
   - Follow best practices
   - Troubleshoot common issues

### Understanding Red-Agent

**Want to know how it works?**

2. **[Attack Taxonomy](./attack-taxonomy.md)** - The 10x10 matrix explained
   - 11 risk categories in detail
   - 10 attack styles with examples
   - Severity and confidence scoring
   - Grounding and validation

### Fixing Issues

**Ready to fix the findings?**

3. **[Fix Orchestrator](./fix-orchestrator.md)** - Automated remediation
   - Interactive fix workflow
   - GitHub automation mode
   - Fix strategies by category
   - Safety and validation

### Automation

**Want to automate red-agent?**

4. **[GitHub Integration](./github-integration.md)** - CI/CD and agents
   - Claude Code agent setup
   - GitHub Actions workflows
   - PR review automation
   - Scheduled security audits

### Security

**Concerned about security?**

5. **[Security Documentation](./jscpd-security.md)** - Enterprise-grade security
   - Multi-layer protection
   - Supply chain security
   - Incident response
   - Monitoring and alerts

## 🎯 Quick Navigation

### By Task

| I want to... | Read this |
|--------------|-----------|
| Run my first analysis | [Usage Guide - Basic Commands](./usage-guide.md#basic-commands) |
| Analyze a pull request | [Usage Guide - PR Analysis](./usage-guide.md#pr-analysis) |
| Understand a finding | [Attack Taxonomy - Risk Categories](./attack-taxonomy.md#risk-categories-detailed) |
| Fix issues automatically | [Fix Orchestrator - Quick Start](./fix-orchestrator.md#quick-start) |
| Set up GitHub Actions | [GitHub Integration - Workflows](./github-integration.md#github-actions-workflows) |
| Create Claude Code agent | [GitHub Integration - Agent Setup](./github-integration.md#claude-code-agent-integration) |
| Secure npm dependencies | [Security - Overview](./jscpd-security.md#security-layers) |

### By Role

**Developer:**
- [Daily workflow](./usage-guide.md#pr-analysis-workflow)
- [Fixing issues](./fix-orchestrator.md#interactive-mode-workflow)
- [Understanding findings](./attack-taxonomy.md#risk-categories-detailed)

**DevOps Engineer:**
- [GitHub Actions setup](./github-integration.md#github-actions-workflows)
- [Automated fixes](./github-integration.md#automated-fixes)
- [CI/CD integration](./github-integration.md#pr-review-automation)

**Security Engineer:**
- [Attack taxonomy](./attack-taxonomy.md)
- [Security workflows](./github-integration.md#security-considerations)
- [Incident response](./jscpd-security.md#incident-response)

**Team Lead:**
- [Best practices](./usage-guide.md#best-practices)
- [Review gates](./github-integration.md#review-with-approval-gate)
- [Metrics and monitoring](./jscpd-security.md#monitoring-and-alerts)

## 📖 Documentation by Topic

### Commands

**Conversation Analysis:**
```bash
/redteam                    # Standard analysis
/redteam quick              # Fast scan
/redteam deep               # Comprehensive
/redteam focus:security     # Targeted analysis
```
[→ Full command reference](./usage-guide.md#basic-commands)

**PR Analysis:**
```bash
/redteam-pr:staged          # Staged changes
/redteam-pr:working         # Working directory
/redteam-pr:diff            # Branch diff
/redteam-pr:branch          # Full branch
```
[→ PR analysis guide](./usage-guide.md#pr-analysis)

**Fix Orchestration:**
```bash
/redteam-fix-orchestrator              # Interactive
/redteam-fix-orchestrator --mode github # Automated
```
[→ Fix orchestrator guide](./fix-orchestrator.md)

### Risk Categories

| Category | What it Detects | Severity Range |
|----------|-----------------|----------------|
| security-vulnerabilities | SQL injection, XSS, auth bypass | CRITICAL-HIGH |
| code-duplication | Duplicate code, DRY violations | HIGH-MEDIUM |
| logic-errors | Off-by-one, wrong operators | HIGH-LOW |
| input-validation | Missing sanitization | HIGH-MEDIUM |
| breaking-changes | API contract violations | HIGH-MEDIUM |
| information-disclosure | Secret leaks, verbose errors | CRITICAL-LOW |
| edge-case-handling | Missing null checks | MEDIUM-LOW |
| scope-creep | Unintended changes | MEDIUM-LOW |
| test-coverage-gaps | Missing tests | LOW |
| reasoning-flaws | Logical errors | MEDIUM-LOW |

[→ Complete taxonomy](./attack-taxonomy.md)

### Workflows

**Local Development:**
```bash
# 1. Create feature branch
git checkout -b feature/new-auth

# 2. Develop with quick checks
/redteam-pr:working quick

# 3. Pre-commit analysis
git add .
/redteam-pr:staged standard

# 4. Fix issues
/redteam-fix-orchestrator

# 5. Final check
/redteam-pr:diff deep

# 6. Create PR
git commit && git push
gh pr create
```
[→ Full workflow guide](./usage-guide.md#pr-analysis-workflow)

**GitHub Automation:**
```yaml
# PR analysis on every PR
on: pull_request
jobs:
  analyze:
    - run: claude code -m "/redteam-pr:diff standard"

# Automated fixes with label
on: pull_request labeled
  if: github.event.label.name == 'auto-fix'
  jobs:
    fix:
      - run: claude code -m "/redteam-fix-orchestrator --mode github"
```
[→ GitHub integration guide](./github-integration.md)

### Analysis Modes

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| quick | 30-60s | Good | Development iterations |
| standard | 2-5min | Better | Daily PRs |
| deep | 5-15min | Best | Critical reviews |

[→ Mode selection guide](./usage-guide.md#analysis-modes)

## 🔍 Finding Help

### By Problem

**"I don't know where to start"**
→ [Usage Guide - Basic Commands](./usage-guide.md#basic-commands)

**"I got too many findings"**
→ [Usage Guide - Too Many Findings](./usage-guide.md#too-many-findings)

**"I don't understand a finding"**
→ [Attack Taxonomy - Examples](./attack-taxonomy.md#risk-categories-detailed)

**"How do I fix this?"**
→ [Fix Orchestrator - Fix Strategies](./fix-orchestrator.md#fix-strategies-by-category)

**"How do I automate this?"**
→ [GitHub Integration - Workflows](./github-integration.md#github-actions-workflows)

**"Is this secure?"**
→ [Security Documentation](./jscpd-security.md)

### By Error Message

**"No findings detected"**
→ [Usage Guide - Troubleshooting](./usage-guide.md#no-findings-detected)

**"Analysis timeout"**
→ [Usage Guide - Analysis Timeout](./usage-guide.md#analysis-timeout)

**"jscpd not available"**
→ [Usage Guide - jscpd Not Available](./usage-guide.md#jscpd-not-available)

**"Fix failed to apply"**
→ [Fix Orchestrator - Troubleshooting](./fix-orchestrator.md#fix-failed-to-apply)

**"Tests failed after fix"**
→ [Fix Orchestrator - Tests Failed](./fix-orchestrator.md#tests-failed-after-fix)

**Vulnerability detected in jscpd**
→ [Security - Incident Response](./jscpd-security.md#if-vulnerability-detected)

## 🚀 Example Workflows

### First-Time User

```bash
# 1. Verify installation
claude code "/help"  # Should show /redteam commands

# 2. Run first analysis
/redteam quick

# 3. Understand the report
# Read: Attack Taxonomy - Risk Categories

# 4. Try PR analysis
git checkout -b test/red-agent
# Make some changes
/redteam-pr:working standard

# 5. Fix an issue
/redteam-fix-orchestrator

# Success! You're ready to use red-agent
```

### Daily Development

```bash
# Morning: Check main branch
git checkout main && git pull
/redteam-pr:branch quick

# Development: Quick checks
# ... write code ...
/redteam-pr:working quick

# Pre-commit: Standard analysis
git add .
/redteam-pr:staged standard

# Fix issues if found
/redteam-fix-orchestrator

# Commit and PR
git commit && git push
gh pr create

# Evening: Review team PRs
gh pr list
gh pr checkout 123
/redteam-pr:diff deep
```

### Security Audit

```bash
# 1. Deep analysis of main
git checkout main
/redteam deep focus:security-vulnerabilities

# 2. Check recent changes
/redteam-pr:branch deep

# 3. Generate security report
# Export findings to report.md

# 4. Create tracking issues
gh issue create --title "Security: [Finding ID]" --body "..."

# 5. Monitor fix progress
# Track issue closure rate
```

## 📊 Document Statistics

- **Total pages**: 5
- **Total sections**: 50+
- **Code examples**: 100+
- **Commands documented**: 15+
- **Workflows**: 10+

## 🔄 Updates

This documentation is maintained alongside the red-agent plugin.

**Version:** 1.0.0 (with jscpd integration)
**Last updated:** 2026-01-03

## 📝 Contributing

Found an issue? Have a suggestion?

1. **Documentation issues**: Create GitHub issue with label `documentation`
2. **Plugin issues**: Create GitHub issue with label `bug` or `enhancement`
3. **Security issues**: Email security team (do not create public issue)

## 🎓 Learning Path

**Recommended reading order:**

1. **Week 1: Basics**
   - Usage Guide (Commands)
   - Usage Guide (Modes)
   - Your first analysis

2. **Week 2: Understanding**
   - Attack Taxonomy (Overview)
   - Attack Taxonomy (Categories)
   - Interpret findings correctly

3. **Week 3: Fixing**
   - Fix Orchestrator (Interactive)
   - Fix Orchestrator (Strategies)
   - Apply fixes safely

4. **Week 4: Automation**
   - GitHub Integration (Actions)
   - GitHub Integration (Agents)
   - Automate your workflow

5. **Week 5: Security**
   - Security Documentation
   - Incident Response
   - Monitoring

## 📚 Additional Resources

**External Links:**
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [GitHub Actions](https://docs.github.com/actions)
- [jscpd Repository](https://github.com/kucherenko/jscpd)
- [npm Security](https://docs.npmjs.com/auditing-package-dependencies-for-security-vulnerabilities)

**Related Tools:**
- [PAL Integration Guide](../docs/pal-integration.md)
- [Context Engineering](../skills/multi-agent-collaboration/references/context-engineering.md)
- [Rainbow Teaming](../skills/rainbow-teaming/SKILL.md)

---

**Need more help?** Check the [main README](../README.md) or create a GitHub issue.
