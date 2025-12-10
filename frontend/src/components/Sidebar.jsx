import "./Sidebar.css";
import Logo from "./Logo";

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  currentView,
  onViewChange,
  user,
  onLogout,
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <Logo size="md" className="sidebar-logo" />
        <button className="new-conversation-btn btn btn-primary" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>


      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${conv.id === currentConversationId && currentView === "chat" ? "active" : ""
                }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">{conv.title || "New Conversation"}</div>
              <div className="conversation-meta">{conv.message_count} messages</div>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="nav-section">
          {user && user.is_instance_admin && (
            <>
              <h3>Instance Admin</h3>
              <div
                className={`nav-item ${currentView === "organizations" ? "active" : ""}`}
                onClick={() => onViewChange("organizations")}
              >
                Organizations
              </div>
            </>
          )}

          {user && (user.is_admin || user.is_instance_admin) && (
            <>
              <h3>Admin</h3>

              <div className="nav-group-label">Council Settings</div>
              <div
                className={`nav-item ${currentView === "personalities" ? "active" : ""}`}
                onClick={() => onViewChange("personalities")}
              >
                Council Personalities
              </div>

              <div className="nav-group-label">System Settings</div>
              <div
                className={`nav-item ${currentView === "users" ? "active" : ""}`}
                onClick={() => onViewChange("users")}
              >
                User Management
              </div>
              <div
                className={`nav-item ${currentView === "settings" ? "active" : ""}`}
                onClick={() => onViewChange("settings")}
              >
                Settings
              </div>
            </>
          )}
          <div className="nav-group-label" style={{ marginTop: "1rem" }}>
            Resources
          </div>
          <a
            href="/help"
            className="nav-item"
            style={{ display: "block", textDecoration: "none" }}
          >
            User Manual
          </a>
          <a
            href="/faq"
            className="nav-item"
            style={{ display: "block", textDecoration: "none" }}
          >
            FAQ
          </a>

          <div className="nav-group-label" style={{ marginTop: "1rem" }}>
            Account
          </div>
          <div
            className={`nav-item ${currentView === "user-settings" ? "active" : ""}`}
            onClick={() => onViewChange("user-settings")}
          >
            User Settings
          </div>
        </div>

        {user && (
          <div className="user-section">
            <div className="user-info">
              <span className="username">{user.username}</span>
              {user.is_instance_admin && <span className="admin-badge">Instance Admin</span>}
              {!user.is_instance_admin && user.is_admin && (
                <span className="admin-badge">Admin</span>
              )}
            </div>
            <button className="logout-btn" onClick={onLogout}>
              Logout
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
