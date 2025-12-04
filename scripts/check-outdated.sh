#!/bin/bash
# Script to check for outdated dependencies in both Python and JavaScript packages
# Usage: ./scripts/check-outdated.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports"

# Create reports directory if it doesn't exist
mkdir -p "$REPORTS_DIR"

echo "=========================================="
echo "Dependency Outdated Check"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Python Dependencies Check
echo "=== Python Dependencies ==="
echo ""

cd "$PROJECT_ROOT"

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Checking Python packages with uv..."
    
    # Try to get outdated packages (uv may not have this command, so we'll try alternatives)
    if uv pip list --outdated &> /dev/null; then
        uv pip list --outdated > "$REPORTS_DIR/python-outdated.txt" 2>&1 || true
        if [ -s "$REPORTS_DIR/python-outdated.txt" ]; then
            echo "Outdated Python packages found:"
            cat "$REPORTS_DIR/python-outdated.txt"
        else
            echo "✓ All Python packages are up to date"
        fi
    else
        echo "Note: 'uv pip list --outdated' not available, trying alternative method..."
        
        # Alternative: Check installed vs latest versions manually
        echo "Installed Python packages:"
        uv pip list | head -20
        echo ""
        echo "To check for updates, run: uv sync --upgrade"
    fi
    
    echo ""
    echo "Security audit (pip-audit):"
    if uv run pip-audit --desc 2>/dev/null | head -30; then
        echo ""
        echo "Full report saved to: $REPORTS_DIR/python-security-audit.txt"
        uv run pip-audit --desc > "$REPORTS_DIR/python-security-audit.txt" 2>&1 || true
    else
        echo "Note: pip-audit not available or no issues found"
    fi
else
    echo "⚠️  uv not found. Install it from https://docs.astral.sh/uv/"
fi

echo ""
echo "=========================================="
echo ""

# JavaScript Dependencies Check
echo "=== JavaScript Dependencies ==="
echo ""

cd "$PROJECT_ROOT/frontend"

if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        echo "Checking JavaScript packages with npm..."
        
        # Check for outdated packages
        npm outdated > "$REPORTS_DIR/js-outdated.txt" 2>&1 || true
        
        if [ -s "$REPORTS_DIR/js-outdated.txt" ]; then
            # Check if it's just the header or actual outdated packages
            if grep -q "Package" "$REPORTS_DIR/js-outdated.txt" && ! grep -q "Current" "$REPORTS_DIR/js-outdated.txt"; then
                echo "✓ All JavaScript packages are up to date"
            else
                echo "Outdated JavaScript packages found:"
                cat "$REPORTS_DIR/js-outdated.txt"
            fi
        else
            echo "✓ All JavaScript packages are up to date"
        fi
        
        echo ""
        echo "Security audit (npm audit):"
        npm audit --audit-level=moderate > "$REPORTS_DIR/js-security-audit.txt" 2>&1 || true
        
        if grep -q "found 0 vulnerabilities" "$REPORTS_DIR/js-security-audit.txt"; then
            echo "✓ No security vulnerabilities found"
        else
            echo "Security issues found:"
            head -50 "$REPORTS_DIR/js-security-audit.txt"
            echo ""
            echo "Full report saved to: $REPORTS_DIR/js-security-audit.txt"
        fi
        
        echo ""
        echo "To update packages:"
        echo "  - Patch updates: npm update"
        echo "  - Check updates: npx npm-check-updates"
        echo "  - Update all: npx npm-check-updates -u && npm install"
    else
        echo "⚠️  npm not found. Install Node.js from https://nodejs.org/"
    fi
else
    echo "⚠️  package.json not found in frontend directory"
fi

echo ""
echo "=========================================="
echo ""
echo "Reports saved to: $REPORTS_DIR/"
echo "  - python-outdated.txt"
echo "  - python-security-audit.txt"
echo "  - js-outdated.txt"
echo "  - js-security-audit.txt"
echo ""
echo "For detailed upgrade plan, see: docs/UPGRADE_PLAN.md"

