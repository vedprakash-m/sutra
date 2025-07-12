# CI/CD Troubleshooting Guide

## Overview

This guide helps diagnose and resolve CI/CD pipeline failures in the Sutra project. It provides systematic approaches to identify root causes and implement lasting solutions.

## Quick Diagnosis Checklist

### 1. Environment Differences
- [ ] Node.js version mismatch (CI: 18, Local: ?)
- [ ] Python version mismatch (CI: 3.12, Local: ?)
- [ ] npm vs npm ci behavior differences
- [ ] Operating system differences (CI: Ubuntu, Local: macOS/Windows)

### 2. Dependency Issues
- [ ] package-lock.json out of sync
- [ ] requirements.txt vs requirements-minimal.txt discrepancies
- [ ] Missing or conflicting package versions

### 3. Script Execution Issues
- [ ] Shell script compatibility (bash vs zsh vs sh)
- [ ] File permissions and executable bits
- [ ] Path separator differences (Unix vs Windows)
- [ ] Temporary file location issues

### 4. Test Environment Issues
- [ ] Missing environment variables
- [ ] Database/service dependencies
- [ ] Race conditions in test setup/teardown

## Common Failure Patterns

### Pattern 1: "Process completed with exit code 1" in Frontend Validation

**Symptoms:**
- Validation passes locally but fails in CI
- Generic exit code 1 without detailed error message
- Failure occurs in frontend validation phase

**Root Causes:**
- TypeScript/ESLint version incompatibilities
- npm install vs npm ci behavior differences
- Temporary file permission issues
- Script error handling problems

**Solutions:**
1. Run `./scripts/pre-ci-validation.sh` locally to simulate CI
2. Check TypeScript and ESLint compatibility matrix
3. Update unified-validation.sh error handling
4. Use workspace-relative temporary files

### Pattern 2: Dependency Resolution Failures

**Symptoms:**
- "Module not found" errors
- Version conflict warnings
- Import resolution failures

**Root Causes:**
- Mismatch between requirements.txt and requirements-minimal.txt
- Node.js package version conflicts
- Missing peer dependencies

**Solutions:**
1. Run dependency synchronization check
2. Update requirements files consistently
3. Lock package versions in package.json

### Pattern 3: Test Environment Setup Failures

**Symptoms:**
- Tests pass locally but fail in CI
- Database connection errors
- Service startup timeouts

**Root Causes:**
- Missing test database setup
- Service dependency ordering
- Environment variable differences

**Solutions:**
1. Use Docker Compose for consistent test environments
2. Implement proper service health checks
3. Add environment variable validation

## Diagnostic Commands

### Local CI Simulation
```bash
# Full CI environment simulation
./scripts/pre-ci-validation.sh

# Quick validation check
./scripts/unified-validation.sh ci core

# Check for environment differences
./scripts/cross-platform-validation.sh
```

### Dependency Analysis
```bash
# Check Node.js dependencies
npm audit
npm ls typescript eslint

# Check Python dependencies
cd api && pip check
cd api && python -c "import sys; print(sys.version)"
```

### Error Analysis
```bash
# Check recent CI logs
git log --oneline -5

# Test specific components
npm test -- --verbose
cd api && python -m pytest -v
```

## Prevention Strategies

### 1. Pre-Commit Validation
- Install pre-commit hooks: `pre-commit install`
- Run full validation: `./scripts/unified-validation.sh local all`

### 2. Pre-Push Validation
- Automatic CI simulation for main branch pushes
- Quick validation for feature branches
- Comprehensive error reporting

### 3. Continuous Monitoring
- Regular dependency updates
- Version compatibility checks
- Cross-platform testing

## Emergency Fixes

### Quick Fix Checklist
1. **Revert last commit if CI was working before:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Skip CI temporarily (only for urgent fixes):**
   ```bash
   git commit -m "urgent fix [skip ci]"
   ```

3. **Force push with fixed dependencies:**
   ```bash
   npm ci && npm run build
   git add package-lock.json
   git commit -m "fix: update dependencies"
   git push origin main
   ```

## Long-term Improvements

### 1. Infrastructure as Code
- Containerize development environment
- Use Docker for consistent local/CI environments
- Implement dev container configuration

### 2. Enhanced Monitoring
- Add CI/CD performance metrics
- Implement failure pattern detection
- Set up automated dependency updates

### 3. Documentation
- Keep this guide updated with new patterns
- Document all configuration changes
- Maintain troubleshooting runbooks

## Support and Escalation

### Self-Service Resources
1. Run diagnostic commands above
2. Check recent commits for breaking changes
3. Review CI/CD logs for specific error messages
4. Test locally with exact CI environment simulation

### When to Escalate
- Critical production deployment blocked
- Systematic CI/CD infrastructure issues
- Security-related failures
- Multiple team members affected

## Related Documentation
- [Local Development Setup](../README.md)
- [Pre-commit Configuration](../.pre-commit-config.yaml)
- [CI/CD Pipeline](../.github/workflows/ci-cd.yml)
- [Cross-platform Validation](../scripts/cross-platform-validation.sh)
