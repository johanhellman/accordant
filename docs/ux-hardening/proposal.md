# UX Hardening & Reliability Proposal

**Status**: Living Document  
**Owner**: Antigravity (Agent)  
**Last Updated**: 2025-12-15

---

## 1. Project Inventory & Tooling
**Base Path**: `/frontend`

| Category | Tool / Pattern | Config Files |
| :--- | :--- | :--- |
| **Framework** | React 19 + Vite 7 (ES Modules) | `package.json`, `vite.config.js` |
| **Language** | JavaScript (ESM) | `package.json` (`"type": "module"`) |
| **Build** | Vite (`vite build`) | `vite.config.js` |
| **Linting** | ESLint 9 (Flat Config) | `eslint.config.js` |
| **Formatting** | Prettier | `.prettierrc.json` |
| **Unit Testing** | Vitest + React Testing Library | `frontend/src/api.test.js`, `frontend/src/test/setup.js` |
| **E2E Testing** | **None found** | N/A |
| **CI/CD** | **None (Quality Gates)**. Only Claude Code Review. | `.github/workflows/claude.yml` |

**Observations**:
- The project is a modern React setup (Vite + React 19).
- **Critical Gap**: No CI workflows run `lint`, `test`, or `build` on Pull Requests. Regressions can be merged easily.
- **Testing Gap**: Only [`api.js`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/frontend/src/api.js) appears to have unit tests key logic. Component tests seem absent.

---

## 2. Reliability Risk Map

### A. CI/CD Quality Gates (Critical)
*   **Risk**: `main` branch is unprotected check-wise. Breaking changes (syntax, build failures) can land without warning.
*   **Evidence**: `.github/workflows/` contains only AI code review actions.
*   **Mitigation**: Implement `ci.yml` to run `npm ci`, `npm run lint`, `npm run test`, `npm run build`.

### B. API Client & Data Fetching
*   **Risk**: Manual `fetch` wrapper in [`api.js`](file:///Users/johanhellman/Projects/LLM%20Experiments/accordant/frontend/src/api.js).
    *   **Singleton Token**: `let authToken = null` module-level state. Safe-ish in browser, brittle in tests/SSR.
    *   **Repetitive Error Handling**: Every method manually checks `if (!response.ok)` and parses errors. High chance of inconsistency.
    *   **Hardcoded Base**: Depends on `Vite` env vars or implicit relative paths.
*   **Mitigation**: Standardize error interception, consider a tiny wrapper class or maintain the module but centralized error normalization.

### C. Authentication State
*   **Risk**: Auth token is stored in memory (`api.js`) and likely context (`AuthContext.jsx`). Page refresh might lose state if not synced to localStorage/cookies (needs verification in `AuthContext`).
*   **Mitigation**: Verify persistence strategy. Add E2E tests for "Login -> Refresh -> Still Logged In".

### D. Component Stability
*   **Risk**: No visible component tests. UI regressions (e.g., button finding, form submission) are manually tested or untested.
*   **Mitigation**: Add Smoke Tests for critical paths (Login, Register, Chat).

---

## 3. Success Metrics & Baseline

### Definitions
*   **Reliability**: Ability to deploy changes without breaking existing critical flows (Login, Chat, Admin).
*   **Detectability**: Time to find a regression (Target: <5 mins in CI).

### Metrics
| Metric | Baseline (Today) | Target (Phase 1) |
| :--- | :--- | :--- |
| **CI Gates** | 0 checks | Lint, Typecheck (if added), Test, Build |
| **E2E Smoke Tests** | 0 scenarios | 3 (Login, Create Chat, Send Message) |
| **Unit Test Coverage** | Low (API only) | High (Utils + API + Core Logic) |
| **Linting** | Manual command | Enforced on PR |

---

## Proposed Next Steps

### Step 2: Quick Win Guardrails
1.  **Strict Lint Command**: Ensure `npm run lint` fails on warnings (or fix them).
2.  **Preflight Script**: Create `npm run preflight` to run lint + test + build locally.
3.  **Basic CI**: Create `.github/workflows/ci.yml` to enforce the above.

### 1. "Quick Win" Guardrails (Step 2 Implementation)
**Status**: [x] Implemented

We have established a baseline of reliability tools without altering the codebase architecture.

#### New Scripts
- **`npm run test:ci`**: Runs unit tests in a non-interactive mode suitable for CI.
- **`npm run preflight`**: A "safe-to-push" check that runs:
  1. Linting (`eslint`)
  2. Formatting Check (`prettier`)
  3. Unit Tests (`vitest run`)
  4. Production Build (`vite build`)

#### CI/CD
- **GitHub Actions (`.github/workflows/ci.yml`)**: Automatically runs the `preflight` suite on every push to `main` and all Pull Requests.

#### Code Quality Improvements
- Expanded ESLint globals to fix `process` undefined errors.
- Fixed numerous React hook dependencies and unused variable warnings.
- Resolved "dead code" in `SystemPromptsEditor.jsx` ensuring cleaner maintenance.
- Fixed `UserManagement` and `Sidebar` tests to be robust against implementation details (using semantic roles and `within` scoping).
### Step 3: Stabilize Shared Primitives (Implemented)
1.  **Status**: [x] Implemented
2.  **Refactoring**: `api.js` now uses a standardized `request` helper and `ApiError` class.
3.  **Auth**: Token injection is centralized in the request helper.

### Step 4: E2E Smoke Suite (Implemented)
1.  **Status**: [x] Implemented
2.  **Tooling**: Playwright installed and configured.
3.  **Tests**: `login.spec.js` covers Landing -> Login -> Register -> Authenticated Empty State.
4.  **Docs**: Added ADR-020 and updated Developer Guide.

### Step 5: (Next Steps)
Review metrics and expand test coverage.
