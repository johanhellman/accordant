import React from "react";
import { Outlet, useLocation, useNavigate, useParams, Link } from "react-router-dom";
import { MessageSquare, Settings, HelpCircle, User } from "lucide-react";
import Sidebar from "./Sidebar";
import "../App.css";

const Layout = ({ conversations, onNewConversation, user, onLogout, loadConversations }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id: currentConversationId } = useParams();

  // Determine current view based on path for mobile nav highlighting
  const getCurrentView = () => {
    const path = location.pathname;
    if (path === "/" || path.startsWith("/chat")) return "chat";
    if (path.startsWith("/settings")) return "settings";
    if (path.startsWith("/personalities")) return "personalities";
    if (path.startsWith("/users")) return "users";
    if (path.startsWith("/dashboard")) return "dashboard";
    if (path.startsWith("/organizations")) return "organizations";
    if (path.startsWith("/account")) return "user-settings";
    return "";
  };

  const currentView = getCurrentView();

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={(id) => navigate(`/chat/${id}`)}
        onNewConversation={onNewConversation}
        currentView={currentView}
        onViewChange={(view) => {
          // Map view names to routes (for compatibility with existing Sidebar props if needed)
          // Ideally Sidebar should be refactored to use Links, but for now we adapt the handler
          if (view === "chat") navigate("/");
          else if (view === "settings") navigate("/settings");
          else if (view === "personalities") navigate("/personalities");
          else if (view === "users") navigate("/users");
          else if (view === "dashboard") navigate("/dashboard");
          else if (view === "organizations") navigate("/organizations");
          else if (view === "user-settings") navigate("/account");
        }}
        user={user}
        onLogout={onLogout}
      />
      <div className="main-content">
        <Outlet context={{ loadConversations }} />
      </div>

      {/* Mobile Bottom Navigation */}
      <div className="mobile-bottom-nav">
        <div className="mobile-nav-items">
          <div
            className={`mobile-nav-item ${currentView === "chat" ? "active" : ""}`}
            onClick={() => navigate("/")}
          >
            <MessageSquare className="mobile-nav-icon" />
            <span>Council</span>
          </div>
          {(user?.is_admin || user?.is_instance_admin) && (
            <div
              className={`mobile-nav-item ${["personalities", "users", "settings", "dashboard", "organizations"].includes(currentView) ? "active" : ""}`}
              onClick={() => navigate(user?.is_instance_admin ? "/dashboard" : "/personalities")}
            >
              <Settings className="mobile-nav-icon" />
              <span>Settings</span>
            </div>
          )}
          <Link to="/help" className="mobile-nav-item">
            <HelpCircle className="mobile-nav-icon" />
            <span>Help</span>
          </Link>
          <div
            className={`mobile-nav-item ${currentView === "user-settings" ? "active" : ""}`}
            onClick={() => navigate("/account")}
          >
            <User className="mobile-nav-icon" />
            <span>Account</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Layout;
