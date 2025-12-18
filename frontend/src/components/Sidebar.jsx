import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, Settings, Users, HelpCircle, LogOut } from "lucide-react";
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
  isOpen, // New prop
  onClose, // New prop
}) {
  const [councilExpanded, setCouncilExpanded] = useState(false);
  const [orgExpanded, setOrgExpanded] = useState(false);

  const isAdmin = user && (user.is_admin || user.is_instance_admin);
  const isInstanceAdmin = user && user.is_instance_admin;

  return (
    <div className={`sidebar ${isOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <Logo size="md" className="sidebar-logo" />
        <button className="new-conversation-btn btn btn-primary" onClick={onNewConversation}>
          <Plus size={18} />
          <span>New Session</span>
        </button>
      </div>

      <div className="conversation-list">
        <div className="conversation-list-header">Council Sessions</div>
        {conversations.length === 0 ? (
          <div className="no-conversations">No sessions yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId && currentView === "chat" ? "active" : ""
              }`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-title">{conv.title || "New Session"}</div>
              <div className="conversation-meta">{conv.message_count} messages</div>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="nav-section">
          {/* Council Settings - Collapsible */}
          {isAdmin && (
            <div className="nav-group">
              <div
                className="nav-group-header"
                onClick={() => setCouncilExpanded(!councilExpanded)}
              >
                {councilExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <Settings size={16} />
                <span>Council Setup</span>
              </div>
              {councilExpanded && (
                <div className="nav-group-content">
                  <div
                    className={`nav-item ${currentView === "personalities" ? "active" : ""}`}
                    onClick={() => onViewChange("personalities")}
                  >
                    Personalities
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Organization Settings - Collapsible */}
          {isAdmin && (
            <div className="nav-group">
              <div className="nav-group-header" onClick={() => setOrgExpanded(!orgExpanded)}>
                {orgExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <Users size={16} />
                <span>Organization</span>
              </div>
              {orgExpanded && (
                <div className="nav-group-content">
                  {isInstanceAdmin && (
                    <>
                      <div
                        className={`nav-item ${currentView === "dashboard" ? "active" : ""}`}
                        onClick={() => onViewChange("dashboard")}
                      >
                        Dashboard
                      </div>
                      <div
                        className={`nav-item ${currentView === "organizations" ? "active" : ""}`}
                        onClick={() => onViewChange("organizations")}
                      >
                        Organizations
                      </div>
                    </>
                  )}
                  <div
                    className={`nav-item ${currentView === "users" ? "active" : ""}`}
                    onClick={() => onViewChange("users")}
                  >
                    Users
                  </div>
                  <div
                    className={`nav-item ${currentView === "settings" ? "active" : ""}`}
                    onClick={() => onViewChange("settings")}
                  >
                    Settings
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Help & Resources */}
          <div className="nav-group">
            <a href="/help" className="nav-group-header nav-link">
              <HelpCircle size={16} />
              <span>Help & Docs</span>
            </a>
          </div>
        </div>

        {/* User Section */}
        {user && (
          <div className="user-section">
            <div className="user-info">
              <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
              <div className="user-details">
                <span className="username">{user.username}</span>
                {user.is_instance_admin && <span className="user-role">Instance Admin</span>}
                {!user.is_instance_admin && user.is_admin && (
                  <span className="user-role">Admin</span>
                )}
              </div>
            </div>
            <div className="user-actions">
              <button
                className="user-action-btn"
                onClick={() => onViewChange("user-settings")}
                title="Settings"
              >
                <Settings size={16} />
              </button>
              <button className="user-action-btn" onClick={onLogout} title="Logout">
                <LogOut size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
