import React, { useState, useEffect, useCallback } from "react";
import { api } from "../api";
import "./LeagueTable.css";
import ContextualHelp from "./ContextualHelp";

const LeagueTable = ({ isInstanceAdmin }) => {
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);
  const [feedbackData, setFeedbackData] = useState(new Map());
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = isInstanceAdmin
        ? await api.getInstanceLeagueTable()
        : await api.getLeagueTable();
      setRankings(data);
    } catch (error) {
      console.error("Failed to load league table:", error);
    } finally {
      setLoading(false);
    }
  }, [isInstanceAdmin]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleRow = async (personalityId) => {
    if (expandedRow === personalityId) {
      setExpandedRow(null);
      return;
    }

    setExpandedRow(personalityId);

    // Fetch feedback if not already cached
    if (!feedbackData.has(personalityId)) {
      try {
        setFeedbackLoading(true);
        // Note: fetchPersonalityFeedback needs ID.
        // For Instance Admin view, we might not have ID or it might be ambiguous.
        // But let's assume standard ID for now.
        // Instance Admin view aggregates by Name usually, so ID might be missing or generic.
        // If ID is missing, we can't fetch feedback (Privacy Firewall acts here too).
        if (!personalityId) return;

        const data = await api.getPersonalityFeedback(personalityId);
        setFeedbackData((prev) => {
          const next = new Map(prev);
          next.set(personalityId, data.summary);
          return next;
        });
      } catch (error) {
        console.error("Failed to fetch feedback:", error);
        setFeedbackData((prev) => {
          const next = new Map(prev);
          next.set(personalityId, "Failed to load feedback.");
          return next;
        });
      } finally {
        setFeedbackLoading(false);
      }
    }
  };

  if (loading) return <div className="league-loading">Loading Rankings...</div>;

  return (
    <div className="league-container">
      <div className="league-header">
        <h3>
          {isInstanceAdmin ? "Global System Rankings" : "Organization League Table"}
          <ContextualHelp topic="ranking" />
        </h3>
        <p className="league-subtitle">
          {isInstanceAdmin
            ? "Aggregated performance of System Personalities across all organizations."
            : "Performance metrics based on local voting history."}
        </p>
      </div>

      <table className="league-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Personality</th>
            <th>Win Rate</th>
            <th>Avg Rank</th>
            <th>Sessions</th>
            <th>Status</th>
            <th style={{ width: "50px" }}></th>
          </tr>
        </thead>
        <tbody>
          {rankings.map((r, index) => (
            <React.Fragment key={index}>
              <tr
                className={`league-row ${expandedRow === r.id ? "expanded" : ""}`}
                onClick={() => toggleRow(r.id)}
              >
                <td className="rank-cell">
                  {index === 0 && <span className="trophy">🏆</span>}#{index + 1}
                </td>
                <td className="name-cell">
                  <span className="p-name">{r.name}</span>
                  {r.id && <span className="p-id-micro">{r.id.slice(0, 6)}</span>}
                </td>
                <td>
                  <div className="league-stat-bar-container">
                    <div className="league-stat-bar" style={{ width: `${r.win_rate}%` }}></div>
                    <span className="league-stat-value">{r.win_rate}%</span>
                  </div>
                </td>
                <td>{r.average_rank}</td>
                <td>{r.sessions}</td>
                <td>
                  {r.is_active ? (
                    <span className="badge active">Active</span>
                  ) : (
                    <span className="badge inactive">Inactive</span>
                  )}
                </td>
                <td>
                  <span className={`chevron ${expandedRow === r.id ? "down" : "right"}`}>›</span>
                </td>
              </tr>
              {expandedRow === r.id && (
                <tr className="feedback-row">
                  <td colSpan="7">
                    <div className="feedback-content">
                      <h4>Community Feedback Analysis</h4>
                      {feedbackLoading && !feedbackData.has(r.id) ? (
                        <div className="spinner-small">Generating analysis...</div>
                      ) : (
                        <div className="feedback-text">
                          {isInstanceAdmin && !r.id
                            ? "Qualitative feedback is local to organizations and not aggregated globally."
                            : feedbackData.get(r.id) || "No feedback available."}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LeagueTable;
