import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Stage2.css";

/**
 * Replace anonymous response labels (e.g., "Response A") with actual model names.
 * Used to display readable model names in Stage 2 rankings while preserving
 * the original anonymized evaluation context.
 *
 * @param {string} text - Text containing anonymous labels (e.g., "Response A")
 * @param {Object<string, string>} labelToModel - Mapping from labels to model IDs
 * @returns {string} Text with labels replaced by bold model names
 */
function deAnonymizeText(text, labelToModel) {
  if (!labelToModel) return text;

  let result = text;
  // Replace each "Response X" with the actual model name
  Object.entries(labelToModel).forEach(([label, value]) => {
    // Value can be a string (legacy) or an object { name, id, model }
    let modelName = "";
    if (typeof value === "string") {
      modelName = value;
    } else if (value && typeof value === "object") {
      // Prefer name if available, else model
      modelName = value.name || value.model || "Unknown";
    }

    // If it looks like a model ID (provider/model), split it.
    // If it's a personality name, use it as is.
    const display = modelName.includes("/") ? modelName.split("/")[1] || modelName : modelName;
    result = result.replace(new RegExp(label, "g"), `**${display}**`);
  });
  return result;
}

export default function Stage2({ rankings, labelToModel, aggregateRankings }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!rankings || !Array.isArray(rankings) || rankings.length === 0) {
    return null;
  }

  const activeRank = rankings.find((_, index) => index === activeTab) || rankings[0];

  return (
    <div className="stage stage2">
      <h3 className="stage-title">Stage 2: Peer Rankings</h3>

      <h4>Raw Evaluations</h4>
      <p className="stage-description">
        Each model evaluated all responses (anonymized as Response A, B, C, etc.) and provided
        rankings. Below, model names are shown in <strong>bold</strong> for readability, but the
        original evaluation used anonymous labels.
      </p>

      <div className="tabs">
        {rankings.map((rank, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? "active" : ""}`}
            onClick={() => setActiveTab(index)}
          >
            {rank.personality_name ||
              (rank.model ? rank.model.split("/")[1] || rank.model : "Unknown")}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="ranking-model">
          {activeRank.personality_name ? (
            <>
              <span className="personality-name">{activeRank.personality_name}</span>
              <span className="model-detail"> ({activeRank.model || "Unknown"})</span>
            </>
          ) : (
            activeRank.model || "Unknown"
          )}
        </div>
        <div className="ranking-content markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {deAnonymizeText(activeRank.ranking || "", labelToModel)}
          </ReactMarkdown>
        </div>

        {activeRank.parsed_ranking &&
          Array.isArray(activeRank.parsed_ranking) &&
          activeRank.parsed_ranking.length > 0 && (
            <div className="parsed-ranking">
              <strong>Extracted Ranking:</strong>
              <ol>
                {activeRank.parsed_ranking.map((label, i) => (
                  <li key={i}>
                    {(() => {
                      // eslint-disable-next-line security/detect-object-injection
                      const val = labelToModel && labelToModel[label];
                      if (!val) return label;
                      const name =
                        typeof val === "string" ? val : val.name || val.model || "Unknown";
                      return name.includes("/") ? name.split("/")[1] || name : name;
                    })()}
                  </li>
                ))}
              </ol>
            </div>
          )}
      </div>

      {aggregateRankings && Array.isArray(aggregateRankings) && aggregateRankings.length > 0 && (
        <div className="aggregate-rankings">
          <h4>Aggregate Rankings (Street Cred)</h4>
          <p className="stage-description">
            Combined results across all peer evaluations (lower score is better):
          </p>
          <div className="aggregate-list">
            {aggregateRankings.map((agg, index) => (
              <div key={index} className="aggregate-item">
                <span className="rank-position">#{index + 1}</span>
                <span className="rank-model">
                  {agg.model ? agg.model.split("/")[1] || agg.model : "Unknown"}
                </span>
                <span className="rank-score">
                  Avg: {agg.average_rank ? agg.average_rank.toFixed(2) : "N/A"}
                </span>
                <span className="rank-count">({agg.rankings_count || 0} votes)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
