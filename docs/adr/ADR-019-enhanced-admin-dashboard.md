# ADR-019: Enhanced Admin Dashboard and Management Capabilities

**Status**: Accepted
**Date**: 2025-12-11
**Deciders**: Project Team

## Context

The current admin interfaces for Organizations, User Management, and User Settings are primarily "read-only" lists. As the application grows, administrators (both Instance and Organization level) need more active management capabilities to maintain system hygiene, manage user access, and monitor system usage. Specifically, there is a lack of high-level visibility into system health (stats) and granular control over entities (delete, edit role, etc.).

## Decision

We will transition the admin interfaces from passive "viewers" to active "management consoles".

### 1. Unified Admin Dashboard (Instance Admin)

We will introduce a new `AdminDashboard` component as the landing page for Instance Admins.
- **Key Metrics**: Real-time counters for Organizations, Users, Active Conversations (last 24h approximation), and Total Messages.
- **Purpose**: Provide immediate "at-a-glance" system health status.

### 2. Enhanced Management Capabilities

We will expose new backend endpoints to support CRUD operations that were previously unavailable or manual:
- **Organizations**:
    - **Edit**: Allow renaming and modifying API configuration directly.
    - **Delete**: Allow hard deletion of organizations (cascading to users and data).
    - **Stats**: Expose token usage (if tracked) or conversation counts per organization.
- **Users**:
    - **Role Management**: Promote/Demote logic explicitly exposed.
    - **Removal**: Allow Org Admins to remove users from their organization.
    - **Delete Account**: Allow users to self-delete their data (GDPR compliance support).
- **User Settings**:
    - **Password Change**: specific endpoint for self-service password updates.

### 3. Backend Support

We will extend `admin_routes.py` and `users.py` / `organizations.py` to:
- calculate basic statistics on-demand.
- handle "Delete" operations with proper cleanup (cascading deletes for SQLite files where applicable).

## Consequences

### Positive
- **Improved UX**: Admins can resolve issues (e.g., billing, access control) without DB access.
- **Scalability**: Laying the foundation for self-serve management.
- **Visibility**: Better insight into how the platform is being used.

### Negative
- **Performance**: Calculating stats (especially "active conversations") might be expensive if strict "real-time" accuracy is required. We will accept eventual consistency or cached stats if performance degrades.
- **Risk**: "Delete" actions are destructive. We must implement confirmation dialogs and strict permission checks to prevent accidental data loss.
