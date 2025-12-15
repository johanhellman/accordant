# Backend Reliability Hardening — Proposal & Progress

**Status:** Step 1 (Inventory & Discovery)  
**Last Updated:** 2025-12-15

---

## 1. Current State Inventory

### 1A) Backend Structure & Runtime
- **Entry Point:** [`backend/main.py`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/backend/main.py) (FastAPI app definition)
- **Language/Framework:** Python 3.14+ (target), FastAPI, Uvicorn
- **Architecture:** Monolithic API with "Service-like" modularity (admin, orgs, council).
- **Concurrency Model:** Asyncio with `anyio`/FastAPI. Global semaphore limits concurrent LLM requests ([`backend/openrouter.py`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/backend/openrouter.py)).
- **Persistence (Database):** 
    - **Engine:** SQLite (using SQLAlchemy)
    - **Topology:** Multi-tenant via file separation.
        - **System DB:** `data/system.db` (Users, Orgs mappings)
        - **Tenant DBs:** `data/organizations/{id}/tenant.db` (Conversations, Votes)
        - **Definition:** [`backend/database.py`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/backend/database.py)
- **External Dependencies:** OpenRouter API (LLM)

### 1B) Reliability Risk Map

| Vector | Risk Level | Evidence / Rationale | Key Files | Mitigation Candidate |
| :--- | :--- | :--- | :--- | :--- |
| **CI Gaps** | **CRITICAL** | **Backend tests are NOT running in CI.** The current CI workflow ([`.github/workflows/ci.yml`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/.github/workflows/ci.yml)) only enters `frontend/` and runs `npm run preflight`. `pytest` code coverage exists but is ignored by PR gates. | `.github/workflows/ci.yml` | **Step 2:** Add `pytest` and `ruff` to CI. |
| **Migrations** | High | **Ad-hoc / "Lazy" Migrations.** Schema updates happen at runtime inside [`backend/database.py:get_tenant_session`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/backend/database.py#L98). `_migrate_tenant_schema` manually alters tables. No version tracking, no rollbacks. | `backend/database.py` | **Step 6:** Introduce proper migration tool (Alembic) or robust versioned scripts. |
| **Error Handling** | Medium | **Ad-hoc Exceptions.** `HTTPException` is raised directly throughout routes (e.g., [`backend/main.py`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/backend/main.py)). No centralized error normalization or unique internal error codes for debugging. | `backend/main.py` | **Step 4:** Standardize error response shape & internal codes. |
| **LLM Resilience** | Low (Good) | **Robust Client.** `backend/openrouter.py` implements exponential backoff, retries (429/5xx), and global concurrency semaphores. | `backend/openrouter.py` | **Step 5:** Harden further if observability reveals edge cases. |
| **Persistence** | Medium | **SQLite Concurrency.** While `check_same_thread=False` works for read-heavy, write-heavy loads on SQLite can cause `database is locked` errors. | `backend/database.py` | **Step 4/5:** Improved timeout/retry logic for DB locks if observed. |

### 1C) Tooling & CI Inventory
- **Test Framework:** `pytest` (Configured in [`pyproject.toml`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/pyproject.toml))
- **Linting/Formatting:** `ruff` (Configured in `pyproject.toml`)
- **Security Scan:** `bandit` (Configured in `pyproject.toml`)
- **CI Workflow:** GitHub Actions ([`.github/workflows/ci.yml`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/.github/workflows/ci.yml))
    - **Current:** `npm run preflight` (Frontend Lint/Test/Build)
    - **Missing:** Backend Lint/Test

---

## 2. Success Metrics & Baseline
- **PR Gate Coverage:** 100% of PRs must pass Backend Lint (`ruff`) and Backend Tests (`pytest`) before merge. (Currently: 0%)
- **Test Stability:** 0 Flaky tests in CI.
- **Migration Safety:** 0 Runtime schema errors allowed.

---

## 3. Plan: Step 2 (Quick Win Guardrails) - COMPLETED

**Objective:** Close the critical gap in CI/CD by enforcing backend quality checks.

- [x] **Create local "preflight" script**: Created `scripts/check_backend.sh`.
- [x] **Update CI Workflow**: Updated `.github/workflows/ci.yml` to run backend checks using `uv`.
- [x] **Fix Immediate Lints**: Fixed ~100 formatting/linting errors. Suppressed acceptable legacy patterns (ternaries, nested withs) to establish a green baseline for Style & Security.
- [x] **Baseline Status**:
    - **Lint (Ruff):** PASSING (Strictly enforced)
    - **Security (Bandit):** PASSING
    - **Tests (Pytest):** FAILING (64 errors). Marked as non-fatal in CI for now. **Fixing these is the primary goal of Step 3.**

---

## 4. Plan: Step 3 (Tests That Catch Regressions) - NEXT

**Objective:** Repair the existing test suite to catch regressions, then expand coverage.

1.  **Fix Critical Test Failures**: Address the `AttributeError: ... has no attribute 'USERS_FILE'` errors caused by the removal of JSON storage.
2.  **Fix Multi-tenancy Test Collisions**: Ensure tests use isolated ephemeral databases (using `conftest.py` fixtures properly).
3.  **Enforce Passing Tests in CI**: Once fixes are landed, remove the `|| true` from `scripts/check_backend.sh` to make tests a hard blocker.

