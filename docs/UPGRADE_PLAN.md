# Dependency Upgrade Plan

This document outlines the strategy for identifying outdated dependencies and upgrading them systematically.

## Overview

This project uses two package managers:
- **Python**: `uv` (manages dependencies via `pyproject.toml`)
- **JavaScript/Node.js**: `npm` (manages dependencies via `frontend/package.json`)

## Identifying Outdated Components

### Python Dependencies

#### Method 1: Using `uv` (Recommended)
```bash
# Check for outdated packages
uv pip list --outdated

# Or check specific packages
uv pip list --outdated | grep -E "(fastapi|pydantic|httpx)"
```

#### Method 2: Manual Check via PyPI
```bash
# For each package, check latest version
uv pip index versions <package-name>
```

#### Method 3: Using `pip-audit` (Security-focused)
```bash
# Check for security vulnerabilities (already in dev dependencies)
uv run pip-audit
```

### JavaScript Dependencies

#### Method 1: Using `npm outdated` (Recommended)
```bash
cd frontend
npm outdated
```

This shows:
- **Current**: Installed version
- **Wanted**: Version matching semver range in package.json
- **Latest**: Latest version available

#### Method 2: Using `npm-check-updates` (ncu)
```bash
cd frontend
npx npm-check-updates
# Or to see what would be updated:
npx npm-check-updates --target minor  # Only minor/patch updates
npx npm-check-updates --target patch  # Only patch updates
```

