import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Stage3.css";

export default function Stage3({ finalResponse }) {
  if (!finalResponse || typeof finalResponse !== "object") {
    return null;
  }

  const modelName = finalResponse.model
    ? finalResponse.model.split("/")[1] || finalResponse.model
    : "Unknown";
  const responseText = finalResponse.response || "";

  return (
    <div className="stage stage3">
      <h3 className="stage-title">Stage 3: Final Council Answer</h3>
      <div className="final-response">
        <div className="chairman-label">
          {finalResponse.consensus_contributions
            ? "Synthesizer: Strategic Consensus"
            : `Chairman: ${modelName}`}
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{responseText}</ReactMarkdown>
        </div>

        {finalResponse.consensus_contributions &&
          finalResponse.consensus_contributions.length > 0 && (
            <div className="attribution-section">
              <h4>
                Consensus Strategy:{" "}
                {finalResponse.consensus_contributions[0].strategy || "Balanced"}
              </h4>
              <div className="attribution-grid">
                {finalResponse.consensus_contributions.map((c, idx) => (
                  <div key={idx} className="attribution-card">
                    <div className="attr-header">
                      <span className="attr-id">{c.id}</span>
                      <span className="attr-weight" style={{ width: 60 }}>
                        {/* Simple bar or percentage? Just text for now */}
                        {(c.weight * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="attr-reason">{c.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
      </div>
    </div>
  );
}
