# Branch Protection Configuration for Sutra
# Apply these settings in GitHub Repository Settings > Branches > Add rule

## Main Branch Protection Rules

### 1. Basic Protection ✅
- [x] Require a pull request before merging
- [x] Require approvals: **1** (for single person team, this can be yourself)
- [x] Dismiss stale PR approvals when new commits are pushed
- [x] Require review from code owners (if CODEOWNERS file exists)

### 2. Status Check Requirements ✅
**Required status checks that must pass:**
- [x] `code-quality` (ESLint, TypeScript, formatting)
- [x] `frontend-tests` (unit tests + build validation) 
- [x] `backend-tests` (Python tests + validation)
- [x] `infrastructure-tests` (Bicep validation)
- [x] `security-scan` (vulnerability scanning)
- [x] `e2e-tests` (integration tests)

**Settings:**
- [x] Require branches to be up to date before merging
- [x] Require status checks to pass before merging

### 3. Additional Restrictions ✅
- [x] Restrict pushes that create files larger than 100MB
- [x] Require signed commits (recommended for security)
- [x] Include administrators (apply rules to admins too)

### 4. Merge Options ✅ 
- [x] Allow squash merging (recommended for clean history)
- [ ] Allow merge commits (disable for linear history)
- [ ] Allow rebase merging (disable to prevent confusion)

### 5. Delete Head Branches ✅
- [x] Automatically delete head branches after merge

---

## Recommended Workflow for Single Developer/Small Team

### Daily Development:
```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes, commit frequently
git add .
git commit -m "feat: add new feature"

# 3. Before pushing - run local validation
npm run ci:local

# 4. Push to feature branch
git push origin feature/new-feature

# 5. Create PR in GitHub UI
# 6. Wait for all status checks to pass
# 7. Self-approve (if you're the only developer)
# 8. Squash and merge
```

### Emergency Hotfixes:
```bash
# For critical production issues only
git checkout -b hotfix/critical-fix

# Make minimal changes
git add .
git commit -m "fix: critical production issue"

# Fast track validation
npm run precommit  # Quick checks only

# Push and create emergency PR
git push origin hotfix/critical-fix

# Mark PR as urgent, merge after essential checks pass
```

---

## GitHub Repository Settings

### 1. Actions Permissions
- **Actions permissions**: Allow all actions and reusable workflows
- **Fork pull request workflows**: Require approval for first-time contributors

### 2. Secrets Configuration
Required secrets for CI/CD:
- `AZURE_CREDENTIALS` (service principal JSON)
- `AZURE_STATIC_WEB_APPS_API_TOKEN` (from Azure portal)

### 3. Environments
Create environments:
- **production**: Require manual approval for deployments
  - Protection rules: Required reviewers (1)
  - Wait timer: 0 minutes (for fast deployment)

### 4. Vulnerability Alerts
- [x] Enable Dependabot alerts
- [x] Enable Dependabot security updates
- [x] Enable Dependabot version updates (optional)

---

## Quick Setup Commands

```bash
# Install pre-commit hooks locally
pip install pre-commit
pre-commit install

# Create CODEOWNERS file (optional)
echo "* @your-github-username" > .github/CODEOWNERS

# Test the complete validation pipeline locally
npm run ci:local:full
```

---

## Cost-Optimized Considerations

Since you're using single slot, single environment deployment:

1. **Fast Feedback**: Status checks run in parallel to minimize wait time
2. **Essential Checks Only**: Focus on tests that catch real issues
3. **Efficient Resource Usage**: Use caching, minimal dependencies
4. **Emergency Bypass**: Allow hotfix process for critical issues

This configuration ensures production safety while maintaining high deployment velocity for a small team.
