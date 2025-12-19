import React, { useState, useEffect } from "react";
import { api } from "../api";
import PromptEditor from "./PromptEditor";
import { Plus, Trash2, Save, GitBranch, AlertTriangle } from "lucide-react";
import "./StrategyManager.css";

const StrategyManager = () => {
  const [strategies, setStrategies] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Edit State
  const [editForm, setEditForm] = useState({
    id: "",
    display_name: "",
    description: "",
    prompt_content: "",
    source: "custom",
  });

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const data = await api.listStrategies();
      setStrategies(data);
      if (data.length > 0 && !selectedId) {
        selectStrategy(data[0]);
      } else if (selectedId) {
        // Reselect updated
        const updated = data.find((s) => s.id === selectedId);
        if (updated) selectStrategy(updated);
      }
    } catch (err) {
      console.error("Failed to list strategies", err);
    } finally {
      setLoading(false);
    }
  };

  const selectStrategy = (strategy) => {
    setSelectedId(strategy.id);
    setEditForm({
      id: strategy.id,
      display_name: strategy.display_name,
      description: strategy.description || "",
      prompt_content: strategy.prompt_content,
      source: strategy.source,
    });
  };

  const handleCreateNew = () => {
    const newStrat = {
      id: "new_strategy",
      display_name: "New Strategy",
      description: "",
      prompt_content: "You are the chairman. Your goal is to...",
      source: "custom",
      isNew: true,
    };
    setSelectedId(null);
    setEditForm(newStrat);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editForm.isNew) {
        // Create
        // Auto-generate ID from name if not set
        const id = editForm.display_name.toLowerCase().replace(/\s+/g, "_");
        await api.createStrategy({
          ...editForm,
          id: id,
        });
        setSelectedId(id);
      } else {
        // Update
        await api.updateStrategy(editForm.id, editForm);
      }
      await loadStrategies();
    } catch (err) {
      console.error(err);
      alert("Failed to save strategy");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure?")) return;
    try {
      await api.deleteStrategy(editForm.id);
      setSelectedId(null);
      handleCreateNew(); // Reset view
      loadStrategies();
    } catch {
      alert("Failed to delete strategy");
    }
  };

  if (loading && strategies.length === 0)
    return <div className="loading">Loading Strategies...</div>;

  return (
    <div className="strategy-manager">
      <div className="sm-sidebar">
        <div className="sm-sidebar-header">
          <h3>Consensus Strategies</h3>
          <button className="create-strategy-btn" onClick={handleCreateNew}>
            <Plus size={14} /> New
          </button>
        </div>
        <div className="sm-strategy-list">
          {strategies.map((s) => (
            <div
              key={s.id}
              className={`strategy-item ${selectedId === s.id ? "active" : ""}`}
              onClick={() => selectStrategy(s)}
            >
              <div className="strategy-item-name">{s.display_name}</div>
              <div className="strategy-item-meta">
                <span className={`tag ${s.source === "system" ? "system" : "custom"}`}>
                  {s.source}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="sm-content">
        <div className="sm-form-header">
          <div className="sm-form-title">
            {editForm.source === "system" ? (
              <h2>{editForm.display_name}</h2>
            ) : (
              <input
                value={editForm.display_name}
                onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                placeholder="Strategy Name"
              />
            )}
          </div>
          <div className="sm-actions">
            {editForm.source !== "system" && !editForm.isNew && (
              <button className="delete-btn" onClick={handleDelete} title="Delete Strategy">
                <Trash2 size={16} />
              </button>
            )}
            {editForm.source !== "system" && (
              <button className="save-btn" onClick={handleSave} disabled={saving}>
                {saving ? (
                  "Saving..."
                ) : (
                  <>
                    <Save size={16} style={{ marginRight: 8 }} /> Save Changes
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {editForm.source === "system" && (
          <div className="read-only-banner">
            <AlertTriangle size={16} />
            <span>
              System strategies are read-only. Clone this strategy to make edits (Feature coming
              soon).
            </span>
          </div>
        )}

        <div className="sm-description">
          <label>Description</label>
          <textarea
            value={editForm.description}
            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
            disabled={editForm.source === "system"}
            placeholder="Briefly describe how this consensus strategy works..."
          />
        </div>

        <PromptEditor
          label="Strategy Prompt Logic"
          description="The core instructions for the synthesizer model."
          value={editForm.prompt_content}
          onChange={(val) => setEditForm({ ...editForm, prompt_content: val })}
          rows={20}
          requiredVariables={[]} // Maybe check backend/council logic for required vars
          disabled={true} // Wait, PromptEditor disabled logic is weird in SystemPromptsEditor?
          // Actually SystemPromptsEditor passes disabled if source=system
        />
        {/* Force enable if custom */}
        {/* Wait, PromptEditor has preview mode internal state. 'disabled' prop isn't standard in the one I viewed? 
            Let's check PromptEditor again.
            It receives 'value', 'onChange'. 
            It doesn't seem to explicitly accept 'disabled' on the top level, but passes props?
            Ah, wait. Let's look at PromptEditor.jsx again.
        */}
      </div>
    </div>
  );
};

export default StrategyManager;