#### Method 3: Manual Check
Visit [npmjs.com](https://www.npmjs.com) and check each package's latest version.

### Automated Check Script

Create a script to check all dependencies at once:

```bash
#!/bin/bash
# scripts/check-outdated.sh

echo "=== Python Dependencies ==="
uv pip list --outdated || echo "Note: uv pip list --outdated may not be available"

echo ""
echo "=== JavaScript Dependencies ==="
cd frontend
npm outdated || echo "No outdated packages found"
cd ..
```

## Current Dependency Status

### Python Runtime Dependencies (from `pyproject.toml`)

| Package | Current (min) | Latest Available | Status |
|---------|---------------|------------------|--------|
| fastapi | >=0.115.0 | TBD | Check required |
| uvicorn[standard] | >=0.32.0 | TBD | Check required |
| python-dotenv | >=1.0.0 | TBD | Check required |
| httpx | >=0.27.0 | TBD | Check required |
| pydantic | >=2.9.0 | TBD | Check required |
| passlib[bcrypt] | >=1.7.4 | TBD | Check required |
| pyjwt | >=2.10.1 | TBD | Check required |
| python-multipart | >=0.0.20 | TBD | Check required |
| pyyaml | >=6.0.3 | TBD | Check required |
| cryptography | >=46.0.3 | TBD | Check required |
| requests | >=2.32.5 | TBD | Check required |

### Python Dev Dependencies

| Package | Current (min) | Latest Available | Status |
|---------|---------------|------------------|--------|
| pytest | >=8.0.0 | TBD | Check required |
| pytest-asyncio | >=0.23.0 | TBD | Check required |
| pytest-cov | >=5.0.0 | TBD | Check required |
| pytest-mock | >=3.12.0 | TBD | Check required |
| pip-audit | >=2.10.0 | TBD | Check required |
| pre-commit | >=3.0.0 | TBD | Check required |
| ruff | >=0.8.0 | TBD | Check required |
| bandit[toml] | >=1.7.0 | TBD | Check required |

### JavaScript Runtime Dependencies

| Package | Current | Latest Available | Status |
|---------|---------|------------------|--------|
| react | ^19.2.0 | TBD | Check required |
| react-dom | ^19.2.0 | TBD | Check required |
| react-markdown | ^10.1.0 | TBD | Check required |
| remark-gfm | ^4.0.1 | TBD | Check required |

### JavaScript Dev Dependencies

| Package | Current | Latest Available | Status |
|---------|---------|------------------|--------|
| @eslint/js | ^9.39.1 | TBD | Check required |
| @testing-library/jest-dom | ^6.6.3 | TBD | Check required |
| @testing-library/react | ^16.1.0 | TBD | Check required |
| @testing-library/user-event | ^14.5.2 | TBD | Check required |
| @types/react | ^19.2.5 | TBD | Check required |
| @types/react-dom | ^19.2.3 | TBD | Check required |
| @vitejs/plugin-react | ^5.1.1 | TBD | Check required |
| @vitest/ui | ^4.0.15 | TBD | Check required |
| eslint | ^9.39.1 | TBD | Check required |
| eslint-plugin-react-hooks | ^7.0.1 | TBD | Check required |
| eslint-plugin-react-refresh | ^0.4.24 | TBD | Check required |
| eslint-plugin-security | ^3.0.1 | TBD | Check required |
| globals | ^16.5.0 | TBD | Check required |
| jsdom | ^25.0.1 | TBD | Check required |
| prettier | ^3.4.2 | TBD | Check required |
| vite | ^7.2.4 | TBD | Check required |
| vitest | ^4.0.15 | TBD | Check required |

## Upgrade Strategy

### Phase 1: Assessment (Week 1)

1. **Run outdated checks**
   ```bash
   # Python
   uv pip list --outdated > reports/python-outdated.txt
   
   # JavaScript
   cd frontend && npm outdated > ../reports/js-outdated.txt
   ```

2. **Categorize updates**
   - **Security patches**: Critical, update immediately
   - **Patch versions** (x.y.Z): Low risk, safe to update
   - **Minor versions** (x.Y.z): Medium risk, test thoroughly
   - **Major versions** (X.y.z): High risk, requires code changes

3. **Check for breaking changes**
   - Review changelogs for major/minor updates
   - Check migration guides
   - Identify deprecated features

### Phase 2: Security Updates (Immediate)

**Priority: CRITICAL**

Update all packages with known security vulnerabilities immediately:

```bash
# Python security audit
uv run pip-audit --desc

# JavaScript security audit
cd frontend
npm audit
npm audit fix  # Auto-fix where possible
```

**Process:**
1. Run security audits
2. Update vulnerable packages
3. Test critical paths
4. Deploy immediately

### Phase 3: Patch Updates (Low Risk)

**Priority: HIGH**

Update patch versions (e.g., 1.2.3 → 1.2.4):

```bash
# Python - Update patch versions
uv sync --upgrade-package fastapi --upgrade-package pydantic

# JavaScript - Update patch versions
cd frontend
npm update  # Updates within semver ranges
```

**Process:**
1. Update patch versions
2. Run test suite
3. Quick smoke test
4. Commit if tests pass

### Phase 4: Minor Updates (Medium Risk)

**Priority: MEDIUM**

Update minor versions (e.g., 1.2.3 → 1.3.0):

**Python:**
```bash
# Update specific packages
uv sync --upgrade-package fastapi --upgrade-package httpx

# Or update all
uv sync --upgrade
```

**JavaScript:**
```bash
cd frontend
# Update specific packages
npm install react@^19.3.0 react-dom@^19.3.0

# Or use npm-check-updates for controlled updates
npx npm-check-updates -u --target minor
npm install
```

**Process:**
1. Update one package at a time (or related packages together)
2. Review changelog for breaking changes
3. Run full test suite
4. Manual testing of affected features
5. Commit with detailed message

### Phase 5: Major Updates (High Risk)

**Priority: LOW (Schedule separately)**

Major version updates require careful planning:

**Process:**
1. **Research Phase**
   - Read migration guides
   - Review breaking changes
   - Check compatibility with other dependencies
   - Estimate effort

2. **Planning Phase**
   - Create upgrade branch
   - Document required code changes
   - Plan testing strategy
   - Schedule maintenance window if needed

3. **Implementation Phase**
   - Update dependency version
   - Fix breaking changes
   - Update code as needed
   - Update tests

4. **Testing Phase**
   - Run full test suite
   - Manual testing of all features
   - Performance testing
   - Security audit

5. **Deployment Phase**
   - Merge to main
   - Monitor for issues
   - Have rollback plan ready

## Testing Strategy

### After Each Update

1. **Automated Tests**
   ```bash
   # Python tests
   uv run pytest
   
   # JavaScript tests
   cd frontend && npm test
   ```

2. **Linting**
   ```bash
   make lint-all
   ```

3. **Security Checks**
   ```bash
   # Python
   uv run pip-audit
   uv run bandit -r backend/
   
   # JavaScript
   cd frontend && npm audit
   ```

4. **Smoke Tests**
   - Start backend: `uv run python -m backend.main`
   - Start frontend: `cd frontend && npm run dev`
   - Test critical user flows:
     - Login
     - Create conversation
     - Submit query
     - View responses

### Regression Testing

After major updates, test:
- [ ] User authentication
- [ ] Multi-user isolation
- [ ] Organization management
- [ ] API endpoints (use Swagger UI)
- [ ] Frontend rendering
- [ ] Error handling
- [ ] Performance (response times)

## Rollback Plan

### Python Dependencies

```bash
# Rollback to previous lock file
git checkout HEAD~1 uv.lock
uv sync

# Or rollback specific package
uv sync --upgrade-package fastapi==0.115.0
```

### JavaScript Dependencies

```bash
cd frontend

# Rollback to previous lock file
git checkout HEAD~1 package-lock.json
npm install

# Or rollback specific package
npm install react@19.2.0 react-dom@19.2.0
```

## Upgrade Checklist

### Before Upgrading

- [ ] Create backup branch: `git checkout -b upgrade/dependencies-YYYY-MM-DD`
- [ ] Run full test suite and ensure all tests pass
- [ ] Document current versions
- [ ] Review changelogs for breaking changes
- [ ] Check compatibility matrix

### During Upgrading

- [ ] Update one category at a time (security → patch → minor → major)
- [ ] Update related packages together (e.g., react + react-dom)
- [ ] Commit after each successful update
- [ ] Run tests after each update
- [ ] Document any code changes required

### After Upgrading

- [ ] All tests pass
- [ ] Linting passes
- [ ] Security audit passes
- [ ] Manual smoke tests pass
- [ ] Update documentation if needed
- [ ] Create PR with detailed description
- [ ] Monitor for issues after deployment

## Automation Opportunities

### CI/CD Integration

Add to CI pipeline:
```yaml
# Example GitHub Actions
- name: Check for outdated dependencies
  run: |
    uv pip list --outdated
    cd frontend && npm outdated
```

### Scheduled Checks

Create a weekly job to:
1. Check for outdated packages
2. Check for security vulnerabilities
3. Create issue/PR with update recommendations

### Dependency Update Bots

Consider using:
- **Dependabot** (GitHub): Automated dependency updates
- **Renovate**: More configurable than Dependabot
- **pyup.io**: Python-specific updates

## Version Pinning Strategy

### Current Approach

- **Python**: Minimum versions with `>=` (allows patch/minor updates)
- **JavaScript**: Caret ranges `^` (allows patch/minor updates)

### Recommendations

1. **Production**: Pin exact versions in lock files (`uv.lock`, `package-lock.json`)
2. **Development**: Use ranges for flexibility
3. **Security**: Always pin security-critical packages (e.g., `cryptography`, `pyjwt`)

### Lock File Management

- **Always commit lock files** (`uv.lock`, `package-lock.json`)
- **Never manually edit lock files**
- **Regenerate after dependency changes**: `uv sync` or `npm install`

## Monitoring and Maintenance

### Regular Schedule

- **Weekly**: Check for security updates
- **Monthly**: Review minor version updates
- **Quarterly**: Plan major version updates
- **Ad-hoc**: Update when security vulnerabilities are discovered

### Tools

- **Python**: `pip-audit`, `safety`, `bandit`
- **JavaScript**: `npm audit`, `snyk`, `retire.js`

## Example Upgrade Workflow

### Scenario: Updating FastAPI from 0.115.0 to 0.116.0

```bash
# 1. Create branch
git checkout -b upgrade/fastapi-0.116.0

# 2. Check current version
uv pip show fastapi

# 3. Review changelog
# Visit: https://fastapi.tiangolo.com/release-notes/

# 4. Update dependency
uv sync --upgrade-package fastapi

# 5. Run tests
uv run pytest

# 6. Check for breaking changes
# Review test output and errors

# 7. Update code if needed
# (None required for patch/minor updates typically)

# 8. Commit
git add pyproject.toml uv.lock
git commit -m "chore(deps): upgrade fastapi to 0.116.0

- Updated fastapi from 0.115.0 to 0.116.0
- All tests passing
- No breaking changes detected"

# 9. Create PR and review
```

## Resources

### Python

- [PyPI](https://pypi.org/) - Package repository
- [pip-audit](https://pypa.github.io/pip-audit/) - Security auditing
- [Safety DB](https://github.com/pyupio/safety-db) - Security vulnerability database

### JavaScript

- [npmjs.com](https://www.npmjs.com/) - Package repository
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit) - Security auditing
- [npm-check-updates](https://github.com/raineorshine/npm-check-updates) - Update checker

### General

- [Semantic Versioning](https://semver.org/) - Version numbering scheme
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format

## Notes

- Always test in a separate branch before merging
- Keep upgrade commits separate from feature work
- Document any breaking changes and migration steps
- Consider the impact on production before major updates
- Monitor error logs after deployment

