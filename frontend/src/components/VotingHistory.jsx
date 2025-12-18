import { useState, useEffect, useMemo } from "react";
import { api } from "../api";
import "./VotingHistory.css";

export default function VotingHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // UI State
  const [activeTab, setActiveTab] = useState("history"); // 'history' | 'stats'

  // Filter State
  const [selectedUser, setSelectedUser] = useState("");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [showEnabledOnly, setShowEnabledOnly] = useState(false);
  const [personalities, setPersonalities] = useState([]);

  useEffect(() => {
    loadHistory();
    loadPersonalities();
  }, []);

  const loadPersonalities = async () => {
    try {
      const data = await api.listPersonalities();
      setPersonalities(data);
    } catch (err) {
      console.error("Failed to load personalities:", err);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await api.getVotingHistory();
      // Sort by timestamp descending
      const sorted = data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setHistory(sorted);
    } catch (err) {
      setError("Failed to load voting history");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Derived Data
  const uniqueUsers = useMemo(() => {
    const users = new Set(history.map((h) => h.username).filter(Boolean));
    return Array.from(users).sort();
  }, [history]);

  const filteredHistory = useMemo(() => {
    return history.filter((session) => {
      // User Filter
      if (selectedUser && session.username !== selectedUser) return false;

      // Date Range Filter
      const sessionDate = new Date(session.timestamp);
      if (dateRange.start) {
        const start = new Date(dateRange.start);
        if (sessionDate < start) return false;
      }
      if (dateRange.end) {
        const end = new Date(dateRange.end);
        // Set end date to end of day
        end.setHours(23, 59, 59, 999);
        if (sessionDate > end) return false;
      }

      return true;
    });
  }, [history, selectedUser, dateRange]);

  if (loading) return <div className="loading">Loading history...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="voting-history">
      <div className="vh-header">
        <h2>Global Voting History</h2>

        <div className="vh-controls">
          <div className="vh-tabs">
            <button
              className={`vh-tab ${activeTab === "history" ? "active" : ""}`}
              onClick={() => setActiveTab("history")}
            >
              History List
            </button>
            <button
              className={`vh-tab ${activeTab === "stats" ? "active" : ""}`}
              onClick={() => setActiveTab("stats")}
            >
              Statistics (Heatmap)
            </button>
            <button
              className={`vh-tab ${activeTab === "consensus" ? "active" : ""}`}
              onClick={() => setActiveTab("consensus")}
            >
              Consensus
            </button>
          </div>

          <div className="vh-filters">
            <select
              id="vh-user-filter"
              name="selectedUser"
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="filter-select"
            >
              <option value="">All Users</option>
              {uniqueUsers.map((user) => (
                <option key={user} value={user}>
                  {user}
                </option>
              ))}
            </select>

            <div className="date-filters">
              <input
                id="vh-start-date"
                name="startDate"
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange((prev) => ({ ...prev, start: e.target.value }))}
                className="filter-date"
                placeholder="Start Date"
              />
              <span className="date-sep">to</span>
              <input
                id="vh-end-date"
                name="endDate"
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange((prev) => ({ ...prev, end: e.target.value }))}
                className="filter-date"
                placeholder="End Date"
              />
            </div>
          </div>

          <div className="toggle-filter">
            <label>
              <input
                id="vh-enabled-only"
                name="showEnabledOnly"
                type="checkbox"
                checked={showEnabledOnly}
                onChange={(e) => setShowEnabledOnly(e.target.checked)}
              />
              Show Enabled Only
            </label>
          </div>
        </div>
      </div>

      <div className="vh-content">
        {activeTab === "history" ? (
          <HistoryList history={filteredHistory} />
        ) : activeTab === "stats" ? (
          <VotingHeatmap
            history={filteredHistory}
            showEnabledOnly={showEnabledOnly}
            personalities={personalities}
          />
        ) : (
          <ConsensusDashboard />
        )}
      </div>
    </div>
  );
}

