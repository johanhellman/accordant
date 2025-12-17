# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the LLM Council project. ADRs document important architectural decisions, their context, and consequences.

## What are ADRs?

Architecture Decision Records are documents that capture important architectural decisions made along with their context and consequences. They help maintain institutional memory and provide a clear record of why certain design choices were made.

## ADR Format

Each ADR follows this structure:

- **Status**: Proposed, Accepted, Deprecated, or Superseded
- **Context**: The issue motivating this decision
- **Decision**: The change that we're proposing or have agreed to implement
- **Consequences**: What becomes easier or more difficult to do because of this change

## Index of ADRs

| ADR # | Title | Status | Date |
|-------|-------|--------|------|
| [ADR-001](ADR-001-3-stage-council-deliberation.md) | 3-Stage Council Deliberation System | Accepted | 2025-11-25 |
| [ADR-002](ADR-002-anonymized-peer-review.md) | Anonymized Peer Review in Stage 2 | Accepted | 2025-11-25 |
| [ADR-003](ADR-003-json-file-storage.md) | JSON-Based File Storage | Superseded by ADR-016 | 2025-11-25 |
| [ADR-004](ADR-004-openrouter-api-integration.md) | Router-Independent LLM API Integration | Accepted | 2025-11-25 |
| [ADR-005](ADR-005-personality-mode.md) | Personality Mode for Council Members | Accepted (Modified by ADR-007) | 2025-11-25 |
| [ADR-006](ADR-006-context-sliding-window.md) | Context Management with Sliding Window | Accepted | 2025-11-25 |
| [ADR-007](ADR-007-modular-personality-configuration.md) | Modular Personality Configuration | Accepted | 2025-11-25 |
| [ADR-008](ADR-008-admin-api-and-config.md) | Admin API and Configuration | Accepted |
| [ADR-009](ADR-009-ui-redesign.md) | UI Redesign and Theme Overhaul | Accepted | 2025-11-25 |
| [ADR-010](ADR-010-multi-user-architecture.md) | Multi-User Architecture | Superseded by ADR-016 | 2025-12-03 |
| [ADR-011](ADR-011-client-side-voting-statistics.md) | Client-Side Voting Statistics Aggregation | Accepted | 2025-12-04 |
| [ADR-012](ADR-012-multi-tenancy-architecture.md) | Multi-Tenancy Architecture | Accepted | 2025-12-04 |
| [ADR-013](ADR-013-secrets-management.md) | Secrets Management | Accepted | 2025-12-04 |
| [ADR-014](ADR-014-structured-personality-prompts.md) | Structured Personality Prompts | Accepted | 2025-12-08 |
| [ADR-015](ADR-015-federated-voting-privacy.md) | Federated Voting Privacy | Accepted | 2025-12-08 |
| [ADR-016](ADR-016-multi-tenant-sqlite-sharding.md) | Multi-Tenant SQLite Sharding | Accepted | 2025-12-10 |
| [ADR-017](ADR-017-sqlite-voting-and-identity.md) | SQLite Voting Storage & UUID Identity | Accepted | 2025-12-11 |
| [ADR-018](ADR-018-async-council-architecture.md) | Async Council Architecture | Accepted | 2025-12-12 |
| [ADR-019](ADR-019-enhanced-admin-dashboard.md) | Enhanced Admin Dashboard | Accepted | 2025-12-13 |
| [ADR-020](ADR-020-e2e-testing-with-playwright.md) | E2E Testing with Playwright | Accepted | 2025-12-13 |
| [ADR-021](ADR-021-observability-standards.md) | Observability Standards | Accepted | 2025-12-17 |
| [ADR-022](ADR-022-resilience-patterns.md) | Resilience Patterns (Retries & Rate Limiting) | Accepted | 2025-12-17 |
| [ADR-023](ADR-023-hybrid-migration-strategy.md) | Hybrid Migration Strategy (Alembic + Custom) | Accepted |
| [ADR-024](ADR-024-strategic-consensus-attribution.md) | Strategic Consensus & Attribution | Proposed | 2025-12-17 |

## Decision Timeline

The ADRs are ordered chronologically based on when the architectural decisions were made:

1. **ADR-001**: Foundation decision - the 3-stage deliberation system
2. **ADR-002**: Core feature - anonymized peer review to prevent bias
3. **ADR-003**: Storage decision - JSON file-based storage (Superseded by ADR-016)
4. **ADR-004**: Integration decision - Router-independent abstraction supporting OpenRouter and LiteLLM
5. **ADR-005**: Enhancement - personality mode for character-based interactions
6. **ADR-006**: Optimization - sliding window for context management
7. **ADR-007**: Configuration - modular personality configuration system
8. **ADR-008**: Admin - admin API and configuration management
9. **ADR-009**: UI - redesign and theme overhaul
10. **ADR-010**: Architecture - multi-user support (Superseded by ADR-016)
11. **ADR-011**: Performance - client-side voting statistics aggregation
12. **ADR-012**: Architecture - multi-tenancy architecture with data isolation
13. **ADR-013**: Security - secrets management with encryption at rest
14. **ADR-014**: Configuration - structured personality prompts with editable sections
15. **ADR-015**: Privacy - federated voting stats with privacy firewalls
16. **ADR-016**: Architecture - multi-tenant sharded SQLite database to fix scalability & isolation
17. **ADR-017**: Identity - SQLite voting storage and UUID identity
18. **ADR-018**: Architecture - async council architecture
19. **ADR-019**: UI - enhanced admin dashboard
20. **ADR-020**: Testing - E2E testing with Playwright
21. **ADR-021**: Observability - standards for errors, logging, and tracing
22. **ADR-022**: Resilience - retries via tenacity and rate limiting via slowapi
23. **ADR-023**: Database - Hybrid migration strategy (Alembic + Migrate-on-Connect)

## Related Documentation

- [Developer Guide](../DEVELOPER_GUIDE.md) - Implementation details and development notes
- [README.md](../../README.md) - Project overview and setup
- [API Documentation](../api/API_SURFACE.md) - API endpoint documentation
- [System Overview](../design/SYSTEM_OVERVIEW.md) - High-level architecture and component overview
