# jscpd Security Documentation

Security measures and best practices for jscpd npm dependency management.

## Overview

Red-agent uses jscpd for duplicate code detection with multi-layer security:
- **Package locking** with SHA-512 integrity hashes ✅ IMPLEMENTED
- **npm audit** on every commit and in CI ✅ IMPLEMENTED
- **Subresource integrity** verification ✅ IMPLEMENTED
- **Supply chain attack** mitigation ✅ IMPLEMENTED
- **MITM protection** via npm's built-in security ✅ IMPLEMENTED

### Implementation Status

**Currently Implemented** (v1.3.0):
- ✅ Exact version pinning (package.json)
- ✅ SHA-512 integrity hashes (package-lock.json)
- ✅ Pre-commit npm audit hooks
- ✅ CI validation for dependencies
- ✅ Integrity verification script (verify_npm_integrity.py)

**Planned/Future Enhancements**:
- ⏳ Real-time monitoring and alerting
- ⏳ Automated incident response workflows
- ⏳ Runtime behavioral validation
- ⏳ jscpd execution sandboxing
- ⏳ Telemetry for anomaly detection

**Note**: The security measures documented below describe both implemented features and best practices for enterprise deployments. Features marked as "planned" represent recommended enhancements for production environments with strict security requirements.

## Security Layers

### Layer 1: Version Pinning

**File:** `red-agent/package.json`

```json
{
  "dependencies": {
    "jscpd": "4.0.5"  // Exact version, no ranges
  }
}
```

**Protection:**
- Prevents automatic updates to potentially compromised versions
- Ensures consistent behavior across environments
- Requires explicit update decision

**Why exact versions:**
- No `^4.0.5` (would allow 4.x.x)
- No `~4.0.5` (would allow 4.0.x)
- Only `4.0.5` (exact match required)

### Layer 2: Integrity Hashing

**File:** `red-agent/package-lock.json`

```json
{
  "packages": {
    "node_modules/jscpd": {
      "version": "4.0.5",
      "integrity": "sha512-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    }
  }
}
```

**Protection:**
- SHA-512 cryptographic hash of package tarball
- npm verifies hash on installation
- Any tampering detected immediately

**Verification process:**
1. npm downloads package from registry
2. Computes SHA-512 hash of downloaded tarball
3. Compares with `integrity` field in lock file
4. Installation fails if hashes don't match

### Layer 3: Pre-Commit Validation

**File:** `.pre-commit-config.yaml`

```yaml
- id: npm-audit-jscpd
  name: Audit npm dependencies (jscpd)
  entry: bash -c "cd red-agent && npm audit --production"

- id: verify-npm-integrity
  name: Verify npm integrity hashes
  entry: python scripts/verify_npm_integrity.py

- id: check-npm-lock-committed
  name: Check npm lock file is committed
  entry: bash -c "[ -f red-agent/package-lock.json ]"
```

**Protection:**
- Catches known vulnerabilities before commit
- Verifies all packages have integrity hashes
- Ensures lock file is committed (not ignored)

**What it detects:**
- CVEs in dependencies
- Missing integrity hashes
- Uncommitted lock file
- Outdated security advisories

### Layer 4: CI Validation

**File:** `.github/workflows/ci.yml`

```yaml
validate-npm-deps:
  steps:
    - name: Install npm dependencies
      run: |
        cd red-agent
        npm ci  # Uses lock file, fails if mismatch

    - name: Audit npm dependencies
      run: |
        cd red-agent
        npm audit --production

    - name: Verify lock file integrity
      run: |
        cd red-agent
        npm ls --json > /tmp/deps.json
        grep -q '"integrity"' /tmp/deps.json
```

**Protection:**
- Validates on every PR
- Catches newly disclosed vulnerabilities
- Verifies lock file consistency
- Blocks merging if vulnerabilities found

## MITM Protection

### How npm Prevents MITM Attacks

