# Test Coverage Report
**Date**: 2025-12-16
**Total Coverage**: 79%

## Breakdown by Module

| Module | Statements | Missing | Coverage | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Core Logic** |
| `backend/council.py` | 152 | 0 | 100% | Critical path fully covered |
| `backend/council_helpers.py` | 92 | 0 | 100% | Helper logic fully covered |
| `backend/llm_service.py` | 38 | 0 | 100% | |
| `backend/ranking_service.py` | 111 | 36 | 68% | Service logic mostly covered, missing edge cases |
| `backend/evolution_service.py` | 62 | 11 | 82% | core logic covered |
| **API & Routes** |
| `backend/main.py` | 302 | 117 | 61% | Integration tests cover main flows, some error handlers missing |
| `backend/admin_routes.py` | 372 | 85 | 77% | |
| `backend/org_routes.py` | 49 | 7 | 86% | |
| **Data & Config** |
| `backend/storage.py` | 94 | 4 | 96% | High confidence in data persistence |
| `backend/database.py` | 48 | 16 | 67% | |
| `backend/config/personalities.py` | 185 | 28 | 85% | |

## Methodology
Generated using `pytest-cov`:
```bash
uv run pytest --cov=backend --cov-report=term-missing
```

## Goals
*   **Maintain > 80% coverage** on critical paths (Council, Storage).
*   Improve `backend/main.py` coverage by adding more integration tests for edge cases.
*   Improve `backend/ranking_service.py` coverage by adding more varied voting scenarios.
