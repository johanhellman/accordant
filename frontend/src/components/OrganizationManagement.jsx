import { useState, useEffect } from "react";
import { api } from "../api";
import { Trash2, Edit2, ShieldAlert, X } from "lucide-react";
import "./OrganizationManagement.css";

export default function OrganizationManagement() {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [editingOrg, setEditingOrg] = useState(null);
  const [deletingOrg, setDeletingOrg] = useState(null);

  // Edit Form State
  const [editForm, setEditForm] = useState({
    api_key: "",
    base_url: "",
  });

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      const data = await api.listOrganizations();
      setOrganizations(data);
      setError(null);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleError = (err) => {
    if (err.status === 401) {
      setError("Authentication required. Please refresh the page or log in again.");
    } else if (err.status === 403) {
      setError("Access denied. Instance admin privileges required.");
    } else if (err.status === 405) {
      setError("Method not allowed. Please check your API configuration.");
    } else {
      setError("Operation failed. Please try again.");
    }
    console.error("Operation failed:", err);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + " " + date.toLocaleTimeString();
    } catch {
      return dateString;
    }
  };

  // --- Actions ---

  const handleEditClick = (org) => {
    setEditingOrg(org);
    setEditForm({
      api_key: "", // Don't show existing key for security, only placeholder
      base_url: org.api_config?.base_url || "",
    });
  };

  const handleDeleteClick = (org) => {
    setDeletingOrg(org);
  };

  const handleSaveEdit = async () => {
    try {
      const updates = {};
      if (editForm.api_key) updates.api_key = editForm.api_key;
      if (editForm.base_url) updates.base_url = editForm.base_url;

      await api.updateOrganization(editingOrg.id, updates);

      // Refresh list
      await loadOrganizations();
      setEditingOrg(null);
    } catch (err) {
      alert("Failed to update organization: " + err.message);
    }
  };

  const handleConfirmDelete = async () => {
    try {
      await api.deleteOrganization(deletingOrg.id);
      await loadOrganizations();
      setDeletingOrg(null);
    } catch (err) {
      alert("Failed to delete organization: " + err.message);
    }
  };

  if (loading) return <div className="loading">Loading organizations...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="organization-management">
      <header className="page-header">
        <h2>Organization Management</h2>
        <div className="header-actions">
          {/* Add Create Org button here in future if desired */}
        </div>
      </header>

      <div className="orgs-table-container">
        <table className="orgs-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>Owner Email</th>
              <th>Created At</th>
              <th>Configuration</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {organizations.length === 0 ? (
              <tr>
                <td colSpan="6" className="no-data">
                  No organizations found
                </td>
              </tr>
            ) : (
              organizations.map((org) => (
                <tr key={org.id}>
                  <td className="font-medium">{org.name}</td>
                  <td className="id-cell">{org.id.substring(0, 8)}...</td>
                  <td>{org.owner_email || "N/A"}</td>
                  <td>{formatDate(org.created_at)}</td>
                  <td>
                    {org.api_config?.api_key ? (
                      <span className="status-badge configured">Key Set</span>
                    ) : (
                      <span className="status-badge not-configured">No Key</span>
                    )}
                    {org.api_config?.base_url && (
                      <span className="base-url-tag" title={org.api_config.base_url}>Custom URL</span>
                    )}
                  </td>
                  <td>
                    <div className="actions-cell">
                      <button
                        className="icon-btn edit-btn"
                        onClick={() => handleEditClick(org)}
                        title="Edit Configuration"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        className="icon-btn delete-btn"
                        onClick={() => handleDeleteClick(org)}
                        title="Delete Organization"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {editingOrg && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Edit Organization: {editingOrg.name}</h3>
              <button className="close-btn" onClick={() => setEditingOrg(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>API Key (Leave blank to keep existing)</label>
                <input
                  type="password"
                  value={editForm.api_key}
                  onChange={(e) => setEditForm({ ...editForm, api_key: e.target.value })}
                  placeholder="sk-..."
                />
              </div>
              <div className="form-group">
                <label>Base URL</label>
                <input
                  type="text"
                  value={editForm.base_url}
                  onChange={(e) => setEditForm({ ...editForm, base_url: e.target.value })}
                  placeholder="https://openrouter.ai/api/v1"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setEditingOrg(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveEdit}>Save Changes</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {deletingOrg && (
        <div className="modal-overlay">
          <div className="modal-content danger-modal">
            <div className="modal-header">
              <h3 className="danger-text"><ShieldAlert size={24} /> Delete Organization?</h3>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to delete <strong>{deletingOrg.name}</strong>?
              </p>
              <div className="warning-box">
                <p>This action is <strong>irreversible</strong>.</p>
                <ul>
                  <li>All users in this organization will be deleted.</li>
                  <li>All conversation history (tenant database) will be wiped.</li>
                  <li>All custom personalities will be lost.</li>
                </ul>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setDeletingOrg(null)}>Cancel</button>
              <button className="btn btn-danger" onClick={handleConfirmDelete}>Confirm Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
