import React, { useState, useEffect } from 'react';
import { api } from '../api';
import PersonalityPromptEditor from './PersonalityPromptEditor';
import './PersonalityManager.css'; // Reusing existing styles for now

const PersonalityEditor = ({ personalityId, onSave, onCancel }) => {
    const [personality, setPersonality] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [models, setModels] = useState([]);
    const [providerFilter, setProviderFilter] = useState("all");
    const [systemPrompts, setSystemPrompts] = useState({});
    const [scope, setScope] = useState('org'); // Default to org for now, could be prop if we support global editing here

    useEffect(() => {
        loadData();
    }, [personalityId]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [pData, mList, sPrompts] = await Promise.all([
                api.listPersonalities(), // We list all to find specific one or fetched by ID?
                api.listModels(),
                api.getSystemPrompts()
            ]);

            setModels(mList);
            setSystemPrompts(sPrompts);

            // We need to find the specific personality or fetch it directly
            // listPersonalities returns the array.
            // Ideally we stick to the pattern of the old manager: find in list.
            // Or we can fetch directly if we had a get endpoint for single URL.
            // But let's just find it in the list for consistency with "Shadowing" logic which implies
            // we might start with a system one.

            const found = pData.find(p => p.id === personalityId);
            if (found) {
                // Normalize prompt
                let safePrompt = found.personality_prompt;
                if (typeof safePrompt === "string") {
                    safePrompt = { "IDENTITY & ROLE": safePrompt };
                } else if (!safePrompt) {
                    safePrompt = {};
                }
                setPersonality({ ...found, personality_prompt: safePrompt });

                // Determine scope/source?
                // For now assuming Org scope since Manager is Org focused.
            } else {
                setError("Personality not found.");
            }

        } catch (err) {
            setError("Failed to load personality data.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!personality) return;

        // Valdiation?
        // ... reuse validation logic from old manager ...

        try {
            // Prepare payload
            const payload = {
                ...personality,
                temperature: parseFloat(personality.temperature)
            };

            // If source is system, we are CUSTOMIZING (Creating an override)
            // So we use org API update/create
            if (personality.source === 'system') {
                // Verify it doesn't map to a new ID (ID should be locked for overrides usually?)
                // But if we are shadowing, we keep the same ID.
                await api.updatePersonality(payload.id, payload);
            } else {
                await api.updatePersonality(payload.id, payload);
            }

            if (onSave) onSave();
        } catch (err) {
            alert("Failed to save: " + err.message);
        }
    };

    const providers = ["all", ...new Set(models.map((m) => m.provider))];
    const filteredModels = (
        providerFilter === "all" ? models : models.filter((m) => m.provider === providerFilter)
    ).sort((a, b) => (a.name || a.id).localeCompare(b.name || b.id));

    if (loading) return <div className="loading">Loading Editor...</div>;
    if (error) return <div className="error">{error}</div>;
    if (!personality) return null;

    return (
        <div className="personality-editor-container">
            <div className="personality-editor">
                <div className="editor-header">
                    <h2>
                        {personality.source === 'system' ? `Customize ${personality.name}` : "Edit Personality"}
                    </h2>
                    <button className="close-btn" onClick={onCancel}>×</button>
                </div>

                {personality.source === 'system' && (
                    <div className="system-notice">
                        ℹ️ You are about to customize a System Personality. This will create a local copy that overrides the global default.
                    </div>
                )}

                <div className="editor-content">
                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="personality-id">ID (Unique) *</label>
                            <input
                                id="personality-id"
                                name="personalityId"
                                value={personality.id}
                                disabled={true} // ID is locked during edit
                                className="disabled-input"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="personality-name">Name *</label>
                            <input
                                id="personality-name"
                                name="personalityName"
                                value={personality.name}
                                onChange={(e) => setPersonality({ ...personality, name: e.target.value })}
                                placeholder="Display Name"
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="personality-description">Description *</label>
                        <input
                            id="personality-description"
                            name="personalityDescription"
                            value={personality.description}
                            onChange={(e) => setPersonality({ ...personality, description: e.target.value })}
                            placeholder="Short description of role"
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="personality-provider-filter">Model *</label>
                            <div className="model-selector">
                                <select
                                    id="personality-provider-filter"
                                    name="providerFilter"
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
                                    id="personality-model"
                                    name="personalityModel"
                                    value={personality.model}
                                    onChange={(e) => setPersonality({ ...personality, model: e.target.value })}
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
                            <label htmlFor="personality-temperature">Temperature *</label>
                            <input
                                id="personality-temperature"
                                name="personalityTemperature"
                                type="number"
                                min="0"
                                max="2"
                                step="0.1"
                                value={personality.temperature}
                                onChange={(e) => setPersonality({ ...personality, temperature: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="form-group prompt-editor-wrapper">
                        <PersonalityPromptEditor
                            promptData={personality.personality_prompt}
                            systemPrompts={systemPrompts}
                            onChange={(newData) => setPersonality({ ...personality, personality_prompt: newData })}
                        />
                    </div>
                </div>

                <div className="editor-actions">
                    <button onClick={onCancel} className="secondary">
                        Cancel
                    </button>
                    <button onClick={handleSave} className="primary">
                        {personality.source === 'system' ? "Save as Custom Override" : "Save Changes"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PersonalityEditor;
