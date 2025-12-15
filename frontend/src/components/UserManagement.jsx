import { useState, useEffect } from "react";
import { api } from "../api";
import { Trash2, UserCog, User, Shield, Search, X } from "lucide-react";
import "./UserManagement.css";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  // Deletion State
  const [deletingUser, setDeletingUser] = useState(null);

  // Invitations Logic
  const [invitations, setInvitations] = useState([]);
  const [loadingInvites, setLoadingInvites] = useState(false);
  const [inviteError, setInviteError] = useState(null);

  useEffect(() => {
    loadUsers();
    loadInvitations();
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

  const handleDeleteClick = (user) => {
    setDeletingUser(user);
  };

  const handleConfirmDelete = async () => {
    try {
      await api.deleteUser(deletingUser.id);
      await loadUsers();
      setDeletingUser(null);
    } catch (err) {
      alert("Failed to delete user: " + err.message);
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

  // Filter Logic
  const filteredUsers = users.filter((user) => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole =
      roleFilter === "all" ? true : roleFilter === "admin" ? user.is_admin : !user.is_admin;
    return matchesSearch && matchesRole;
  });

  if (loading) return <div className="loading">Loading users...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="user-management">
      <header className="page-header">
        <h2>User Management</h2>
      </header>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="search-bar">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="role-filter"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          <option value="all">All Roles</option>
          <option value="admin">Admins</option>
          <option value="user">Users</option>
        </select>
      </div>

      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.length === 0 ? (
              <tr>
                <td colSpan="4" className="no-data">
                  No users found
                </td>
              </tr>
            ) : (
              filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="user-cell">
                      <div className="user-avatar">
                        <User size={20} />
                      </div>
                      <div className="user-details">
                        <span className="username">{user.username}</span>
                        <span className="user-id">ID: {user.id.substring(0, 8)}...</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`role-badge ${user.is_admin ? "admin" : "user"}`}>
                      {user.is_admin ? <Shield size={12} /> : <User size={12} />}
                      {user.is_admin ? "Org Admin" : "Member"}
                    </span>
                  </td>
                  <td>
                    <span className="status-badge active">Active</span>
                  </td>
                  <td>
                    <div className="actions-cell">
                      <button
                        className="icon-btn"
                        title={user.is_admin ? "Demote to Member" : "Promote to Admin"}
                        onClick={() => handleToggleAdmin(user.id, user.is_admin)}
                      >
                        <UserCog size={18} />
                      </button>
                      <button
                        className="icon-btn delete-btn"
                        title="Remove User"
                        onClick={() => handleDeleteClick(user)}
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

      <div className="invitations-section">
        <h3>Invitations</h3>
        <p className="hint">Invite new members using time-limited codes.</p>

        <div className="invitations-list">
          {loadingInvites ? (
            <div className="loading-sm">Loading invitations...</div>
          ) : invitations.length === 0 ? (
            <div className="no-data-sm">No active invitations</div>
          ) : (
            <table className="invites-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Expires</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((invite) => (
                  <tr key={invite.code}>
                    <td className="code-cell">{invite.code}</td>
                    <td>{new Date(invite.expires_at).toLocaleDateString()}</td>
                    <td>
                      <span
                        className={`status-dot ${invite.is_active ? "active" : "inactive"}`}
                      ></span>
                      {invite.is_active ? "Active" : "Expired"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {inviteError && <div className="error-msg-sm">{inviteError}</div>}

        <button className="btn btn-secondary mt-4" onClick={handleCreateInvite}>
          + Generate Invite Code
        </button>
      </div>

      {/* Delete Confirmation Modal */}
      {deletingUser && (
        <div className="modal-overlay">
          <div className="modal-content danger-modal">
            <div className="modal-header">
              <h3>Remove User?</h3>
              <button className="close-btn" onClick={() => setDeletingUser(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to remove <strong>{deletingUser.username}</strong> from the
                organization?
              </p>
              <p className="subtext">
                They will maintain their account but lose access to this workspace.
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setDeletingUser(null)}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleConfirmDelete}>
                Confirm Removal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
