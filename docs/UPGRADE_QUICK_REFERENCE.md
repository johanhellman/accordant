# Dependency Upgrade Quick Reference

Quick reference guide for checking and upgrading dependencies.

## Quick Commands

### Check for Outdated Dependencies

```bash
# Check all dependencies (recommended)
make check-outdated

# Or use the shell script directly
./scripts/check-outdated.sh

# Detailed analysis with Python script
make analyze-deps

# Check Python only
make check-outdated-py

# Check JavaScript only
make check-outdated-js
```

### Security Audits

```bash
# Run security audits for all dependencies
make security-audit

# Python security audit only
make security-check-py

# JavaScript security audit
cd frontend && npm audit
```

## Upgrade Workflow

### 1. Check Current Status

```bash
make check-outdated
```

This will:
- Check Python packages for updates
- Check JavaScript packages for updates
- Run security audits
- Save reports to `reports/` directory

### 2. Review Reports

Check the generated reports:
- `reports/python-outdated.txt` - Outdated Python packages
- `reports/python-security-audit.txt` - Python security issues
- `reports/js-outdated.txt` - Outdated JavaScript packages
- `reports/js-security-audit.txt` - JavaScript security issues

### 3. Prioritize Updates

**Priority Order:**
1. 🔴 **Security vulnerabilities** - Update immediately
2. 🟢 **Patch updates** (x.y.Z) - Low risk, safe to update
3. 🟡 **Minor updates** (x.Y.z) - Test thoroughly
4. ⚪ **Major updates** (X.y.z) - Plan separately

### 4. Update Dependencies

#### Python Updates

```bash
# Update specific package
uv sync --upgrade-package <package-name>

# Update all packages (within constraints)
uv sync --upgrade

# Update to latest versions (may break constraints)
uv sync --upgrade-package <package-name> --upgrade-package <package-name>
```

#### JavaScript Updates

```bash
cd frontend

# Update within semver ranges (safe)
npm update

# Check what would be updated
npx npm-check-updates

# Update specific package
npm install <package>@latest

# Update all packages (use with caution)
npx npm-check-updates -u
npm install
```

### 5. Test After Updates

```bash
# Run all tests
uv run pytest
cd frontend && npm test

# Run linting
make lint-all

# Security checks
make security-audit

# Manual smoke test
# Start backend and frontend, test critical flows
```

### 6. Commit Changes

```bash
git add pyproject.toml uv.lock frontend/package.json frontend/package-lock.json
git commit -m "chore(deps): upgrade <package> to <version>

- Updated <package> from <old> to <new>
- All tests passing
- Security audit clean"
```

## Common Scenarios

### Security Vulnerability Found

```bash
# 1. Check details
uv run pip-audit --desc
cd frontend && npm audit

# 2. Auto-fix where possible
cd frontend && npm audit fix

# 3. Manual update if needed
uv sync --upgrade-package <vulnerable-package>
cd frontend && npm install <vulnerable-package>@latest

# 4. Test and deploy immediately
```

### Major Version Update Needed

```bash
# 1. Create branch
git checkout -b upgrade/<package>-major

# 2. Research breaking changes
# - Read changelog
# - Check migration guide
# - Review compatibility

# 3. Update dependency
uv sync --upgrade-package <package>  # or npm install

# 4. Fix breaking changes
# - Update code
# - Update tests
# - Update documentation

# 5. Test thoroughly
make lint-all
uv run pytest
cd frontend && npm test

# 6. Create PR with detailed description
```

### Update All Patch Versions

```bash
# Python - Update all packages within constraints
uv sync --upgrade

# JavaScript - Update within semver ranges
cd frontend && npm update

# Test
make lint-all
uv run pytest
cd frontend && npm test

# Commit if tests pass
```

## Troubleshooting

### Update Breaks Tests

```bash
# Rollback to previous lock file
git checkout HEAD~1 uv.lock
uv sync

# Or rollback specific package
uv sync --upgrade-package <package>==<old-version>
```

### npm Update Fails

```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Or update specific package
npm install <package>@<version>
```

### uv Sync Issues

```bash
# Clear cache and reinstall
rm -rf .venv uv.lock
uv sync

# Or sync specific groups
uv sync --all-groups
```

## Files to Track

When upgrading dependencies, these files may change:

- `pyproject.toml` - Dependency specifications
- `uv.lock` - Locked Python versions (always commit)
- `frontend/package.json` - Dependency specifications
- `frontend/package-lock.json` - Locked JavaScript versions (always commit)

**Always commit lock files** - they ensure reproducible builds.

## Resources

- **Full Upgrade Plan**: `docs/UPGRADE_PLAN.md`
- **Python Packages**: https://pypi.org/
- **JavaScript Packages**: https://www.npmjs.com/
- **Security**: Run `make security-audit` regularly

## Automation

Consider setting up:

1. **Weekly automated checks** - Run `make check-outdated` and create issues
2. **Dependabot** - GitHub's automated dependency updates
3. **Renovate** - More configurable than Dependabot
4. **CI integration** - Check for outdated deps in CI pipeline

## Best Practices

1. ✅ **Update regularly** - Don't let dependencies get too far behind
2. ✅ **Test after updates** - Always run tests before committing
3. ✅ **Update one category at a time** - Security → Patch → Minor → Major
4. ✅ **Review changelogs** - Especially for major/minor updates
5. ✅ **Commit lock files** - Ensures reproducible builds
6. ✅ **Use branches** - Test updates in separate branches
7. ✅ **Document breaking changes** - If any code changes are needed

