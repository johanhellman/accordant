import { useState, useEffect } from "react";
import { api } from "../api";
import PersonalityPromptEditor from "./PersonalityPromptEditor";
import "./PersonalityManager.css";

function PersonalityManager() {
  const [personalities, setPersonalities] = useState([]);
  const [models, setModels] = useState([]);
  const [systemPrompts, setSystemPrompts] = useState({});
  const [selectedPersonality, setSelectedPersonality] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Model filtering
  const [providerFilter, setProviderFilter] = useState("all");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [pList, mList, sPrompts] = await Promise.all([
        api.listPersonalities(),
        api.listModels(),
        api.getSystemPrompts(),
      ]);
      setPersonalities(pList);
      setModels(mList);
      setSystemPrompts(sPrompts);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (p) => {
    // Ensure prompt is a dict for editor, even if backend sends string legacy
    // (Though backend should handle migration, let's be safe for UI state)
    let safePrompt = p.personality_prompt;
    if (typeof safePrompt === "string") {
      safePrompt = { "IDENTITY & ROLE": safePrompt };
    } else if (!safePrompt) {
      safePrompt = {};
    }

    setSelectedPersonality({
      ...p,
      personality_prompt: safePrompt,
      // Remove UI legacy fallback injection if we want to stop using it
    });
    setIsEditing(true);
  };

  const handleCreate = () => {
    setSelectedPersonality({
      id: "",
      name: "",
      description: "",
      model: "",
      temperature: 0.7,
      enabled: true,
      personality_prompt: {},
      // UI dict is kept minimal or effectively empty for now as requested
      ui: {},
    });
    setIsEditing(true);
  };

  const validateForm = (p) => {
    const errors = [];
    if (!p.id) errors.push("ID is required");
    if (!p.name) errors.push("Name is required");
    if (!p.description) errors.push("Description is required");
    if (!p.model) errors.push("Model is required");
    if (!p.personality_prompt) errors.push("Personality Prompt is required");
    // Simple check if dict is empty
    if (typeof p.personality_prompt === 'object' && Object.keys(p.personality_prompt).length === 0) {
      // Technically can be valid if user wants empty, but let's encourage at least Identity
      // Let's not strict enforce Identity for now, but general 'required' check on backend might fail
    }
    if (p.temperature === undefined || p.temperature === null || p.temperature === "")
      errors.push("Temperature is required");
    return errors;
  };

  const handleSave = async () => {
    // Ensure UI object structure
    const pToSave = {
      ...selectedPersonality,
      temperature: parseFloat(selectedPersonality.temperature),
      // No UI processing needed anymore
    };

    const errors = validateForm(pToSave);
    if (errors.length > 0) {
      alert("Please fix the following errors:\n- " + errors.join("\n- "));
      return;
    }

    try {
      if (personalities.find((p) => p.id === pToSave.id && p !== selectedPersonality)) {
        // Update existing
        await api.updatePersonality(pToSave.id, pToSave);
      } else {
        // Create new (check if ID exists first in list to determine if it's an update or create logic)
        const exists = personalities.some((p) => p.id === pToSave.id);
        if (exists) {
          await api.updatePersonality(pToSave.id, pToSave);
        } else {
          await api.createPersonality(pToSave);
        }
      }
      setIsEditing(false);
      loadData();
    } catch (error) {
      alert("Failed to save personality: " + error.message);
    }
  };

  const handleToggleEnabled = async (p, e) => {
    e.stopPropagation(); // Prevent card click
    const updated = { ...p, enabled: !p.enabled };
    try {
      // Optimistic update
      setPersonalities(personalities.map((item) => (item.id === p.id ? updated : item)));
      await api.updatePersonality(p.id, updated);
    } catch (error) {
      console.error("Failed to toggle:", error);
      // Revert on error
      loadData();
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this personality?")) return;
    try {
      await api.deletePersonality(id);
      loadData();
    } catch (error) {
      console.error("Failed to delete:", error);
    }
  };

  const providers = ["all", ...new Set(models.map((m) => m.provider))];
  const filteredModels = (
    providerFilter === "all" ? models : models.filter((m) => m.provider === providerFilter)
  ).sort((a, b) => (a.name || a.id).localeCompare(b.name || b.id));

  if (isLoading) return <div className="loading">Loading personalities...</div>;

  if (isEditing) {
    return (
      <div className="personality-editor-container">
        <div className="personality-editor">
          <div className="editor-header">
            <h2>{selectedPersonality.id ? "Edit Personality" : "New Personality"}</h2>
            <button className="close-btn" onClick={() => setIsEditing(false)}>
              ×
            </button>
          </div>

          <div className="editor-content">
            <div className="form-row">
              <div className="form-group">
                <label>ID (Unique) *</label>
                <input
                  value={selectedPersonality.id}
                  onChange={(e) =>
                    setSelectedPersonality({ ...selectedPersonality, id: e.target.value })
                  }
                  disabled={personalities.some((p) => p.id === selectedPersonality.id)}
                  placeholder="e.g., gpt_expert"
                />
              </div>
              <div className="form-group">
                <label>Name *</label>
                <input
                  value={selectedPersonality.name}
                  onChange={(e) =>
                    setSelectedPersonality({ ...selectedPersonality, name: e.target.value })
                  }
                  placeholder="Display Name"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Description *</label>
              <input
                value={selectedPersonality.description}
                onChange={(e) =>
                  setSelectedPersonality({ ...selectedPersonality, description: e.target.value })
                }
                placeholder="Short description of role"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Model *</label>
                <div className="model-selector">
                  <select
                    value={providerFilter}
                    onChange={(e) => setProviderFilter(e.target.value)}
                    className="provider-select"
                  >
                    {providers.map((p) => (
                      <option key={p} value={p}>
                        {p.toUpperCase()}
                      </option>
                    ))}
                  </select>
                  <select
                    value={selectedPersonality.model}
                    onChange={(e) =>
                      setSelectedPersonality({ ...selectedPersonality, model: e.target.value })
                    }
                    className="model-select"
                  >
                    <option value="">Select a model...</option>
                    {filteredModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.id})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Temperature *</label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={selectedPersonality.temperature}
                  onChange={(e) =>
                    setSelectedPersonality({ ...selectedPersonality, temperature: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Removed UI Fields (Avatar, Color, Group, Tags) */}

            <div className="form-group">
              <PersonalityPromptEditor
                promptData={selectedPersonality.personality_prompt}
                systemPrompts={systemPrompts}
                onChange={(newData) =>
                  setSelectedPersonality({
                    ...selectedPersonality,
                    personality_prompt: newData,
                  })
                }
              />
            </div>
          </div>

          <div className="editor-actions">
            <button onClick={() => setIsEditing(false)} className="secondary">
              Cancel
            </button>
            <button onClick={handleSave} className="primary">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="personality-manager">
      <div className="header">
        <div>
          <h2>Personalities</h2>
          <p className="subtitle">Manage the council members and their behaviors.</p>
        </div>
        <button onClick={handleCreate} className="primary">
          + Add Personality
        </button>
      </div>

      <div className="personality-grid">
        {personalities.map((p) => (
          <div
            key={p.id}
            className={`personality-card ${!p.enabled ? "disabled" : ""}`}
            onClick={() => handleEdit(p)}
          >
            <div className="card-top">
              <div className="card-header">
                <h3>{p.name}</h3>
                <div
                  className="toggle-switch"
                  onClick={(e) => handleToggleEnabled(p, e)}
                  title={p.enabled ? "Disable" : "Enable"}
                >
                  <input type="checkbox" checked={p.enabled} readOnly />
                  <span className="slider"></span>
                </div>
              </div>
              <span className="model-badge">{p.model}</span>
            </div>

            <p className="description">{p.description}</p>

            <div className="card-footer">
              <span className="id-badge">{p.id}</span>
              <button
                className="icon-btn delete-btn"
                onClick={(e) => handleDelete(p.id, e)}
                title="Delete"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PersonalityManager;
