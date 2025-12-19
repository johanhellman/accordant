import React, { useState, useEffect } from "react";
import { api } from "../api";
import { X } from "lucide-react";
import "./NewSessionModal.css";

const NewSessionModal = ({ onClose, onStart }) => {
  const [packs, setPacks] = useState([]);
  const [selectedPackId, setSelectedPackId] = useState("");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [packsData, activeConfig] = await Promise.all([api.getPacks(), api.getActiveConfig()]);
      setPacks(packsData);
      // Default to active pack
      if (activeConfig && activeConfig.active_pack_id) {
        setSelectedPackId(activeConfig.active_pack_id);
      } else if (packsData.length > 0) {
        setSelectedPackId(packsData[0].id);
      }
    } catch (e) {
      console.error("Failed to load packs", e);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    setStarting(true);
    try {
      // 1. Activate the selected pack
      if (selectedPackId) {
        await api.setActiveConfig(selectedPackId);
      }

      // 2. Start conversation
      await onStart(); // Parent handles creation and navigation
    } catch (e) {
      console.error(e);
      alert("Failed to start session");
      setStarting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="new-session-modal">
        <div className="modal-header">
          <h3>Start New Council Session</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div>Loading configuration...</div>
          ) : (
            <>
              {packs.length === 0 ? (
                <div className="empty-packs-message">
                  <p>No Council Packs found.</p>
                  <p className="helper-text">
                    You need at least one Pack to start a structured session.
                  </p>
                  {/* Ideally link to creation or allow ad-hoc */}
                </div>
              ) : (
                <div className="form-group">
                  <label>Select Council Pack</label>
                  <select
                    className="pack-select"
                    value={selectedPackId}
                    onChange={(e) => setSelectedPackId(e.target.value)}
                  >
                    {packs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.display_name} {p.is_system ? "(System)" : ""}
                      </option>
                    ))}
                  </select>
                  <div className="helper-text">
                    This defines the personalities and strategy for this session. (Note: Switching
                    this changes your active default for now).
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="start-btn"
            onClick={handleStart}
            disabled={loading || starting || !selectedPackId}
          >
            {starting ? "Starting..." : "Start Session"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NewSessionModal;
