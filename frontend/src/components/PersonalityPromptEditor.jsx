import React from "react";
import "./PromptEditor.css"; // Reuse existing styles or create new ones? Let's reuse for consistency.

const SECTIONS = [
    { id: "identity_and_role", label: "IDENTITY & ROLE" },
    { id: "interpretation_of_questions", label: "INTERPRETATION OF QUESTIONS" },
    { id: "problem_decomposition", label: "PROBLEM DECOMPOSITION" },
    { id: "analysis_and_reasoning", label: "ANALYSIS & REASONING" },
    { id: "differentiation_and_bias", label: "DIFFERENTIATION & BIAS" },
    { id: "tone", label: "TONE" },
];

const ENFORCED_SECTIONS = [
    { key: "stage1_response_structure", title: "RESPONSE STRUCTURE", description: "Enforced by System (Stage 1 Response Structure)" },
    { key: "stage1_meta_structure", title: "META", description: "Enforced by System (Stage 1 Meta Structure)" },
];

function PersonalityPromptEditor({ promptData, systemPrompts = {}, onChange, readOnly = false }) {
    // If promptData is string (legacy), we might want to handle it, but for now assume strict dict from parent logic
    // Parent should handle conversion if needed.

    const handleChange = (section, value) => {
        onChange({
            ...promptData,
            [section]: value,
        });
    };

    return (
        <div className="personality-prompt-editor">
            <div className="info-banner">
                <p>
                    <strong>Structured Personality:</strong> Define the "Soul" of the personality below.
                    The "Body" (Structure & Meta) is enforced by the system.
                </p>
            </div>

            <div className="sections-container">
                {SECTIONS.map((section, index) => (
                    <div key={section.id} className="prompt-section">
                        <div className="section-header">
                            <span className="section-number">{index + 1}</span>
                            <h4>{section.label}</h4>
                        </div>
                        <textarea
                            className="section-input"
                            value={promptData[section.id] || ""}
                            onChange={(e) => handleChange(section.id, e.target.value)}
                            disabled={readOnly}
                            placeholder={`Define ${section.label.toLowerCase()}...`}
                            rows={4}
                        />
                    </div>
                ))}

                {/* Enforced Sections Display */}
                <div className="enforced-sections-divider">
                    <span>System Enforced Sections (Appended Automatically)</span>
                </div>

                {ENFORCED_SECTIONS.map((item, index) => (
                    <div key={item.title} className="prompt-section enforced">
                        <div className="section-header">
                            <span className="section-number">{SECTIONS.length + index + 1}</span>
                            <h4>{item.title}</h4>
                            <span className="badge">System</span>
                        </div>
                        <div className="enforced-description">
                            {item.description}
                        </div>
                        <div className="enforced-content-preview">
                            <pre>{systemPrompts[item.key] || "No content defined in System Prompts."}</pre>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default PersonalityPromptEditor;
