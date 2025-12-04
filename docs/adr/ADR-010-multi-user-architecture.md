# ADR-010: Multi-User Architecture

## Status
Accepted

## Context
The initial version of LLM Council was designed as a single-user application. All chat history was stored in a shared `data/conversations/` directory, and voting history (Stage 2 rankings) was anonymous and global. As the application evolves, there is a need to support multiple users, each with their own private conversation history, while maintaining a shared set of "Council Personalities" and a global view of voting performance for administrators.

## Decision
We will implement a multi-user architecture with the following key components:

### 1. User Model & Authentication
- **User Entity**: Users are stored in `data/users.json` with `id`, `username`, `password_hash`, and `is_admin` flag.
- **Authentication**: JWT-based authentication using `OAuth2PasswordBearer`.
- **Admin Role**: The first user registered is automatically granted Admin privileges. Subsequent users are standard users. Admins can promote/demote other users.

### 2. Data Isolation
- **Conversations**: Conversations are still stored in `data/conversations/`, but each conversation file now includes a `user_id` field.
- **Access Control**: API endpoints filter conversations by `user_id`. Users can only list and access conversations they created.
- **Personalities**: Personalities remain global and shared across all users.

### 3. Voting History Attribution
- **Attribution**: When a user's council session completes, the voting results (Stage 2) are recorded in `voting_history.json` with the `user_id` of the conversation owner.
- **Global View**: Admins can view the full voting history, enriched with username information, to analyze personality performance across the entire user base.

### 4. Admin API
- **User Management**: New endpoints (`/api/admin/users`) allow admins to list users and manage roles.
- **Voting Data**: New endpoint (`/api/votes`) allows admins to fetch global voting history.

## Consequences

### Positive
- **Privacy**: Users can have private conversations without seeing others' chats.
- **Administration**: Admins can manage the system and view global performance metrics.
- **Scalability**: Sets the foundation for future per-user settings (though personalities are currently shared).

### Negative
- **Complexity**: Adds authentication and authorization logic to all conversation endpoints.
- **Migration**: Existing "legacy" conversations and votes lack `user_id` and are treated as anonymous/legacy data.
