import { useState, useEffect } from "react";
import { api } from "../api";
import PromptEditor from "./PromptEditor";
import ModelSelector from "./ModelSelector";
import "./SystemPromptsEditor.css";

function SystemPromptsEditor() {
  const [config, setConfig] = useState(null);
  const [models, setModels] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [c, mList] = await Promise.all([api.getSystemPrompts(), api.listModels()]);
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
      await api.updateSystemPrompts(config);
      alert("System prompts updated successfully!");
    } catch (error) {
      alert("Failed to update: " + error.message);
    } finally {
      setIsSaving(false);
    }
  };


  if (isLoading) return <div className="loading">Loading configuration...</div>;

  return (
    <div className="system-prompts-editor">
      <div className="header">
        <div>
          <h2>System Prompts & Configuration</h2>
          <p className="subtitle">Configure global prompts and special council roles.</p>
        </div>
        <button onClick={handleSave} className="primary" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Configuration"}
        </button>
      </div>

      <div className="editor-layout">
        {/* 1. Base System Prompt */}
        <div className="section">
          <div className="section-header">
            <h3>Base System Prompt</h3>
            <p className="section-desc">Shared instructions for all council members.</p>
          </div>
          <div className="form-group">
            <PromptEditor
              label="Base System Prompt"
              value={config.base_system_prompt}
              onChange={(val) => setConfig({ ...config, base_system_prompt: val })}
              rows={8}
            />
          </div>
        </div>

        {/* 2. Voting Instructions (Ranking Prompt) */}
        <div className="section">
          <div className="section-header">
            <h3>Voting Instructions (Stage 2)</h3>
            <p className="section-desc">Instructions and model used to rank peers.</p>
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
              <PromptEditor
                label="Ranking Prompt"
                description="Used in Stage 2 for peer evaluation."
                value={config.ranking.prompt}
                onChange={(val) =>
                  setConfig({
                    ...config,
                    ranking: { ...config.ranking, prompt: val },
                  })
                }
                rows={12}
                requiredVariables={["{user_query}", "{responses_text}", "{peer_text}"]}
              />
            </div>
          </div>
        </div>

        {/* 3. Chairman Configuration */}
        <div className="section">
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
              <PromptEditor
                label="Chairman Prompt"
                value={config.chairman.prompt}
                onChange={(val) =>
                  setConfig({
                    ...config,
                    chairman: { ...config.chairman, prompt: val },
                  })
                }
                rows={12}
                requiredVariables={["{user_query}", "{stage1_text}", "{voting_details_text}"]}
              />
            </div>
          </div>
        </div>

        {/* 4. Title Generation Configuration */}
        <div className="section">
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
              <PromptEditor
                label="Title Prompt"
                value={config.title_generation.prompt}
                onChange={(val) =>
                  setConfig({
                    ...config,
                    title_generation: { ...config.title_generation, prompt: val },
                  })
                }
                rows={4}
                requiredVariables={["{user_query}"]}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemPromptsEditor;
