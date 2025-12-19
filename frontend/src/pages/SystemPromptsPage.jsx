import React from "react";
import SystemPromptsEditor from "../components/SystemPromptsEditor";

const SystemPromptsPage = () => {
  // Scope is handled internally by SystemPromptsEditor or defaults to global/org
  // For the top level page, we might want to let user toggle scope or default to "global"
  // Reusing the component for now.
  return (
    <div style={{ padding: "20px" }}>
      <h2>System Prompts</h2>
      <p style={{ marginBottom: "20px", color: "#666" }}>
        Configure global safeguard prompts and directives for all agents.
      </p>
      <SystemPromptsEditor />
    </div>
  );
};

export default SystemPromptsPage;
