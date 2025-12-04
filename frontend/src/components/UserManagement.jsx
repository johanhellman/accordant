import { useState, useEffect } from "react";
import { api } from "../api";
import "./UserManagement.css";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await api.listUsers();
      setUsers(data);
    } catch (err) {
      setError("Failed to load users");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAdmin = async (userId, currentStatus) => {
    try {
      await api.updateUserRole(userId, !currentStatus);
      // Optimistic update
      setUsers(users.map((u) => (u.id === userId ? { ...u, is_admin: !currentStatus } : u)));
    } catch (err) {
      console.error("Failed to update role:", err);
      alert("Failed to update user role");
    }
  };

  // Invitations Logic
  const [invitations, setInvitations] = useState([]);
  const [loadingInvites, setLoadingInvites] = useState(false);
  const [inviteError, setInviteError] = useState(null);

  useEffect(() => {
    loadInvitations();
  }, []);

  const loadInvitations = async () => {
    setLoadingInvites(true);
    try {
      const data = await api.getInvitations();
      setInvitations(data);
    } catch (err) {
      console.error("Failed to load invitations:", err);
    } finally {
      setLoadingInvites(false);
    }
  };

  const handleCreateInvite = async () => {
    setInviteError(null);
    try {
      await api.createInvitation();
      await loadInvitations();
    } catch (err) {
      setInviteError("Failed to create invitation");
      console.error(err);
    }
  };

  if (loading) return <div className="loading">Loading users...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="user-management">
      <h2>User Management</h2>
      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>ID</th>
              <th>Role</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td className="id-cell">{user.id}</td>
                <td>
                  <span className={`role-badge ${user.is_admin ? "admin" : "user"}`}>
                    {user.is_admin ? "Admin" : "User"}
                  </span>
                </td>
                <td>
                  <button
                    className={`role-btn ${user.is_admin ? "demote" : "promote"}`}
                    onClick={() => handleToggleAdmin(user.id, user.is_admin)}
                  >
                    {user.is_admin ? "Remove Admin" : "Make Admin"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="invitations-section" style={{ marginTop: "30px" }}>
        <h3>Organization Invitations</h3>
        <p className="hint">Generate codes to invite new members to your organization.</p>

        <div className="invitations-list">
          {loadingInvites ? (
            <div>Loading invitations...</div>
          ) : invitations.length === 0 ? (
            <div className="no-data">No active invitations</div>
          ) : (
            <table className="invites-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Expires At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((invite) => (
                  <tr key={invite.code}>
                    <td className="code-cell">{invite.code}</td>
                    <td>{new Date(invite.expires_at).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-badge ${invite.is_active ? "active" : "inactive"}`}>
                        {invite.is_active ? "Active" : "Used/Expired"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {inviteError && <div className="error-message">{inviteError}</div>}

        <div className="form-actions">
          <button type="button" className="secondary-btn" onClick={handleCreateInvite}>
            Generate New Invite Code
          </button>
        </div>
      </div>
    </div>
  );
}
