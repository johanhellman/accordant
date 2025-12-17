# ADR 012: Multi-Tenancy Architecture

## Status

Accepted

## Context

The LLM Council application was originally designed as a single-tenant system. To support multiple organizations running on the same instance with strict data isolation and configuration management, a multi-tenancy architecture was required.

## Decision

We decided to implement a "Shared Database, Separate Schema" approach (logically), adapted for file-based storage.

1. **Organization Entity**: Introduced a top-level `Organization` model.
2. **Data Segregation**:
    - Global data: `users.json`, `organizations.json` (Registry).
    - Org-specific data: Stored in `data/organizations/{org_id}/`.
    - Content: Conversations, Personalities, System Prompts, and Voting History are isolated per organization.
3. **User Association**: Users are linked to a single Organization via `org_id`.
4. **Admin Hierarchy**:
    - **Instance Admin**: Manages organizations and system-wide settings.
    - **Org Admin**: Manages users and settings within their organization.
5. **Migration**: A "Default Organization" was created to house all legacy data, ensuring backward compatibility.

## Consequences

### Positive

- **Isolation**: Strict separation of data between organizations.
- **Scalability**: Supports multiple teams/groups on one deployment.
- **Flexibility**: Each org can have its own personalities and system prompts.

### Negative

- **Complexity**: File system structure is more complex (`data/organizations/{id}/...`).
- **Management**: Requires new admin tools to manage organizations and invites.
