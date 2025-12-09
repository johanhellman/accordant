import React, { useState, useEffect } from 'react';
import { api } from '../api';
import './PersonalityManager.css';
import PersonalityEditor from './PersonalityEditor';
import SystemPromptsEditor from './SystemPromptsEditor';
import LeagueTable from './LeagueTable';
import EvolutionPanel from './EvolutionPanel';
import VotingHistory from './VotingHistory';

const PersonalityManager = () => {
  const [personalities, setPersonalities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('personalities'); // personalities, league, evolution, system-prompts
  const [activePersonality, setActivePersonality] = useState(null);
  const [isInstanceAdmin, setIsInstanceAdmin] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // New Personality State
  const [isCreating, setIsCreating] = useState(false);
  const [newPersonality, setNewPersonality] = useState({
    name: '',
    description: '',
    model: '',
    temperature: 0.7,
    personality_prompt: ''
  });

  useEffect(() => {
    loadData();
    checkUserRole();
  }, []);

  const checkUserRole = async () => {
    try {
      const user = await api.getCurrentUser();
      setIsInstanceAdmin(user.is_instance_admin);
    } catch (e) {
      console.error("Failed to check user role", e);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.listPersonalities();
      setPersonalities(data);
      setError(null);
    } catch (err) {
      setError('Failed to load personalities');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      if (!newPersonality.name || !newPersonality.model) {
        alert("Name and Model are required.");
        return;
      }

      const id = newPersonality.name.toLowerCase().replace(/\s+/g, '-');
      if (personalities.some(p => p.id === id)) {
        alert("A personality with this name (ID) already exists.");
        return;
      }

      await api.createPersonality({
        ...newPersonality,
        id,
        personality_prompt: typeof newPersonality.personality_prompt === 'string'
          ? newPersonality.personality_prompt
          : {}
      });

      setIsCreating(false);
      setNewPersonality({ name: '', description: '', model: '', temperature: 0.7, personality_prompt: '' });
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this personality?')) return;
    try {
      await api.deletePersonality(id);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUseTemplate = (template) => {
    setNewPersonality({
      ...newPersonality,
      name: template.name,
      description: template.description,
      personality_prompt: template.prompt
    });
  };

  const openEditor = (personality) => {
    setActivePersonality(personality);
    setIsEditing(true);
  };

  const closeEditor = () => {
    setIsEditing(false);
    setActivePersonality(null);
    loadData();
  };

  if (loading && !isEditing) return <div className="loading">Loading Personalities...</div>;

  // Render Editor Mode
  if (isEditing && activePersonality) {
    return (
      <div className="manager-container">
        <button className="back-btn" onClick={closeEditor}>← Back to List</button>
        <PersonalityEditor
          personalityId={activePersonality.id}
          onSave={closeEditor}
          onCancel={closeEditor}
        />
      </div>
    );
  }

  // Render Tabbed View
  return (
    <div className="manager-container">
      <div className="manager-header">
        <h2>Council Personalities</h2>

      </div>

      <div className="manager-tabs">
        <button
          className={`tab-btn ${activeTab === 'personalities' ? 'active' : ''}`}
          onClick={() => setActiveTab('personalities')}
        >
          Personalities
        </button>
        <button
          className={`tab-btn ${activeTab === 'league' ? 'active' : ''}`}
          onClick={() => setActiveTab('league')}
        >
          League Table
        </button>
        <button
          className={`tab-btn ${activeTab === 'evolution' ? 'active' : ''}`}
          onClick={() => setActiveTab('evolution')}
        >
          Evolution
        </button>
        <button
          className={`tab-btn ${activeTab === 'system-prompts' ? 'active' : ''}`}
          onClick={() => setActiveTab('system-prompts')}
        >
          System Prompts
        </button>
        <button
          className={`tab-btn ${activeTab === 'voting-history' ? 'active' : ''}`}
          onClick={() => setActiveTab('voting-history')}
        >
          Voting History
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="tab-content">
        {activeTab === 'personalities' && (
          <div className="personalities-grid">
            <div className="grid-actions">
              <button className="create-btn" onClick={() => setIsCreating(true)}>
                + Add Personality
              </button>
            </div>
            {personalities.map(p => (
              <div key={p.id} className="personality-card">
                <div className="card-header">
                  <div className="card-icon" style={{ backgroundColor: p.ui?.color || '#666' }}>
                    {p.ui?.icon || '👤'}
                  </div>
                  <div className="card-meta">
                    <h3>{p.name}</h3>
                    <span className="model-badge">{p.model}</span>
                  </div>
                </div>
                <div className="card-body">
                  <p>{p.description}</p>
                  <div className="tags">
                    {p.source === 'system' && <span className="tag system">System</span>}
                    {p.source === 'custom' && <span className="tag custom">Custom</span>}
                    {!p.enabled && <span className="tag disabled">Disabled</span>}
                  </div>
                </div>
                <div className="card-actions">
                  <button onClick={() => openEditor(p)}>
                    {p.source === 'system' ? 'View / Shadow' : 'Edit'}
                  </button>
                  {p.source !== 'system' && (
                    <button className="p-delete-btn" onClick={() => handleDelete(p.id)}>Delete</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'league' && (
          <LeagueTable isInstanceAdmin={isInstanceAdmin} />
        )}

        {activeTab === 'evolution' && (
          <EvolutionPanel
            personalities={personalities}
            onRefresh={loadData}
          />
        )}

        {activeTab === 'system-prompts' && (
          <SystemPromptsEditor />
        )}

        {activeTab === 'voting-history' && (
          <VotingHistory />
        )}
      </div>

      {/* Create Modal */}
      {isCreating && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Add New Personality</h3>

            <div className="template-selector">
              <small>Quick Start Templates:</small>
              <div className="template-buttons">
                <button onClick={() => handleUseTemplate({
                  name: "The Skeptic",
                  description: "Questions assumptions and looks for edge cases.",
                  prompt: "You are The Skeptic. Your goal is to identify potential flaws..."
                })}>Skeptic</button>
                <button onClick={() => handleUseTemplate({
                  name: "The Optimist",
                  description: "Focuses on potential benefits and positive outcomes.",
                  prompt: "You are The Optimist. Your goal is to highlight opportunities..."
                })}>Optimist</button>
              </div>
            </div>

            <div className="form-group">
              <label>Name</label>
              <input
                value={newPersonality.name}
                onChange={e => setNewPersonality({ ...newPersonality, name: e.target.value })}
                placeholder="e.g. The Analyst"
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newPersonality.description}
                onChange={e => setNewPersonality({ ...newPersonality, description: e.target.value })}
                placeholder="Brief description of their role..."
              />
            </div>
            <div className="form-group">
              <label>Model</label>
              <select
                value={newPersonality.model}
                onChange={e => setNewPersonality({ ...newPersonality, model: e.target.value })}
              >
                <option value="">Select a Model...</option>
                <option value="gemini/gemini-2.5-pro">Gemini 2.5 Pro</option>
                <option value="gemini/gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
              </select>
            </div>

            <div className="form-note">
              You can configure the full personality profile (Identity, Tone, etc.) after creation.
            </div>

            <div className="modal-actions">
              <button onClick={() => setIsCreating(false)}>Cancel</button>
              <button className="primary" onClick={handleCreate}>Create Personality</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalityManager;
