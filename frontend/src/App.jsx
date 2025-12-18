import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Layout from "./components/Layout";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage"; // Admin Dashboard
import PersonalitiesPage from "./pages/PersonalitiesPage";
import UsersPage from "./pages/UsersPage";
import OrganizationsPage from "./pages/OrganizationsPage";
import SettingsPage from "./pages/SettingsPage";
import UserSettingsPage from "./pages/UserSettingsPage";
import DocPage from "./pages/DocPage";

import Login from "./components/Login";
import AccordantLanding from "./components/AccordantLanding";
import { api } from "./api";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { initAnalytics } from "./utils/analytics";
import "./App.css";

// Wrapper to provide Router context
function AppRouterWrapper() {
  return (
    <BrowserRouter>
      <AppContentWithRouter />
    </BrowserRouter>
  );
}

function AppContentWithRouter() {
  const { user, loading, logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
  const navigate = useNavigate(); // Now safe to use

  const loadConversations = useCallback(async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }, []);

  useEffect(() => {
    if (user) {
      loadConversations();
    } else {
      setConversations([]);
    }
  }, [user, loadConversations]);

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      navigate(`/chat/${newConv.id}`);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  if (loading) return <div className="loading-screen">Loading...</div>;

  if (!user) {
    if (showLogin) return <Login onBackToLanding={() => setShowLogin(false)} />;
    return <AccordantLanding onShowLogin={() => setShowLogin(true)} />;
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          <Layout
            conversations={conversations}
            onNewConversation={handleNewConversation}
            user={user}
            onLogout={logout}
            loadConversations={loadConversations}
          />
        }
      >
        <Route index element={<ChatPage />} />
        <Route path="chat/:id" element={<ChatPage />} />

        <Route
          path="settings"
          element={user.is_admin || user.is_instance_admin ? <SettingsPage /> : <Navigate to="/" />}
        />
        <Route
          path="personalities"
          element={
            user.is_admin || user.is_instance_admin ? <PersonalitiesPage /> : <Navigate to="/" />
          }
        />
        <Route
          path="users"
          element={user.is_admin || user.is_instance_admin ? <UsersPage /> : <Navigate to="/" />}
        />
        <Route
          path="dashboard"
          element={user.is_instance_admin ? <DashboardPage /> : <Navigate to="/" />}
        />
        <Route
          path="organizations"
          element={user.is_instance_admin ? <OrganizationsPage /> : <Navigate to="/" />}
        />
        <Route path="account" element={<UserSettingsPage />} />

        <Route path="privacy" element={<DocPage docId="privacy" title="Privacy Policy" />} />
        <Route path="terms" element={<DocPage docId="terms" title="Terms of Use" />} />
        <Route path="faq" element={<DocPage docId="faq" title="FAQ" />} />
        <Route path="help" element={<DocPage docId="manual" title="User Manual" />} />

        <Route path="*" element={<Navigate to="/" />} />
      </Route>
    </Routes>
  );
}

function App() {
  useEffect(() => {
    initAnalytics();
  }, []);

  return (
    <AuthProvider>
      <AppRouterWrapper />
    </AuthProvider>
  );
}

export default App;
