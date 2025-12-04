import { useState, useEffect } from "react";
import { api } from "../api";
import "./OrganizationManagement.css";

export default function OrganizationManagement() {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      const data = await api.listOrganizations();
      setOrganizations(data);
      setError(null); // Clear any previous errors
    } catch (err) {
      if (err.status === 401) {
        setError("Authentication required. Please refresh the page or log in again.");
      } else if (err.status === 403) {
        setError("Access denied. Instance admin privileges required.");
      } else if (err.status === 405) {
        setError("Method not allowed. Please check your API configuration.");
      } else {
        setError("Failed to load organizations. Please try again.");
      }
      console.error("Failed to load organizations:", err);
    } finally {
      setLoading(false);
    }
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

  if (loading) return <div className="loading">Loading organizations...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="organization-management">
      <h2>Organization Management</h2>
      <div className="orgs-table-container">
        <table className="orgs-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>Owner Email</th>
              <th>Created At</th>
              <th>API Key Configured</th>
            </tr>
          </thead>
          <tbody>
            {organizations.length === 0 ? (
              <tr>
                <td colSpan="5" className="no-data">
                  No organizations found
                </td>
              </tr>
            ) : (
              organizations.map((org) => (
                <tr key={org.id}>
                  <td>{org.name}</td>
                  <td className="id-cell">{org.id}</td>
                  <td>{org.owner_email || "N/A"}</td>
                  <td>{formatDate(org.created_at)}</td>
                  <td>
                    {org.api_config?.api_key ? (
                      <span className="status-badge configured">Yes</span>
                    ) : (
                      <span className="status-badge not-configured">No</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

