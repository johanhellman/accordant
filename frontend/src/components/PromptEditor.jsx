import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Editor from "react-simple-code-editor";
import { highlight, languages } from "prismjs/components/prism-core";
import "prismjs/components/prism-clike";
import "prismjs/components/prism-markup"; // Required by markdown
import "prismjs/components/prism-markdown";
import "prismjs/themes/prism.css"; // Or your preferred theme
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
 * @param {number} [props.rows=10] - Number of rows (approximate for editor height)
 */
function PromptEditor({
  value,
  onChange,
  label,
  description,
  requiredVariables = [],
  rows = 10,
}) {
  const [mode, setMode] = useState("edit"); // 'edit' or 'preview'

  // Derive missing variables directly from props to avoid useEffect/setState loops
  // and handle the case where requiredVariables might be a new array reference.
  const missingVars =
    (value || "") && requiredVariables.length > 0
      ? requiredVariables.filter((v) => !(value || "").includes(v))
      : [];

  /**
   * Insert a template variable at the current cursor position in the editor.
   *
   * @param {string} variable - Variable string to insert (e.g., "{user_query}")
   */
  const insertVariable = (variable) => {
    // With simple-code-editor, we can't easily access cursor pos programmatically cleanly
    // without ref access to the textarea, but standard append is safer/simpler if ref is tricky.
    // However, simple-code-editor exposes a textarea that we can target via class or props.
    // Ideally, we append or specific insertion logic if we had a ref.
    // For now, appending to the end is a safe fallback or simple string manipulation if user focused.

    // Simple approach: Replace selection or append if no selection (requires tracking ref/selection)
    // Given the constraints, appending to the end or cursor requires the editor instance.
    // Let's stick to appending for simplicity unless we refactor to track selection.
    onChange((value || "") + variable);
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
              className={`variable-tag ${!(value || "").includes(v) ? "missing" : ""}`}
              onClick={() => insertVariable(v)}
              title="Click to insert"
            >
              {v}
            </button>
          ))}
        </div>
      )}

      {mode === "edit" ? (
        <div className="editor-wrapper">
          <div className="line-numbers">
            {(value || "").split("\n").map((_, i) => (
              <span key={i}>{i + 1}</span>
            ))}
          </div>
          <Editor
            value={value || ""}
            onValueChange={onChange}
            highlight={(code) => highlight(code, languages.markdown, "markdown")}
            padding={15}
            style={{
              fontFamily: '"Fira code", "Fira Mono", monospace',
              fontSize: 14,
              backgroundColor: "#f5f5f5",
              minHeight: `${rows * 1.5}em`,
              flexGrow: 1,
            }}
            className="rich-editor"
            textareaClassName="focus:outline-none"
          />
        </div>
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