function HistoryList({ history }) {
  if (history.length === 0) {
    return <div className="no-history">No votes found matching filters.</div>;
  }

  return (
    <div className="history-list-container">
      {history.map((session) => (
        <div key={session.id} className="history-card">
          <div className="session-header">
            <div className="session-meta">
              <span className="timestamp">{new Date(session.timestamp).toLocaleString()}</span>
              <span className="user-tag">
                User: <strong>{session.username}</strong>
              </span>
            </div>
            <div className="conversation-info">
              Conversation: {session.conversation_title} (Turn {session.turn_number})
            </div>
          </div>

          <VotesTable votes={session.votes} />
        </div>
      ))}
    </div>
  );
}

function VotesTable({ votes }) {
  // Extract all unique candidates (models being voted ON)
  const allCandidates = new Set();
  if (votes) {
    votes.forEach((vote) => {
      vote.rankings.forEach((r) => allCandidates.add(r.candidate));
    });
  }
  const candidates = Array.from(allCandidates).sort();

  // Extract all voters (personalities casting votes)
  const voters = (votes || [])
    .map((v) => ({
      name: v.voter_personality || v.voter_model,
      rankings: v.rankings,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="votes-table-wrapper">
      <table className="votes-table">
        <thead>
          <tr>
            <th className="corner-cell">Candidate \ Voter</th>
            {voters.map((voter, idx) => (
              <th key={idx} className="voter-header">
                {voter.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr key={candidate}>
              <td className="candidate-cell">{candidate}</td>
              {voters.map((voter, idx) => {
                const rank = voter.rankings.find((r) => r.candidate === candidate)?.rank;
                return (
                  <td key={idx} className={`rank-cell rank-${rank || "none"}`}>
                    {rank ? `#${rank}` : "-"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function VotingHeatmap({ history, showEnabledOnly, personalities }) {
  // Calculate aggregate stats
  const stats = useMemo(() => {
    const matrix = {}; // { voter: { candidate: { sum: 0, count: 0 } } }
    const allVoters = new Set();
    const allCandidates = new Set();

    // Create a set of enabled personality names for filtering
    const enabledNames = new Set(personalities.filter((p) => p.enabled).map((p) => p.name));

    history.forEach((session) => {
      // Safety check for votes array
      if (!session.votes) return;

      session.votes.forEach((vote) => {
        const voter = vote.voter_personality || vote.voter_model;

        // Skip if filtering enabled and voter is not enabled
        if (showEnabledOnly && !enabledNames.has(voter) && personalities.length > 0) {
          return;
        }

        allVoters.add(voter);

        if (!matrix[voter]) matrix[voter] = {};

        vote.rankings.forEach((rank) => {
          const candidate = rank.candidate;

          // Skip if filtering enabled and candidate is not enabled
          if (showEnabledOnly && !enabledNames.has(candidate) && personalities.length > 0) {
            return;
          }

          allCandidates.add(candidate);

          if (!matrix[voter][candidate]) {
            matrix[voter][candidate] = { sum: 0, count: 0 };
          }

          matrix[voter][candidate].sum += rank.rank;
          matrix[voter][candidate].count += 1;
        });
      });
    });

    // Calculate average rank received for each candidate to sort columns
    const candidateScores = {};
    allCandidates.forEach((candidate) => {
      let totalSum = 0;
      let totalCount = 0;
      allVoters.forEach((voter) => {
        const cell = matrix[voter]?.[candidate];
        if (cell) {
          totalSum += cell.sum;
          totalCount += cell.count;
        }
      });
      candidateScores[candidate] = totalCount > 0 ? totalSum / totalCount : 999;
    });

    // Sort candidates alphabetically
    const sortedCandidates = Array.from(allCandidates).sort();

    // Sort voters alphabetically
    const sortedVoters = Array.from(allVoters).sort();

    return {
      matrix,
      voters: sortedVoters,
      candidates: sortedCandidates,
    };
  }, [history, showEnabledOnly, personalities]);

  if (history.length === 0) {
    return <div className="no-history">No data available for statistics.</div>;
  }

  return (
    <div className="heatmap-container">
      <div className="heatmap-legend">
        <h3>Personality vs Personality Affinity</h3>
        <p>
          Values represent the <strong>Average Rank</strong> given by the Voter to the Candidate.
        </p>
        <p>Lower is better (1.0 = Always ranked #1).</p>
      </div>

      <div className="heatmap-wrapper">
        <table className="heatmap-table">
          <thead>
            <tr>
              <th className="axis-label-corner">
                <div className="axis-label-y">Voter (Rows)</div>
                <div className="axis-label-x">Candidate (Cols)</div>
              </th>
              {stats.candidates.map((c) => (
                <th key={c} className="candidate-header">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stats.voters.map((voter) => (
              <tr key={voter}>
                <th className="voter-header">{voter}</th>
                {stats.candidates.map((candidate) => {
                  const cell = stats.matrix[voter]?.[candidate];
                  const avg = cell ? (cell.sum / cell.count).toFixed(1) : "-";
                  const count = cell ? cell.count : 0;

                  // Calculate color intensity (1.0 is best/green, 4.0+ is worst/red)
                  let colorClass = "no-data";
                  if (cell) {
                    const val = parseFloat(avg);
                    if (val <= 1.5)
                      colorClass = "heat-1"; // Best
                    else if (val <= 2.5) colorClass = "heat-2";
                    else if (val <= 3.5) colorClass = "heat-3";
                    else colorClass = "heat-4"; // Worst
                  }

                  return (
                    <td
                      key={candidate}
                      className={`heat-cell ${colorClass}`}
                      title={`${count} votes`}
                    >
                      {avg}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ConsensusDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await api.getConsensusStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to load consensus stats", err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) return <div className="loading">Loading consensus statistics...</div>;
  if (!stats) return <div className="error">Failed to load statistics.</div>;

  // Prepare Chart Data
  const personalityList = Object.entries(stats.by_personality || {})
    .map(([id, data]) => ({ id, ...data }))
    .sort((a, b) => b.total_score - a.total_score);

  const strategyList = Object.entries(stats.by_strategy || {})
    .map(([strat, data]) => ({ name: strat, ...data }))
    .sort((a, b) => b.count - a.count);

  const maxScore = Math.max(...personalityList.map((p) => p.total_score), 1);

  return (
    <div className="consensus-dashboard">
      <div className="dashboard-metrics">
        <div className="metric-card">
          <h3>Total Contribution Events</h3>
          <div className="metric-value">{stats.total_contributions}</div>
        </div>
        <div className="metric-card">
          <h3>Average Confidence Score</h3>
          <div className="metric-value">
            {stats.global_avg_score ? (stats.global_avg_score * 100).toFixed(1) + "%" : "-"}
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-panel">
          <h3>Influence Leaderboard (Total Score)</h3>
          <div className="leaderboard-chart">
            {personalityList.map((p) => (
              <div key={p.id} className="chart-row">
                <span className="row-label">{p.name || "Unknown"}</span>
                <div className="row-bar-container">
                  <div
                    className="row-bar"
                    style={{ width: `${(p.total_score / maxScore) * 100}%` }}
                    title={`Score: ${p.total_score.toFixed(2)}`}
                  ></div>
                </div>
                <span className="row-value">{p.total_score.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-panel">
          <h3>Strategy Effectiveness</h3>
          <table className="strategy-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Count</th>
                <th>Avg Score</th>
              </tr>
            </thead>
            <tbody>
              {strategyList.map((s) => (
                <tr key={s.name}>
                  <td>{s.name}</td>
                  <td>{s.count}</td>
                  <td>{(s.avg_score * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="dashboard-panel full-width">
        <h3>Recent Consensus Activity</h3>
        <table className="activity-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Personality</th>
              <th>Strategy</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {(stats.recent_activity || []).map((event) => (
              <tr key={event.id}>
                <td>{new Date(event.timestamp).toLocaleString()}</td>
                <td>{event.personality_name}</td>
                <td>{event.strategy}</td>
                <td>
                  <span
                    className={`score-badge ${
                      event.score > 0.8 ? "high" : event.score > 0.5 ? "medium" : "low"
                    }`}
                  >
                    {(event.score * 100).toFixed(0)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
