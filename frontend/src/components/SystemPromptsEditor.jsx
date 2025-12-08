import { useState, useEffect } from "react";
import { api } from "../api";
import PromptEditor from "./PromptEditor";
import ModelSelector from "./ModelSelector";
import { FileText, Vote, Gavel, PenTool, GitMerge } from "lucide-react";
import "./SystemPromptsEditor.css";

const SECTIONS = [
  { id: "base", label: "Base System Prompt (Global)", icon: FileText },
  { id: "enforced", label: "Enforced Structure (Stage 1)", icon: FileText },
  { id: "ranking", label: "Voting Instructions (Stage 2)", icon: Vote },
  { id: "chairman", label: "Chairman Configuration (Stage 3)", icon: Gavel },
  { id: "evolution", label: "Evolution (Combining)", icon: GitMerge },
  { id: "title", label: "Title Generation (Utility)", icon: PenTool },
];



const InheritanceToggle = ({ label, configValue, onToggle }) => {
  return (
    <div className="inheritance-toggle">
      <label className="toggle-label">
        <input
          type="checkbox"
          checked={configValue.is_default}
          onChange={(e) => onToggle(e.target.checked)}
        />
        <span className="toggle-text">Inherit {label} from Defaults</span>
      </label>
      {configValue.is_default && <span className="badge badge-default">Inherited</span>}
      {!configValue.is_default && <span className="badge badge-custom">Custom Override</span>}
    </div>
  );
};

const ScopeSelector = ({ scope, onChange }) => (
  <div className="scope-selector">
    <label>Editing Scope:</label>
    <div className="scope-buttons">
      <button
        className={scope === 'org' ? 'active' : ''}
        onClick={() => onChange('org')}
      >
        🏢 Organization
      </button>
      <button
        className={scope === 'global' ? 'active' : ''}
        onClick={() => onChange('global')}
      >
        🌍 Global Defaults
      </button>
    </div>
  </div>
);

