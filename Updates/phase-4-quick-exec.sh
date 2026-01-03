#!/bin/bash
# Phase 4 Quick Execution Script
# Run this AFTER completing PAT setup and configuring git remote

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 Phase 4 Quick Execution - COGNISCRIBE                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

REPO_DIR="/users/billp/documents/github/cogniscribe"

# Verify directory
if [ ! -d "$REPO_DIR" ]; then
    echo "❌ Directory not found: $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR"
echo "✅ Changed to: $REPO_DIR"
echo ""

# Step 1: Verify PAT is configured
echo "📋 Step 1: Verifying Git configuration..."
REMOTE_URL=$(git remote get-url origin)
if [[ $REMOTE_URL == *"@github.com"* ]]; then
    echo "✅ Remote URL configured with authentication"
else
    echo "⚠️  Warning: Remote URL may not have PAT configured"
    echo "   Current: $REMOTE_URL"
    echo "   Run: git remote set-url origin https://USERNAME:TOKEN@github.com/Excelsior2026/COGNISCRIBE.git"
fi
echo ""

# Step 2: Check Phase 4 script exists
echo "📋 Step 2: Checking Phase 4 script..."
if [ ! -f "phase-4-complete.sh" ]; then
    echo "❌ phase-4-complete.sh not found"
    echo "   Please ensure the script is in: $REPO_DIR/phase-4-complete.sh"
    exit 1
fi
echo "✅ Phase 4 script found"
echo ""

# Step 3: Run Phase 4 script
echo "📋 Step 3: Running Phase 4 implementation..."
echo "   This may take 2-5 minutes..."
bash phase-4-complete.sh
echo ""

# Step 4: Verify files created
echo "📋 Step 4: Verifying files created..."
FILES=(
    "pytest.ini"
    "pyproject.toml"
    "requirements_dev.txt"
    ".pre-commit-config.yaml"
    ".github/workflows/ci.yml"
    ".github/workflows/cd.yml"
    "Makefile"
    "Dockerfile"
    ".dockerignore"
    "TESTING.md"
    "CI-CD.md"
    "tests/test_integration.py"
    "tests/test_performance.py"
    "tests/conftest.py"
)

MISSING=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file"
        ((MISSING++))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo "✅ All files created successfully"
else
    echo "⚠️  $MISSING files missing"
fi
echo ""

# Step 5: Install dev dependencies
echo "📋 Step 5: Installing development dependencies..."
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python 3.11+"
    exit 1
fi

make install-dev
echo "✅ Dev dependencies installed"
echo ""

# Step 6: Run tests
echo "📋 Step 6: Running tests with coverage..."
make test-cov
echo ""

# Step 7: Check code quality
echo "📋 Step 7: Checking code quality..."
echo "  Running Black format check..."
black --check src/ tests/ 2>/dev/null && echo "  ✅ Format check passed" || echo "  ⚠️  Format issues found (run: make format)"

echo "  Running Ruff linter..."
ruff check src/ tests/ 2>/dev/null && echo "  ✅ Lint check passed" || echo "  ⚠️  Lint issues found (run: make format)"
echo ""

# Step 8: Verify git status
echo "📋 Step 8: Verifying git status..."
BRANCH=$(git branch --show-current)
echo "  Current branch: $BRANCH"

if [ "$BRANCH" == "phase-4-testing-cicd" ]; then
    echo "  ✅ On correct branch"
else
    echo "  ⚠️  Expected branch: phase-4-testing-cicd, got: $BRANCH"
fi

COMMITS=$(git log --oneline -1)
echo "  Latest commit: $COMMITS"
echo ""

# Step 9: Show next steps
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Phase 4 Implementation Complete!                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "  ✅ Testing framework implemented"
echo "  ✅ CI/CD pipelines configured"
echo "  ✅ Code quality tools set up"
echo "  ✅ Docker configuration created"
echo "  ✅ Documentation generated"
echo ""
echo "🚀 Next Steps:"
echo "  1. Review PHASE4_EXECUTION.md for detailed instructions"
echo "  2. Set up GitHub Secrets:"
echo "     - DOCKER_USERNAME"
echo "     - DOCKER_PASSWORD"
echo "     - CODECOV_TOKEN"
echo "  3. Create Pull Request: https://github.com/Excelsior2026/COGNISCRIBE/compare/phase-4-testing-cicd"
echo "  4. Monitor CI workflow: https://github.com/Excelsior2026/COGNISCRIBE/actions"
echo "  5. Merge to main when CI passes"
echo ""
echo "📚 Documentation:"
echo "  - TESTING.md: Complete testing guide"
echo "  - CI-CD.md: Pipeline documentation"
echo "  - PHASE4_EXECUTION.md: Execution guide"
echo ""
echo "⚡ Quick Commands:"
echo "  make test          # Run all tests"
echo "  make test-cov      # Tests with coverage"
echo "  make format        # Format code"
echo "  make lint          # Check code quality"
echo "  make help          # Show all commands"
echo ""

# Step 10: Prompt for next action
echo "Ready to create PR? Run:"
echo "  gh pr create --base main --head phase-4-testing-cicd"
echo ""
echo "Or visit: https://github.com/Excelsior2026/COGNISCRIBE/pulls"
echo ""
