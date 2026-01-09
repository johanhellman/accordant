import React, { useState } from "react";
import PromptEditor from "./PromptEditor";
import "./PromptEditor.css";

const SECTIONS = [
  { id: "identity_and_role", label: "Identity & Role" },
  { id: "interpretation_of_questions", label: "Interpretation" },
  { id: "problem_decomposition", label: "Decomposition" },
  { id: "analysis_and_reasoning", label: "Reasoning" },
  { id: "differentiation_and_bias", label: "Differentiation" },
  { id: "tone", label: "Tone" },
];

const ENFORCED_SECTIONS = [
  {
    key: "stage1_response_structure",
    title: "RESPONSE STRUCTURE",
    description: "Enforced by System (Stage 1 Response Structure)",
  },
  {
    key: "stage1_meta_structure",
    title: "META",
    description: "Enforced by System (Stage 1 Meta Structure)",
  },
];

const PersonalityPromptEditor = ({ promptData, systemPrompts, onChange }) => {
  const [activeSection, setActiveSection] = useState(SECTIONS[0].id);

  const handleChange = (section, value) => {
    onChange({
      ...promptData,
      [section]: value,
    });
  };

  const isEnforcedTab = activeSection === "system_enforced";
  const currentSectionDef = SECTIONS.find((s) => s.id === activeSection);

  return (
    <div className="personality-prompt-editor">
      <div className="info-banner">
        <p>
          <strong>Structured Personality:</strong> Define the "Soul" of the personality below. The
          "Body" (Structure & Meta) is enforced by the system.
        </p>
      </div>

      <div className="prompt-tabs">
        {SECTIONS.map((section) => (
          <button
            key={section.id}
            className={`prompt-tab-btn ${activeSection === section.id ? "active" : ""}`}
            onClick={() => setActiveSection(section.id)}
          >
            {section.label}
          </button>
        ))}
        <button
          className={`prompt-tab-btn system-tab ${activeSection === "system_enforced" ? "active" : ""}`}
          onClick={() => setActiveSection("system_enforced")}
        >
          🔒 System Enforced
        </button>
      </div>

      <div className="prompt-editor-area">
        {!isEnforcedTab ? (
          <div className="section-editor">
            <PromptEditor
              label={currentSectionDef?.label.toUpperCase()}
              // eslint-disable-next-line security/detect-object-injection
              value={promptData[activeSection] || ""}
              onChange={(val) => handleChange(activeSection, val)}
              rows={15}
              description={`Define ${currentSectionDef?.label.toLowerCase()} settings for this personality.`}
            />
          </div>
        ) : (
          <div className="system-enforced-view">
            <div className="section-header-row">
              <h4>SYSTEM ENFORCED PROMPTS</h4>
            </div>
            <div className="enforced-scroll-container">
              {ENFORCED_SECTIONS.map((item) => (
                <div key={item.key} className="enforced-item">
                  <h5>{item.title}</h5>
                  <p className="enforced-desc">{item.description}</p>
                  <pre className="enforced-code">
                    {systemPrompts[item.key] || "No content defined."}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PersonalityPromptEditor;
