import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./Stage1.css";

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || !Array.isArray(responses) || responses.length === 0) {
    return null;
  }

  const activeResponse = responses.find((_, index) => index === activeTab) || responses[0];

  return (
    <div className="stage stage1">
      <h3 className="stage-title">Stage 1: Individual Responses</h3>

      <div className="tabs">
        {responses.map((resp, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? "active" : ""}`}
            onClick={() => setActiveTab(index)}
          >
            {resp.personality_name || resp.model.split("/")[1] || resp.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="model-name">
          {activeResponse.personality_name ? (
            <>
              <span className="personality-name">{activeResponse.personality_name}</span>
              <span className="model-detail"> ({activeResponse.model})</span>
            </>
          ) : (
            activeResponse.model
          )}
        </div>
        <div className="response-text markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{activeResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
