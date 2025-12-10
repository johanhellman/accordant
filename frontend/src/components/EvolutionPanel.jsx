import React, { useState, useEffect } from 'react';
import { api } from '../api';
import './EvolutionPanel.css';
import ContextualHelp from './ContextualHelp';

const EvolutionPanel = ({ personalities: initialPersonalities, onRefresh }) => {
    const [personalities, setPersonalities] = useState(initialPersonalities || []);
    const [selectedParents, setSelectedParents] = useState([]);
    const [offspringName, setOffspringName] = useState('');
    const [isCombining, setIsCombining] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    // Fetch data if not provided via props (standalone mode)
    useEffect(() => {
        if (!initialPersonalities) {
            loadPersonalities();
        } else {
            setPersonalities(initialPersonalities);
        }
    }, [initialPersonalities]);

    const loadPersonalities = async () => {
        try {
            const data = await api.listPersonalities();
            setPersonalities(data);
        } catch (err) {
            console.error("Failed to load personalities:", err);
            setError("Failed to load personalities for evolution selection.");
        }
    };

    const handleToggleParent = (id) => {
        if (selectedParents.includes(id)) {
            setSelectedParents(selectedParents.filter(pid => pid !== id));
        } else {
            if (selectedParents.length >= 3) {
                alert("You can combine max 3 personalities at a time.");
                return;
            }
            setSelectedParents([...selectedParents, id]);
        }
    };

    const handleCombine = async () => {
        if (selectedParents.length < 2) {
            setError("Select at least 2 parents.");
            return;
        }
        if (!offspringName.trim()) {
            setError("Please provide a name for the new personality.");
            return;
        }

        try {
            setIsCombining(true);
            setError(null);
            setResult(null);

            const newPersonality = await api.combinePersonalities({
                parent_ids: selectedParents,
                name_suggestion: offspringName,
            });

            setResult(newPersonality);
            setSelectedParents([]);
            setOffspringName('');

            // Refresh local data or parent data
            if (onRefresh) {
                onRefresh();
            } else {
                loadPersonalities();
            }

        } catch (err) {
            console.error(err);
            setError(err.message || "Detailed evolution failed upon synthesis.");
        } finally {
            setIsCombining(false);
        }
    };

    return (
        <div className="evolution-container">
            <div className="evolution-sidebar">
                <h4>Select Parents</h4>
                <p className="evo-hint">Choose 2-3 personalities to combine.</p>
                <div className="parent-list">
                    {personalities.filter(p => p.enabled).map(p => (
                        <div
                            key={p.id}
                            className={`parent-item ${selectedParents.includes(p.id) ? 'selected' : ''}`}
                            onClick={() => handleToggleParent(p.id)}
                        >
                            <div className="parent-check">
                                {selectedParents.includes(p.id) ? '✓' : ''}
                            </div>
                            <div className="parent-info">
                                <span className="p-name">{p.name}</span>
                                <span className="p-source">{p.source === 'system' ? 'System' : 'Custom'}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="evolution-main">
                <div className="dna-viz">
                    {/* Simple visualizer */}
                    <div className="dna-strand"></div>
                    <div className="evo-icon">🧬</div>
                    <div className="dna-strand"></div>
                </div>

                <h3>Personality Evolution</h3>
                <ContextualHelp topic="evolution" type="banner" />

                <div className="evo-form">
                    <label htmlFor="offspring-name">New Personality Name</label>
                    <input
                        id="offspring-name"
                        name="offspringName"
                        type="text"
                        value={offspringName}
                        onChange={(e) => setOffspringName(e.target.value)}
                        placeholder="e.g. The Diplomat, Logic Core v2..."
                    />

                    <div className="selected-summary">
                        Combining:
                        {selectedParents.length > 0 ? (
                            <span className="tag-list">
                                {selectedParents.map(pid => {
                                    const p = personalities.find(x => x.id === pid);
                                    return <span key={pid} className="parent-tag">{p ? p.name : pid}</span>
                                })}
                            </span>
                        ) : (
                            <span className="placeholder-text"> (None selected)</span>
                        )}
                    </div>

                    {error && <div className="evo-error">{error}</div>}

                    <button
                        className="combine-btn"
                        onClick={handleCombine}
                        disabled={isCombining || selectedParents.length < 2}
                    >
                        {isCombining ? "Synthesizing DNA..." : "Evolution Combine"}
                    </button>
                </div>

                {result && (
                    <div className="evo-success">
                        <h4>Evolution Successful!</h4>
                        <p>Created: <strong>{result.name}</strong></p>
                        <div className="success-actions">
                            <button onClick={() => setResult(null)}>Create Another</button>
                            {/* Could link to editor here */}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default EvolutionPanel;