**Step 1: HTTPS Transport**
```
npm → HTTPS (TLS 1.3) → registry.npmjs.org
```
- All communication encrypted
- Server certificate validated
- No plain-text transmission

**Step 2: Integrity Verification**
```
1. npm downloads package over HTTPS
2. npm computes: SHA-512(tarball) = computed_hash
3. npm reads: integrity field = expected_hash
4. npm compares: computed_hash == expected_hash
5. Installation succeeds only if match
```

**Attack scenarios prevented:**
- **Scenario:** Attacker intercepts HTTPS connection
  - **Prevention:** TLS certificate validation fails

- **Scenario:** Attacker compromises DNS
  - **Prevention:** TLS certificate won't match

- **Scenario:** Attacker modifies package in transit
  - **Prevention:** Integrity hash verification fails

- **Scenario:** Attacker compromises npm mirror
  - **Prevention:** Integrity hash won't match original

## Supply Chain Attack Mitigation

### September 2025 npm Attack Context

**Background:** Large-scale supply chain compromise affected npm ecosystem (Sept 16-23, 2025)

**Red-agent protection:**
1. **Exact version pinning** - jscpd 4.0.5 published before attack
2. **Lock file commitment** - Immutable hash prevents substitution
3. **Audit on commit** - Detects if jscpd later flagged as compromised
4. **CI validation** - Continuous monitoring for new advisories

### Verification Before Update

**When updating jscpd version:**

```bash
# 1. Check npm advisory
npm view jscpd versions --json
npm view jscpd time --json

# 2. Verify publish date
npm view jscpd@4.0.6 time
# Should be BEFORE Sept 16, 2025 or AFTER verification

# 3. Check for security advisories
npm audit

# 4. Review changelog
npm view jscpd@4.0.6 homepage

# 5. Install with exact version
npm install --save-exact jscpd@4.0.6

# 6. Verify integrity hash changed
git diff red-agent/package-lock.json

# 7. Test thoroughly
npm test

# 8. Commit lock file
git add red-agent/package-lock.json
git commit -m "build(deps): update jscpd to 4.0.6"
```

### Defense-in-Depth Strategy

**Multiple validation points:**

```
Developer Machine
  ├─ Pre-commit hooks (npm audit)
  ├─ Lock file verification
  └─ Local testing

Git Repository
  ├─ Lock file committed
  ├─ Version control history
  └─ Code review

CI/CD Pipeline
  ├─ npm audit in CI
  ├─ Integrity verification
  ├─ Automated tests
  └─ Security scanning

Production
  └─ npm ci (strict lock file)
```

**No single point of failure:**
- If pre-commit bypassed → CI catches it
- If CI compromised → lock file hash prevents substitution
- If registry compromised → integrity verification fails

## Security Best Practices

### DO

✅ **Always commit package-lock.json**
```bash
git add red-agent/package-lock.json
```

✅ **Use npm ci in CI/CD**
```bash
npm ci  # Strict lock file, fails on mismatch
```
Not:
```bash
npm install  # Might update, less strict
```

✅ **Run npm audit regularly**
```bash
npm audit
npm audit fix  # Apply fixes
```

✅ **Verify integrity after install**
```bash
python scripts/verify_npm_integrity.py
```

✅ **Update dependencies explicitly**
```bash
npm install --save-exact jscpd@4.0.6
git add package.json package-lock.json
```

### DON'T

❌ **Never add package-lock.json to .gitignore**
```bash
# Bad - defeats security
red-agent/package-lock.json
```

❌ **Never use --no-save flag**
```bash
# Bad - doesn't update lock file
npm install --no-save jscpd
```

❌ **Never skip npm audit**
```bash
# Bad - bypasses security check
npm audit --audit-level=none
```

❌ **Never use version ranges for critical deps**
```json
// Bad - allows automatic updates
"jscpd": "^4.0.5"

// Good - exact version
"jscpd": "4.0.5"
```

