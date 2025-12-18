import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useOutletContext } from "react-router-dom";
import ChatInterface from "../components/ChatInterface";
import { api } from "../api";

const ChatPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { loadConversations } = useOutletContext();

  const [conversation, setConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadConversation = useCallback(
    async (convId) => {
      try {
        const conv = await api.getConversation(convId);
        setConversation(conv);
      } catch (error) {
        console.error("Failed to load conversation:", error);
        // If not found, maybe redirect to home?
        // check error status if possible, for now just log
        if (error?.status === 404) {
          navigate("/");
        }
      }
    },
    [navigate]
  );

  useEffect(() => {
    if (id) {
      loadConversation(id);
    } else {
      // No ID means new chat or empty state?
      // Typically /chat/:id. If we are at /, we might show a "Select a chat" or "New Chat" view
      // But for now, App.jsx treated "no id" as empty.
      setConversation(null);
    }
  }, [id, loadConversation]);

  const handleSendMessage = async (content, consensusEnabled = false) => {
    if (!id) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: "user", content };
      setConversation((prev) => ({
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

      setConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      await api.sendMessageStream(id, content, consensusEnabled, (eventType, event) => {
        const normalizedType = eventType?.trim();

        switch (normalizedType) {
          case "stage1_start": {
            setConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.loading.stage1 = true;
              }
              return { ...prev, messages };
            });
            break;
          }

          case "stage1_complete": {
            setConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.stage1 = event.data?.results || event.data;
                lastMsg.loading.stage1 = false;
              }
              return { ...prev, messages };
            });
            break;
          }

          case "stage2_start": {
            setConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.loading.stage2 = true;
              }
              return { ...prev, messages };
            });
            break;
          }

          case "stage2_complete": {
            setConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.stage2 = event.data?.results || event.data;
                lastMsg.metadata = event.data?.metadata || event.metadata;
                lastMsg.loading.stage2 = false;
              }
              return { ...prev, messages };
            });
            break;
          }

          case "stage3_start": {
            setConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.loading.stage3 = true;
              }
              return { ...prev, messages };
            });
            break;
          }

          case "stage3_complete": {
            setConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === "assistant") {
                lastMsg.stage3 = event.data?.results || event.data;
                lastMsg.loading.stage3 = false;
              }
              return { ...prev, messages };
            });
            break;
          }

          case "title_complete":
            loadConversations();
            break;

          case "complete":
            loadConversations();
            setIsLoading(false);
            break;

          case "error":
            console.error("Stream error:", event.message || event.data?.message);
            setIsLoading(false);
            break;

          default:
            break;
        }
      });
    } catch (error) {
      console.error("Failed to send message:", error);
      setConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2), // Remove pessimistic messages
      }));
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (convId) => {
    try {
      await api.deleteConversation(convId);
      // Refresh list
      loadConversations();
      // Navigate away if current
      if (convId === id) {
        navigate("/");
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      alert("Failed to delete conversation.");
    }
  };

  if (!id) {
    return (
      <div className="empty-state">
        <div className="empty-state-content">
          <h2>Select a conversation or start a new one</h2>
        </div>
      </div>
    );
  }

  return (
    <ChatInterface
      conversation={conversation}
      onSendMessage={handleSendMessage}
      onDelete={handleDeleteConversation}
      isLoading={isLoading}
    />
  );
};

export default ChatPage;
