import { useState, useEffect, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import PersonalityManager from "./components/PersonalityManager";
import LeagueTable from "./components/LeagueTable";
import EvolutionPanel from "./components/EvolutionPanel";
import SystemPromptsEditor from "./components/SystemPromptsEditor";
import UserManagement from "./components/UserManagement";
import VotingHistory from "./components/VotingHistory";
import OrgSettings from "./components/OrgSettings";
import OrganizationManagement from "./components/OrganizationManagement";
import Login from "./components/Login";
import AccordantLanding from "./components/AccordantLanding";
import { api } from "./api";
import { AuthProvider, useAuth } from "./context/AuthContext";
import "./App.css";

function Dashboard() {
  const { user, loading, logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  const [view, setView] = useState("chat"); // 'chat', 'personalities', 'prompts'

  const loadConversations = useCallback(async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }, []);

  const loadConversation = useCallback(async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error("Failed to load conversation:", error);
    }
  }, []);

  // Load conversations on mount or when user changes
  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadConversations();
    } else {
      // Clear state on logout
      setConversations([]);
      setCurrentConversationId(null);
      setCurrentConversation(null);
      setView("chat");
    }
  }, [user, loadConversations]);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadConversation(currentConversationId);
      setView("chat");
    }
  }, [currentConversationId, loadConversation]);

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
      setView("chat");
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    setView("chat");
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: "user", content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: "assistant",
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        // Normalize event type (trim whitespace, handle variations)
        const normalizedType = eventType?.trim();

        switch (normalizedType) {
          case "stage1_start":
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case "stage1_complete":
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data?.results || event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case "stage2_start":
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case "stage2_complete":
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data?.results || event.data;
              lastMsg.metadata = event.data?.metadata || event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case "stage3_start":
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case "stage3_complete":
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data?.results || event.data;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case "stage_start":
            // Generic stage_start event - we already handle specific stage starts above
            // This is just informational, so we can ignore it or use it for general loading state
            // Note: Backend sends this before stage1_start, stage2_start, stage3_start
            // Silently handle this event (no action needed as specific handlers cover it)
            break;

          case "title_complete":
            // Reload conversations to get updated title
            loadConversations();
            break;

          case "complete":
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case "error":
            console.error("Stream error:", event.message || event.data?.message);
            setIsLoading(false);
            break;

          default:
            // Silently ignore stage_start events (handled above) and only log truly unknown events
            const isStageStart = normalizedType === "stage_start" || eventType === "stage_start";
            if (!isStageStart) {
              console.debug("Unknown event type:", eventType, event);
            }
        }
      });
    } catch (error) {
      console.error("Failed to send message:", error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!user) {
    if (showLogin) {
      return <Login onBackToLanding={() => setShowLogin(false)} />;
    }
    return <AccordantLanding onShowLogin={() => setShowLogin(true)} />;
  }

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        currentView={view}
        onViewChange={setView}
        user={user}
        onLogout={logout}
      />
      <div className="main-content">
        {view === "chat" && (
          <ChatInterface
            conversation={currentConversation}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        )}
        {view === "personalities" && (user?.is_admin || user?.is_instance_admin) && (
          <PersonalityManager />
        )}
        {view === "prompts" && (user?.is_admin || user?.is_instance_admin) && (
          <SystemPromptsEditor />
        )}
        {view === "league" && (user?.is_admin || user?.is_instance_admin) && (
          <div className="section-container">
            <h2>Personality League Table</h2>
            <LeagueTable isInstanceAdmin={user?.is_instance_admin} />
          </div>
        )}
        {view === "evolution" && (user?.is_admin || user?.is_instance_admin) && (
          <div className="section-container">
            <h2>Board Evolution</h2>
            <EvolutionPanel />
          </div>
        )}
        {view === "users" && (user?.is_admin || user?.is_instance_admin) && <UserManagement />}
        {view === "organizations" && user?.is_instance_admin && <OrganizationManagement />}
        {view === "voting_history" && (user?.is_admin || user?.is_instance_admin) && (
          <VotingHistory />
        )}
        {view === "settings" && (user?.is_admin || user?.is_instance_admin) && <OrgSettings />}
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Dashboard />
    </AuthProvider>
  );
}

export default App;
