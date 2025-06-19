# Local Validation Guide

This guide ensures your changes pass CI/CD checks before pushing to the repository.

## Quick Pre-Commit Validation

### Essential Check (30 seconds)

```bash
# Check formatting (CRITICAL - will fail CI/CD if incorrect)
npm run format:check

# Fix formatting if needed
npm run format
```

### Comprehensive Validation (5 minutes)

```bash
# Run full pre-commit validation
./scripts/pre-commit-validation.sh
```

## CI/CD Failure Prevention

### Common Issues and Solutions

#### 1. Code Formatting Issues

**Error:** `Code style issues found`
**Solution:**

```bash
npm run format
git add .
git commit --amend --no-edit
```

#### 2. TypeScript Compilation Errors

**Error:** `Type check failed`
**Solution:**

```bash
npm run type-check  # See specific errors
# Fix TypeScript errors, then:
git add .
git commit --amend --no-edit
```

#### 3. Linting Issues

**Error:** `ESLint errors found`
**Solution:**

```bash
npm run lint        # See specific errors
npm run lint:fix    # Auto-fix what can be fixed
# Fix remaining errors manually, then:
git add .
git commit --amend --no-edit
```

#### 4. Build Issues

**Error:** `Build failed`
**Solution:**

```bash
npm run build       # See build errors
# Fix issues, then:
git add .
git commit --amend --no-edit
```

## Automation Setup

### 1. Enable Pre-commit Hooks

```bash
# Install pre-commit (one-time setup)
pip install pre-commit
pre-commit install

# Test the hooks
pre-commit run --all-files
```

### 2. Git Hook Setup (Manual)

```bash
# Copy the git hook
cp scripts/git-pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 3. VS Code Integration

Add to your VS Code settings.json:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "typescript.preferences.includePackageJsonAutoImports": "off"
}
```

## Validation Scripts Reference

| Script                               | Purpose               | Duration |
| ------------------------------------ | --------------------- | -------- |
| `npm run format:check`               | Check code formatting | 10s      |
| `npm run format`                     | Fix code formatting   | 15s      |
| `npm run lint`                       | Check code quality    | 20s      |
| `npm run type-check`                 | Check TypeScript      | 15s      |
| `npm run build`                      | Test production build | 30s      |
| `./scripts/pre-commit-validation.sh` | Full validation       | 5min     |

## Troubleshooting

### Large Number of Files Changed

If you see many files in `npm run format`, you may have:

1. Changed line endings (Windows/Mac/Linux)
2. Updated dependencies that changed formatting rules
3. Modified `.prettierrc` configuration

**Solution:**

```bash
# Let Prettier fix everything
npm run format
git add .
git commit -m "fix: apply consistent code formatting"
```

### Coverage Files Being Formatted

Coverage HTML files shouldn't be formatted. Ensure `.prettierignore` includes:

```
# Coverage reports
htmlcov/
coverage/
.coverage
```

### Python Files Being Checked

Python files are not handled by Prettier. If you see Python formatting issues:

```bash
# For Python formatting (if needed)
black api/
isort api/
```

## Emergency Fix for CI/CD Failures

If CI/CD is failing due to formatting:

```bash
# 1. Pull latest changes
git pull origin main

# 2. Fix formatting
npm run format

# 3. Commit the fix
git add .
git commit -m "fix: resolve code formatting issues"

# 4. Push the fix
git push
```

## Best Practices

1. **Always run `npm run format:check` before committing**
2. **Use the pre-commit validation script for important changes**
3. **Set up automatic formatting in your editor**
4. **Don't commit generated files (coverage, build outputs)**
5. **Run full validation before creating pull requests**

## Files to Never Commit

- `htmlcov/` - Python coverage reports
- `coverage/` - JavaScript coverage reports
- `dist/` - Build outputs
- `node_modules/` - Dependencies
- `.venv/` - Python virtual environments
- `*.log` - Log files
- `.DS_Store` - Mac OS files
