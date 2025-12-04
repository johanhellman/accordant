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
        <div className="chairman-label">Chairman: {modelName}</div>
        <div className="final-text markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{responseText}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
