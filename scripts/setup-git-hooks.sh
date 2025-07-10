#!/bin/bash

# Enhanced Git hooks setup script
# Configures pre-commit, pre-push, and other Git hooks for the Sutra project

set -e

echo "🔧 Setting up Git hooks for Sutra project..."

# Ensure we're in the project root
if [ ! -f "package.json" ] || [ ! -d "api" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    if command -v pip3 &> /dev/null; then
        pip3 install pre-commit
    elif command -v pip &> /dev/null; then
        pip install pre-commit
    else
        echo "❌ Python pip not found. Please install Python and pip first."
        exit 1
    fi
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
# Temporarily unset custom hooks path for pre-commit installation
git config --unset-all core.hooksPath 2>/dev/null || true
pre-commit install

# Configure Git to use custom hooks directory
git config core.hooksPath .githooks

# Install pre-push hook
if [ -f ".githooks/pre-push" ]; then
    chmod +x .githooks/pre-push
    echo "✅ Pre-push hook configured"
fi

# Create a commit-msg hook for conventional commits (optional)
cat > .githooks/commit-msg << 'EOF'
#!/bin/bash
# Commit message validation (optional conventional commits check)

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?\!?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format!"
    echo "Please use conventional commits format:"
    echo "  feat: add new feature"
    echo "  fix: fix a bug"
    echo "  docs: update documentation"
    echo "  style: formatting changes"
    echo "  refactor: code refactoring"
    echo "  test: add or update tests"
    echo "  chore: maintenance tasks"
    echo ""
    echo "Current message: $(cat $1)"
    exit 1
fi
EOF

chmod +x .githooks/commit-msg

echo ""
echo "✅ Git hooks setup completed successfully!"
echo ""
echo "📋 Configured hooks:"
echo "  • Pre-commit: Runs code quality checks before each commit"
echo "  • Pre-push: Runs validation before pushing to remote"
echo "  • Commit-msg: Validates commit message format (conventional commits)"
echo ""
echo "🚀 You're all set! The hooks will run automatically on git operations."
echo ""
echo "💡 To run pre-commit manually: pre-commit run --all-files"
echo "💡 To skip hooks (not recommended): git commit --no-verify"