function SystemPromptsEditor() {
  const [config, setConfig] = useState(null);
  const [models, setModels] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeSection, setActiveSection] = useState("base");

  const [scope, setScope] = useState("org"); // 'org' or 'global'
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    checkAdmin();
  }, []);

  useEffect(() => {
    loadData();
  }, [scope]); // Reload when scope changes

  const checkAdmin = async () => {
    try {
      const user = await api.getCurrentUser();
      setIsAdmin(user.is_instance_admin);
    } catch (e) {
      console.error(e);
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [c, mList] = await Promise.all([
        scope === 'global' ? api.getDefaultSystemPrompts() : api.getSystemPrompts(),
        api.listModels()
      ]);
      setConfig(c);
      setModels(mList.sort((a, b) => (a.name || a.id).localeCompare(b.name || b.id)));
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (scope === 'global') {
        await api.updateDefaultSystemPrompts(config);
        alert("Global defaults updated successfully!");
      } else {
        await api.updateSystemPrompts(config);
        alert("Organization configuration updated successfully!");
      }
    } catch (error) {
      alert("Failed to update: " + error.message);
    } finally {
      setIsSaving(false);
    }
  };


  if (isLoading) return <div className="loading">Loading configuration...</div>;

  const renderContent = () => {
    switch (activeSection) {
      case "base":
        return (
          <div className="section-content fade-in">
            <div className="section-header">
              <h3>Base System Prompt</h3>
              <p className="section-desc">Shared instructions for all council members.</p>
            </div>

            <div className="form-group">
              {scope === 'org' && (
                <InheritanceToggle
                  label="Base System Prompt"
                  configValue={config.base_system_prompt}
                  onToggle={(newIsDefault) => {
                    setConfig({
                      ...config,
                      base_system_prompt: { ...config.base_system_prompt, is_default: newIsDefault }
                    });
                  }}
                />
              )}
              <PromptEditor
                label="Base System Prompt"
                value={config.base_system_prompt.value}
                onChange={(val) => setConfig({
                  ...config,
                  base_system_prompt: { ...config.base_system_prompt, value: val, is_default: false }
                })}
                rows={12}
                disabled={scope === 'org' && config.base_system_prompt.is_default}
              />
            </div>
            <div className="actions">
              <button onClick={handleSave} className="primary" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        );
      case "ranking":
        return (
          <div className="section-content fade-in">
            <div className="section-header">
              <h3>Voting Instructions (Stage 2)</h3>
              <p className="section-desc">
                Instructions for the model on how to evaluate peers.
              </p>
            </div>
            <div className="config-group">
              <ModelSelector
                label="Ranking Model"
                value={config.ranking.model}
                models={models}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    ranking: { ...config.ranking, model: e.target.value },
                  })
                }
                effectiveModel={config.ranking.effective_model}
              />

              <div className="form-group">
                <label>Enforced Context (Prepend)</label>
                <div className="enforced-text">
                  You are evaluating different responses to the following question:<br /><br />
                  Question: &#123;user_query&#125;<br /><br />
                  Here are the responses from &#123;peer_text&#125;:<br /><br />
                  &#123;responses_text&#125;
                </div>
              </div>

              <div className="form-group">
                {scope === 'org' && (
                  <InheritanceToggle
                    label="Ranking Instructions"
                    configValue={config.ranking.prompt}
                    onToggle={(newIsDefault) => {
                      setConfig({
                        ...config,
                        ranking: { ...config.ranking, prompt: { ...config.ranking.prompt, is_default: newIsDefault } }
                      });
                    }}
                  />
                )}
                <PromptEditor
                  label="Ranking Instructions"
                  description="Custom instructions for evaluation (e.g., 'Focus on creativity')."
                  value={config.ranking.prompt.value}
                  onChange={(val) =>
                    setConfig({
                      ...config,
                      ranking: { ...config.ranking, prompt: { ...config.ranking.prompt, value: val, is_default: false } },
                    })
                  }
                  rows={8}
                  disabled={scope === 'org' && config.ranking.prompt.is_default}
                />
              </div>

              <div className="form-group">
                <label>Enforced Output Format (Append)</label>
                <div className="enforced-text">
                  IMPORTANT: Your response MUST be formatted EXACTLY as follows:
                  <br />
                  - Start with the line "&#123;FINAL_RANKING_MARKER&#125;" (all caps, with colon)
                  <br />
                  <br />
                  For each response being evaluated, provide a structured analysis:
                  <br />
                  &gt; 1. **Strengths**: What does this response do well?
                  <br />
                  &gt; 2. **Weaknesses**: What is missing or incorrect?
                  <br />
                  <br />
                  End with a final ranking of the responses from best to worst.
                  <br />
                  - The ranking MUST use the format: "1. &#123;RESPONSE_LABEL_PREFIX&#125;X" (e.g.,
                  "1. &#123;RESPONSE_LABEL_PREFIX&#125;A")
                  <br />
                  - Each entry must be on a new line
                  <br />
                  <br />
                  Now provide your evaluation and ranking:
                </div>
              </div>
            </div>
            <div className="actions">
              <button onClick={handleSave} className="primary" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        );
      case "chairman":
        return (
          <div className="section-content fade-in">
            <div className="section-header">
              <h3>Chairman Configuration</h3>
              <p className="section-desc">Controls the final synthesis (Stage 3).</p>
            </div>

            <div className="config-group">
              <ModelSelector
                label="Chairman Model"
                value={config.chairman.model}
                models={models}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    chairman: { ...config.chairman, model: e.target.value },
                  })
                }
                effectiveModel={config.chairman.effective_model}
              />

              <div className="form-group">
                {scope === 'org' && (
                  <InheritanceToggle
                    label="Chairman Prompt"
                    configValue={config.chairman.prompt}
                    onToggle={(newIsDefault) => {
                      setConfig({
                        ...config,
                        chairman: { ...config.chairman, prompt: { ...config.chairman.prompt, is_default: newIsDefault } }
                      });
                    }}
                  />
                )}
                <PromptEditor
                  label="Chairman Prompt"
                  value={config.chairman.prompt.value}
                  onChange={(val) =>
                    setConfig({
                      ...config,
                      chairman: { ...config.chairman, prompt: { ...config.chairman.prompt, value: val, is_default: false } },
                    })
                  }
                  rows={12}
                  requiredVariables={["{user_query}", "{stage1_text}", "{voting_details_text}"]}
                  disabled={scope === 'org' && config.chairman.prompt.is_default}
                />
              </div>
            </div>
            <div className="actions">
              <button onClick={handleSave} className="primary" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        );

      case "enforced":
        return (
          <div className="section-content fade-in">
            <div className="section-header">
              <h3>Enforced Response Structure (Stage 1)</h3>
              <p className="section-desc">
                These instructions are appended to EVERY personality prompt to ensure consistent output format.
              </p>
            </div>

            <div className="config-group">
              <div className="form-group">
                {scope === 'org' && (
                  <InheritanceToggle
                    label="Response Structure"
                    configValue={config.stage1_response_structure}
                    onToggle={(newIsDefault) => {
                      setConfig({
                        ...config,
                        stage1_response_structure: { ...config.stage1_response_structure, is_default: newIsDefault }
                      });
                    }}
                  />
                )}
                <PromptEditor
                  label="Response Structure"
                  description="Defines the required headings (e.g., Analysis, Standpoint)"
                  value={config.stage1_response_structure.value || ""}
                  onChange={(val) =>
                    setConfig({
                      ...config,
                      stage1_response_structure: { ...config.stage1_response_structure, value: val, is_default: false },
                    })
                  }
                  rows={8}
                  disabled={scope === 'org' && config.stage1_response_structure.is_default}
                />
              </div>

              <div className="form-group">
                {scope === 'org' && (
                  <InheritanceToggle
                    label="Meta Structure"
                    configValue={config.stage1_meta_structure}
                    onToggle={(newIsDefault) => {
                      setConfig({
                        ...config,
                        stage1_meta_structure: { ...config.stage1_meta_structure, is_default: newIsDefault }
                      });
                    }}
                  />
                )}
                <PromptEditor
                  label="Meta Structure"
                  description="Defines the required metadata block (e.g., Confidence Score)"
                  value={config.stage1_meta_structure.value || ""}
                  onChange={(val) =>
                    setConfig({
                      ...config,
                      stage1_meta_structure: { ...config.stage1_meta_structure, value: val, is_default: false },
                    })
                  }
                  rows={6}
                  disabled={scope === 'org' && config.stage1_meta_structure.is_default}
                />
              </div>
            </div>
            <div className="actions">
              <button onClick={handleSave} className="primary" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        );
      case "title":
        return (
          <div className="section-content fade-in">
            <div className="section-header">
              <h3>Title Generation</h3>
              <p className="section-desc">Controls how conversation titles are generated.</p>
            </div>

            <div className="config-group">
              <ModelSelector
                label="Title Generation Model"
                value={config.title_generation.model}
                models={models}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    title_generation: { ...config.title_generation, model: e.target.value },
                  })
                }
                effectiveModel={config.title_generation.effective_model}
              />

              <div className="form-group">
                {scope === 'org' && (
                  <InheritanceToggle
                    label="Title Prompt"
                    configValue={config.title_generation.prompt}
                    onToggle={(newIsDefault) => {
                      setConfig({
                        ...config,
                        title_generation: { ...config.title_generation, prompt: { ...config.title_generation.prompt, is_default: newIsDefault } }
                      });
                    }}
                  />
                )}
                <PromptEditor
                  label="Title Prompt"
                  value={config.title_generation.prompt.value}
                  onChange={(val) =>
                    setConfig({
                      ...config,
                      title_generation: { ...config.title_generation, prompt: { ...config.title_generation.prompt, value: val, is_default: false } },
                    })
                  }
                  rows={4}
                  requiredVariables={["{user_query}"]}
                  disabled={scope === 'org' && config.title_generation.prompt.is_default}
                />
              </div>
            </div>
            <div className="actions">
              <button onClick={handleSave} className="primary" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        );
      case "evolution":
        return (
          <div className="section-content fade-in">
            <div className="section-header">
              <h3>Evolution Instructions</h3>
              <p className="section-desc">
                Instructions for the architect model on how to combine personalities.
              </p>
            </div>

            <div className="config-group">
              <div className="form-group">
                {scope === 'org' && (
                  <InheritanceToggle
                    label="Evolution Prompt"
                    configValue={config.evolution_prompt}
                    onToggle={(newIsDefault) => {
                      setConfig({
                        ...config,
                        evolution_prompt: { ...config.evolution_prompt, is_default: newIsDefault }
                      });
                    }}
                  />
                )}
                <PromptEditor
                  label="Evolution Prompt"
                  value={config.evolution_prompt.value}
                  onChange={(val) =>
                    setConfig({
                      ...config,
                      evolution_prompt: { ...config.evolution_prompt, value: val, is_default: false },
                    })
                  }
                  rows={16}
                  requiredVariables={["{parent_count}", "{offspring_name}", "{parent_data}"]}
                  disabled={scope === 'org' && config.evolution_prompt.is_default}
                />
              </div>
            </div>
            <div className="actions">
              <button onClick={handleSave} className="primary" disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="system-prompts-editor">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Configuration</h2>
          {isAdmin && <ScopeSelector scope={scope} onChange={setScope} />}
        </div>
        <nav className="sidebar-nav">
          {SECTIONS.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                className={`nav-item ${activeSection === section.id ? "active" : ""}`}
                onClick={() => setActiveSection(section.id)}
              >
                <Icon size={18} />
                <span>{section.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
      <div className={`main-content ${scope === 'global' ? 'global-scope' : ''}`}>
        {scope === 'global' && (
          <div className="global-scope-banner">
            ⚠️ You are editing Global Defaults. Changes will affect ALL organizations that inherit these settings.
          </div>
        )}
        {renderContent()}
      </div>
    </div>
  );
}

export default SystemPromptsEditor;
