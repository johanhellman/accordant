import { useState, useEffect } from "react";
import { api } from "../api";
import "./OrgSettings.css";

export default function OrgSettings() {
  const [settings, setSettings] = useState({ api_key: "", base_url: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getOrgSettings();
      setSettings({
        api_key: data.api_key || "", // Will be masked '********'
        base_url: data.base_url || "",
      });
      setError(null); // Clear any previous errors
    } catch (err) {
      // Check if it's an authentication error
      if (err.status === 401 || err.message?.includes("Unauthorized")) {
        setError("Authentication required. Please refresh the page or log in again.");
      } else {
        setError("Failed to load settings. Please try again.");
      }
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // Only send fields that have values (to allow partial updates if needed)
      // But here we send both from state.
      // If api_key is '********', we should probably NOT send it back unless changed?
      // The backend should handle receiving '********' gracefully or we should track dirty state.
      // Better: Only send api_key if it's NOT '********' (i.e. user typed something new)

      const payload = {
        base_url: settings.base_url,
      };

      if (settings.api_key && settings.api_key !== "********") {
        payload.api_key = settings.api_key;
      }

      await api.updateOrgSettings(payload);
      setSuccess("Settings saved successfully");
      setError(null);

      // Reload to get fresh state (and masked key)
      await loadSettings();
    } catch (err) {
      if (err.status === 401 || err.message?.includes("Unauthorized")) {
        setError("Authentication required. Please refresh the page or log in again.");
      } else {
        setError("Failed to save settings. Please try again.");
      }
      console.error("Failed to save settings:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: value }));
  };

  if (loading) return <div className="loading">Loading settings...</div>;

  return (
    <div className="org-settings">
      <h2>Organization Settings</h2>

      <div className="settings-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="api_key">LLM API Key</label>
            <div className="input-wrapper">
              <input
                type="password"
                id="api_key"
                name="api_key"
                value={settings.api_key}
                onChange={handleChange}
                placeholder="sk-..."
                autoComplete="off"
              />
              <small className="hint">
                {settings.api_key === "********"
                  ? "Key is set and encrypted. Enter new key to update."
                  : "Enter your OpenRouter or LLM Provider API Key."}
              </small>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="base_url">LLM Gateway URL</label>
            <input
              type="text"
              id="base_url"
              name="base_url"
              value={settings.base_url}
              onChange={handleChange}
              placeholder="https://openrouter.ai/api/v1/chat/completions"
            />
            <small className="hint">
              Base URL for the LLM provider (e.g. OpenRouter, LocalAI).
            </small>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <div className="form-actions">
            <button type="submit" className="save-btn" disabled={saving}>
              {saving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