❌ **Never ignore npm audit failures in CI**
```yaml
# Bad
- run: npm audit || true  # Ignores failures

# Good
- run: npm audit  # Fails on vulnerabilities
```

## Incident Response

### If Vulnerability Detected

**Scenario:** npm audit reports vulnerability in jscpd

**Response steps:**

1. **Assess severity**
```bash
npm audit
# Note: CRITICAL/HIGH/MEDIUM/LOW
```

2. **Check if actively exploited**
```bash
# Search security advisories
npm view jscpd
# Check CVE databases
```

3. **Determine fix availability**
```bash
npm audit fix --dry-run
```

4. **If fix available:**
```bash
npm audit fix
npm test
git add package-lock.json
git commit -m "security: fix jscpd vulnerability"
```

5. **If no fix available:**
   - **Option A:** Wait for upstream fix
   - **Option B:** Find alternative package
   - **Option C:** Apply workaround
   - **Option D:** Disable jscpd temporarily

```bash
# Disable gracefully (red-agent has graceful degradation)
mv red-agent/node_modules red-agent/node_modules.disabled
# duplicate-code-analyzer will skip with note
```

### If Supply Chain Compromise Suspected

**Indicators:**
- Unexpected package behavior
- Suspicious network activity
- Unknown file system access
- Security audit alerts

**Response:**

1. **Isolate immediately**
```bash
# Stop using potentially compromised package
rm -rf red-agent/node_modules
```

2. **Verify integrity**
```bash
# Check if lock file hash matches expected
git log -p red-agent/package-lock.json
```

3. **Scan for indicators of compromise**
```bash
# Check for suspicious files
find red-agent/node_modules -name "*.js" -exec grep -l "eval\|exec\|child_process" {} \;
```

4. **Report to security team**
- Document suspicious behavior
- Preserve logs and artifacts
- Report to npm security team

5. **Recover safely**
```bash
# Use known-good version
git checkout <last-known-good-commit> -- red-agent/package.json red-agent/package-lock.json
npm ci
```

## Monitoring and Alerts

⏳ **Status**: OPTIONAL/RECOMMENDED - Not required for basic usage

These monitoring features are recommended for enterprise deployments or teams with strict security requirements. Basic protection (integrity hashes, npm audit) is already active.

### Automated Monitoring (Optional)

**Setup GitHub Dependabot:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/red-agent"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
```

**Setup npm audit alerts:**

```yaml
# .github/workflows/security-audit.yml
name: Weekly npm Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Sunday midnight

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          cd red-agent
          npm audit --audit-level=moderate
```

### Manual Monitoring

**Weekly checks:**
```bash
# Check for new vulnerabilities
cd red-agent
npm audit

# Check for outdated packages
npm outdated

# Review security advisories
npm view jscpd
```

## Additional Resources

- **npm security:** https://docs.npmjs.com/auditing-package-dependencies-for-security-vulnerabilities
- **CISA npm alert:** https://www.cisa.gov/news-events/alerts/2025/09/23/widespread-supply-chain-compromise-impacting-npm-ecosystem
- **jscpd repository:** https://github.com/kucherenko/jscpd
- **npm advisory database:** https://github.com/advisories

## Questions?

**Q: Why not use a different duplicate detection tool?**
A: jscpd is well-maintained, widely used, and has good security track record. Plus it's the de-facto standard for JS/TS/Python duplicate detection.

**Q: Can I skip jscpd installation?**
A: Yes! Red-agent has graceful degradation - duplicate-code-analyzer will skip with a note if jscpd not available.

**Q: Is npm really secure enough?**
A: With proper practices (lock files, auditing, integrity verification), npm is as secure as any package manager. The key is defense-in-depth.

**Q: What if npm registry is compromised?**
A: The lock file integrity hashes protect you - even if the registry serves a compromised package, the hash won't match and installation will fail.

**Q: Should I audit transitive dependencies too?**
A: Yes! npm audit checks all dependencies (direct and transitive). That's why we run it in pre-commit and CI.
