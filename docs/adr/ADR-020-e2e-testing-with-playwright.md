# ADR-020: End-to-End Testing with Playwright

**Status**: Accepted  
**Date**: 2025-12-15  
**Owner**: Antigravity  

## Context
The project lacks automated tests for critical user flows (Login, Registration, Chat). Regressions in the GUI or integration between frontend and backend are currently detected manually, which is error-prone and slow.
We need a tool to enforce "Smoke Test" reliability before deployment.

## Decision
We will use **[Playwright](https://playwright.dev/)** for End-to-End (E2E) testing.

**Rationale**:
1.  **Reliability**: Playwright handles modern web app dynamic loading (auto-waiting) better than Selenium/Cypress.
2.  **Speed**: Parallel execution and fast browser contexts.
3.  **DX**: Excellent tooling (Codegen, UI Mode, Trace Viewer).
4.  **Community**: Standard choice for modern React ecosystems.

## Implementation
1.  **Location**: `frontend/tests/e2e/`.
2.  **Config**: `frontend/playwright.config.js`.
3.  **Integration**: Run via `npm run test:e2e` in the `frontend` directory.
4.  **Scope**: Initially covering "Happy Path" smoke tests (e.g., Login -> Dashboard).

## Consequences
- **Positive**: Automated verification of critical paths. Reduced risk of shipping broken UI.
- **Negative**: Adds a dev dependency (`@playwright/test`) and browser binaries (~300MB).
- **Compliance**: Tests must handle ensuring the backend is running (or CI must orchestrate it).
