# Maintenance Guide

This document outlines standard maintenance procedures for the Accordant LLM Council, specifically focusing on dependency management and upgrades.

## Dependency Management

The project uses two package managers:
- **Python**: `uv` (manages dependencies via `pyproject.toml`)
- **JavaScript**: `npm` (manages dependencies via `frontend/package.json`)

### Quick Reference Commands

| Action | Command |
|--------|---------|
| **Check All Outdated** | `make check-outdated` |
| **Security Audit** | `make security-audit` |
| **Update Python Packages** | `uv sync --upgrade` |
| **Update JS Packages** | `cd frontend && npm update` |

### Detailed Check

To see exactly what is outdated:

```bash
# Python
uv pip list --outdated

# JavaScript
cd frontend && npm outdated
```

## Upgrade Workflow

1.  **Check Status**: Run `make check-outdated` to see pending updates and security issues.
2.  **Security First**: Address any high-severity vulnerabilities immediately.
    *   Python: `uv sync --upgrade-package <package_name>`
    *   JS: `npm audit fix` or `npm install <package>@latest`
3.  **Routine Updates**:
    *   **Patch/Minor**: Safe to update mostly automatically. Run `uv sync --upgrade` and `npm update`.
    *   **Major**: Requires careful planning and testing.
4.  **Test**: Always run the test suite after upgrading.
    *   `make test-all` (or `uv run pytest` + `npm test`)

### upgrading Specific Packages

**Python (uv):**
```bash
uv sync --upgrade-package fastapi
```

**JavaScript (npm):**
```bash
cd frontend
npm install react@latest
```

## Versioning Strategy

*   **Lock Files**: Always commit `uv.lock` and `frontend/package-lock.json`. These ensure reproducible builds.
*   **Production**: Use strict version pinning in lock files.
*   **Development**: Use semantic version ranges (e.g. `^1.2.3`) in configuration files to allow for security patches.
