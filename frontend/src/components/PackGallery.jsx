import React, { useState, useEffect } from "react";
import { api } from "../api";
import "./PackGallery.css";
import { Check, Layers, User, Settings } from "lucide-react";

const PackGallery = () => {
  const [packs, setPacks] = useState([]);
  const [activeConfig, setActiveConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState("all"); // 'all', 'system', 'custom'

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [allPacks, config] = await Promise.all([api.getPacks(), api.getActiveConfig()]);
      setPacks(allPacks);
      setActiveConfig(config);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (packId) => {
    try {
      const res = await api.setActiveConfig(packId);
      setActiveConfig(res.active_state);
      // Optional: Show toast
    } catch (e) {
      console.error(e);
      alert("Failed to activate pack");
    }
  };

  const handleCreate = () => {
    // For now, prompt or modal.
    // Ideally navigate to a /config/packs/new or open modal.
    // Since we don't have a full editor yet, alert for now or implemented later.
    alert("Custom Pack creation coming soon!");
  };

  const filteredPacks = packs.filter((p) => {
    if (scope === "system") return p.source === "system";
    if (scope === "custom") return p.source === "custom";
    return true;
  });

  return (
    <div className="pack-gallery-container">
      <div className="gallery-header">
        <h2>Council Packs</h2>
        <div className="header-actions">
          <div className="scope-tabs">
            <button className={scope === "all" ? "active" : ""} onClick={() => setScope("all")}>
              All
            </button>
            <button
              className={scope === "system" ? "active" : ""}
              onClick={() => setScope("system")}
            >
              System
            </button>
            <button
              className={scope === "custom" ? "active" : ""}
              onClick={() => setScope("custom")}
            >
              Custom
            </button>
          </div>
          <button className="create-pack-btn" onClick={handleCreate}>
            + Create Pack
          </button>
        </div>
      </div>

      {loading ? (
        <div>Loading packs...</div>
      ) : (
        <div className="packs-grid">
          {filteredPacks.length === 0 ? (
            <div className="empty-state">
              No packs found for this filter.
              {scope !== "system" && (
                <button onClick={handleCreate}>Create your first Custom Pack</button>
              )}
            </div>
          ) : (
            filteredPacks.map((pack) => {
              const isActive = activeConfig?.active_pack_id === pack.id;
              return (
                <div key={pack.id} className={`pack-card ${pack.source}`}>
                  <div className="pack-header">
                    <h3>{pack.display_name}</h3>
                    {pack.is_system && <span className="badge system">System</span>}
                    {!pack.is_system && <span className="badge custom">Custom</span>}
                  </div>
                  <p className="pack-desc">{pack.description || "No description provided."}</p>

                  <div className="pack-meta">
                    <div className="meta-item">
                      <strong>Strategy:</strong> {pack.config.consensus_strategy || "Default"}
                    </div>
                    <div className="meta-item">
                      <strong>Team:</strong> {pack.config.personalities.length} Personalities
                    </div>
                  </div>

                  <div className="pack-actions">
                    <button
                      className={`activate-btn ${isActive ? "active" : ""}`}
                      onClick={() => handleActivate(pack.id)}
                      disabled={isActive}
                    >
                      {isActive ? "Active" : "Activate"}
                    </button>
                    {pack.source === "custom" && <button className="edit-btn">Edit</button>}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default PackGallery;
