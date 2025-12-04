# ADR-011: Client-Side Voting Statistics Aggregation

## Status
Accepted

## Context
The "Voting History" feature in the Admin UX requires enhancements to provide aggregate statistics (heatmaps) and filtering capabilities. We need to decide where to perform the data aggregation and filtering logic: on the backend (API) or the frontend (Client).

The current dataset size is relatively small (hundreds of voting sessions), and the `GET /api/admin/votes` endpoint already returns the full voting history required for these calculations.

## Decision
We will perform **client-side aggregation and filtering** for the Voting History statistics.

The frontend will:
1. Fetch the full voting history via the existing `GET /api/admin/votes` endpoint.
2. Filter the data in memory based on user selection (User, Date Range).
3. Calculate aggregate statistics (e.g., average rank per personality pair) on the fly.
4. Render the results in a heatmap and filtered list.

## Consequences

### Positive
- **Speed of Implementation**: No backend changes are required, allowing for faster delivery of the UI enhancements.
- **Interactivity**: Filtering and view switching (History vs. Stats) will be instantaneous as no network requests are needed after the initial load.
- **Simplicity**: Keeps the backend logic simple and focused on data persistence.

### Negative
- **Performance at Scale**: As the dataset grows to thousands or tens of thousands of sessions, the initial payload size and client-side processing time may become a bottleneck.
- **Data Duplication**: If other clients (e.g., a mobile app or CLI) need these stats, the logic would need to be duplicated.

## Mitigation
If performance becomes an issue in the future (e.g., >5000 sessions), we will migrate the aggregation logic to a dedicated backend endpoint (e.g., `GET /api/admin/stats`) and implement server-side filtering.
