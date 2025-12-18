# ADR-025: Consensus Dashboard Metrics

## Status
Accepted

## Context
As the "Council of Personalities" architecture (ADR-001) evolves with the introduction of Consensus Mode ("Stage 3"), it is becoming harder to understand how decisions are reached. Users and developers need visibility into:
1.  **Attribution**: Which personalities are driving the consensus?
2.  **Strategy Effectiveness**: Are "risk-averse" or "creative" strategies more successful?
3.  **System Health**: Is the system successfully reaching consensus over time?

Currently, `VotingHistory` only visualizes Stage 2 (Voting) data. Stage 3 metrics are stored in `consensus_contributions` but not exposed in the UI.

## Decision
We will implement a **Consensus Dashboard** as a new tab in the Voting History interface. This dashboard will visualize data from the `consensus_contributions` table.

### Key Metrics Defined
1.  **Total Contribution Events**: Raw count of consensus participation events.
2.  **Average Confidence Score**: The mean of all contribution `score` values (0.0 - 1.0).
3.  **Influence Score**: The sum of `score` values for a given Personality. This represents "weighted contribution volume".
4.  **Strategy Effectiveness**: Aggregation of `score` by `strategy` type.

### Architecture
- **Backend**: Update `/api/votes` or create `/api/admin/stats/consensus` (chosen path) to return aggregated JSON suitable for charting.
- **Frontend**: A read-only dashboard with a "Leaderboard" (Bar Chart) and "Recent Activity" (Timeline).

## Consequences
### Positive
- Increased transparency into the "black box" of consensus formulation.
- Better feedback loop for tuning personality prompts and strategies.

### Negative
- Additional API load when querying historical statistics.
- UI complexity increases with a third tab in Voting History.

## Compliance
- **Privacy**: No user PII is exposed; metrics are strictly about system agents.
- **Performance**: Analytics queries should be limited or paginated (Dashboard loads 'recent 50' for timeline to mitigate load).
