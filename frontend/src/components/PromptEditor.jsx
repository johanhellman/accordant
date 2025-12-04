import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./PromptEditor.css";

/**
 * PromptEditor Component
 * 
 * A dual-mode editor for editing and previewing system prompts with variable insertion.
 * Supports edit/preview modes and validates required template variables.
 * 
 * @param {Object} props - Component props
 * @param {string} props.value - Current prompt text value
 * @param {Function} props.onChange - Callback when value changes (receives new value)
 * @param {string} props.label - Label text for the editor
 * @param {string} [props.description] - Optional description text
 * @param {Array<string>} [props.requiredVariables=[]] - List of required template variables (e.g., ["{user_query}"])
 * @param {number} [props.rows=10] - Number of rows for the textarea
 */
function PromptEditor({ value, onChange, label, description, requiredVariables = [], rows = 10 }) {
  const [mode, setMode] = useState("edit"); // 'edit' or 'preview'

  // Derive missing variables directly from props to avoid useEffect/setState loops
  // and handle the case where requiredVariables might be a new array reference.
  const missingVars =
    value && requiredVariables.length > 0
      ? requiredVariables.filter((v) => !value.includes(v))
      : [];

  /**
   * Insert a template variable at the current cursor position in the textarea.
   * Preserves cursor position and focus after insertion.
   * 
   * @param {string} variable - Variable string to insert (e.g., "{user_query}")
   */
  const insertVariable = (variable) => {
    const textarea = document.querySelector(`textarea[name="${label}"]`);
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = value;
      const before = text.substring(0, start);
      const after = text.substring(end, text.length);
      const newValue = before + variable + after;

      onChange(newValue);

      // Restore focus and cursor position (next tick)
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + variable.length, start + variable.length);
      }, 0);
    } else {
      // Fallback if ref not working or simple append
      onChange(value + variable);
    }
  };

  return (
    <div className="prompt-editor-container">
      <div className="prompt-editor-header">
        <div>
          <div className="prompt-editor-label">{label}</div>
          {description && <div className="prompt-editor-desc">{description}</div>}
        </div>
        <div className="editor-tabs">
          <button
            className={`editor-tab ${mode === "edit" ? "active" : ""}`}
            onClick={() => setMode("edit")}
          >
            Edit
          </button>
          <button
            className={`editor-tab ${mode === "preview" ? "active" : ""}`}
            onClick={() => setMode("preview")}
          >
            Preview
          </button>
        </div>
      </div>

      {requiredVariables.length > 0 && (
        <div className="prompt-editor-toolbar">
          <span style={{ fontSize: "0.9em", color: "#666", alignSelf: "center" }}>
            Required Variables:
          </span>
          {requiredVariables.map((v) => (
            <button
              key={v}
              className={`variable-tag ${!value.includes(v) ? "missing" : ""}`}
              onClick={() => insertVariable(v)}
              title="Click to insert"
            >
              {v}
            </button>
          ))}
        </div>
      )}

      {mode === "edit" ? (
        <textarea
          name={label}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          className="prompt-textarea"
          placeholder="Enter system prompt here..."
        />
      ) : (
        <div className="markdown-preview">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{value || "*No content*"}</ReactMarkdown>
        </div>
      )}

      {missingVars.length > 0 && (
        <div className="validation-error">
          ⚠️ Missing required variables: {missingVars.join(", ")}
        </div>
      )}
    </div>
  );
}

export default PromptEditor;
