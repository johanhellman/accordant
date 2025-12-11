# ADR-018: Async Council Architecture for Robustness

## Status
Accepted (Phase 1 Implemented)

## Date
2025-12-11

## Context
The "Consulting the Council" process was originally implemented as a synchronous streaming response (SSE) tied directly to the HTTP request lifecycle. 

This architecture had a critical flaw: if the client (browser) disconnected—due to navigation within the SPA, tab closure, or network interruption—the server-side generator function would halt immediately. Because the logic to save the results to the database was placed at the very end of this generator, any interruption resulted in data loss. The computation resources spent on the LLM calls were wasted, and the user count not recover the result.

As the Council process involves multiple LLM calls and can take several minutes, requiring a persistent, fragile connection is poor UX and resource management.

## Decision
We will transition to an **Asynchronous Task Architecture** for the Council process.

### Phase 1: Fire & Forget with Asyncio Task (Immediate)
For the immediate implementation:
1.  **Decoupling**: The Council execution logic (`run_council_streaming`) will be wrapped in a `CouncilManager` service.
2.  **Execution**: When a request comes in, the service will spawn an independent `asyncio.Task` to run the logic.
3.  **State**: The task will communicate progress via an `asyncio.Queue`.
4.  **Streaming**: The HTTP response will consume this Queue.
5.  **Persistence**: The background Task is responsible for saving the final state to the database, independent of whether the Queue being consumed.
6.  **Schema**: We will add `processing_state` (`idle`, `active`, `error`) to the `Conversation` model to track status.

### Phase 2: Full Job Queue & Event Bus (Long Term)
As we scale, we will move to a more durable Job Queue system (e.g., Redis/Celery or SQL-backed jobs) and a global Event Bus (Pub/Sub) to allow clients to "re-subscribe" to the live stream of an ongoing job after a disconnect.

## Consequences
### Positive
*   **Data Safety**: Results are guaranteed to be saved once the process starts, regardless of client state.
*   **Resumability**: Users can navigate away and return to see the finished result (via database fetch).
*   **UX Correctness**: Match user expectation that a "backend job" continues in the background.

### Negative
*   **Complexity**: Introduces state management (Task/Queue synchronization) which is harder to debug than a simple linear generator.
*   **Zombie Tasks**: If the server restarts, in-memory `asyncio.Task`s are lost (Phase 1 limitation). This is acceptable for now but motivates Phase 2.
