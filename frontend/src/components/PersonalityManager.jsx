import { useState, useEffect } from "react";
import { api } from "../api";
import PersonalityPromptEditor from "./PersonalityPromptEditor";
import "./PersonalityManager.css";

import "./PersonalityManager.css";

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

function PersonalityManager() {
  const [personalities, setPersonalities] = useState([]);
  const [models, setModels] = useState([]);
  const [systemPrompts, setSystemPrompts] = useState({});
  const [selectedPersonality, setSelectedPersonality] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Model filtering
  const [providerFilter, setProviderFilter] = useState("all");

  const [scope, setScope] = useState("org"); // 'org' or 'global'
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    checkAdmin();
  }, []);

  const checkAdmin = async () => {
    try {
      const user = await api.getCurrentUser();
      setIsAdmin(user.is_instance_admin);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, [scope]); // Reload when scope changes

  const loadData = async () => {
    setIsLoading(true);
    try {
      const isGlobal = scope === 'global';
      const [pList, mList, sPrompts] = await Promise.all([
        isGlobal ? api.listDefaultPersonalities() : api.listPersonalities(),
        api.listModels(),
        isGlobal ? api.getDefaultSystemPrompts() : api.getSystemPrompts(),
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

    // Strict prompt validation
    if (!p.personality_prompt || Object.keys(p.personality_prompt).length === 0) {
      errors.push("Personality Prompt is required");
    } else {
      const requiredSections = [
        { key: "identity_and_role", label: "Identity & Role" },
        { key: "interpretation_of_questions", label: "Interpretation" },
        { key: "problem_decomposition", label: "Decomposition" },
        { key: "analysis_and_reasoning", label: "Reasoning" },
        { key: "differentiation_and_bias", label: "Differentiation" },
        { key: "tone", label: "Tone" }
      ];

      requiredSections.forEach(section => {
        if (!p.personality_prompt[section.key] || !p.personality_prompt[section.key].trim()) {
          errors.push(`Prompt Section '${section.label}' is required`);
        }
      });
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
      if (scope === 'global') {
        const exists = personalities.some((p) => p.id === pToSave.id);
        if (exists && personalities.find(p => p.id === pToSave.id) === selectedPersonality) {
          // We are editing an existing ITEM (selectedPersonality ref match)
          await api.updateDefaultPersonality(pToSave.id, pToSave);
        } else if (exists) {
          // ID matches someone else? (Backend would catch but safe to check)
          await api.updateDefaultPersonality(pToSave.id, pToSave);
        } else {
          await api.createDefaultPersonality(pToSave);
        }
      } else {
        // Org Mode
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

    const p = personalities.find(item => item.id === id);
    if (scope === 'org' && p && p.source === 'system') {
      alert("You cannot delete a System Personality. You can only disable it.");
      return;
    }

    if (!window.confirm("Are you sure you want to delete this personality?")) return;
    try {
      if (scope === 'global') {
        await api.deleteDefaultPersonality(id);
      } else {
        await api.deletePersonality(id);
      }
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
            <h2>
              {scope === 'global'
                ? (selectedPersonality.id ? "Edit Global Default" : "New Global Default")
                : (selectedPersonality.id ? (selectedPersonality.source === 'system' ? `Customize ${selectedPersonality.name}` : "Edit Personality") : "New Personality")
              }
            </h2>
            <button className="close-btn" onClick={() => setIsEditing(false)}>
              ×
            </button>
          </div>
          {scope === 'global' && (
            <div className="system-notice warning">
              ⚠️ You are editing a Global Default. This will affect ALL organizations.
            </div>
          )}
          {scope === 'org' && selectedPersonality.source === 'system' && (
            <div className="system-notice">
              ℹ️ You are about to customize a System Personality. This will create a local copy that overrides the global default.
            </div>
          )}

          <div className="editor-content">
            <div className="form-row">
              <div className="form-group">
                <label>ID (Unique) *</label>
                <input
                  value={selectedPersonality.id}
                  onChange={(e) =>
                    setSelectedPersonality({ ...selectedPersonality, id: e.target.value })
                  }
                  disabled={scope === 'org' && (personalities.some((p) => p.id === selectedPersonality.id) || selectedPersonality.source === 'system')} // Keep ID locked for system override too
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

            <div className="form-group prompt-editor-wrapper">
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
              {selectedPersonality.source === 'system' ? "Save as Custom Override" : "Save Changes"}
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
        <div className="header-actions">
          {isAdmin && <ScopeSelector scope={scope} onChange={setScope} />}
          <button onClick={handleCreate} className="primary">
            + Add Personality
          </button>
        </div>
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
              <div className="badge-group">
                <span className="id-badge">{p.id}</span>
                {p.source === 'system' && <span className="source-badge system" title="System Default">🔒 System</span>}
                {p.source === 'custom' && <span className="source-badge custom" title="Custom Override">✏️ Custom</span>}
              </div>
              <button
                className="icon-btn delete-btn"
                onClick={(e) => handleDelete(p.id, e)}
                title={p.source === 'system' ? "Cannot delete System Personality" : "Delete"}
                disabled={p.source === 'system'}
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
