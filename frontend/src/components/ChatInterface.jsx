import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Trash2 } from "lucide-react";
import Stage1 from "./Stage1";
import Stage2 from "./Stage2";
import Stage3 from "./Stage3";
import "./ChatInterface.css";
import ContextualHelp from "./ContextualHelp";

export default function ChatInterface({ conversation, onSendMessage, onDelete, isLoading }) {
  const [consensusEnabled, setConsensusEnabled] = useState(false);
  const [input, setInput] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const scrollToLatest = (instant = false) => {
    // 1. Priority: Scroll to the last user message to keep context visible
    // This is crucial when assistant responses are very tall (Stages 1-3)
    const userMessages = messagesContainerRef.current?.querySelectorAll(".user-message");
    if (userMessages && userMessages.length > 0) {
      const lastUserMsg = userMessages[userMessages.length - 1];
      lastUserMsg.scrollIntoView({ behavior: instant ? "auto" : "smooth", block: "start" });
    } else {
      // Fallback: Scroll to bottom if no user message (e.g. system msg only)
      messagesEndRef.current?.scrollIntoView({ behavior: instant ? "auto" : "smooth" });
    }
  };

  useEffect(() => {
    // Scroll on initial load or conversation switch
    if (conversation?.messages?.length > 0) {
      scrollToLatest(true); // Instant on load
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversation?.id]); // Only on ID change (new conversation loaded)

  useEffect(() => {
    // Auto-scroll during streaming (when messages length changes or content updates)
    if (isLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [conversation?.messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input, consensusEnabled);
      setInput("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      setIsDeleting(true);
      try {
        await onDelete(conversation.id);
      } catch (error) {
        console.error("Delete failed", error);
        setIsDeleting(false);
      }
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>
          {conversation.title || "Conversation"} <ContextualHelp topic="stages" />
        </h2>
        <button
          className="btn-icon delete-btn"
          onClick={handleDelete}
          title="Delete Conversation"
          disabled={isDeleting}
        >
          <Trash2 size={20} />
        </button>
      </div>

      <div className="messages-container" ref={messagesContainerRef}>
        {!conversation.messages ||
        !Array.isArray(conversation.messages) ||
        conversation.messages.length === 0 ? (
          <div className="empty-state">
            {/* Empty state content moved to header but keeping placeholder if needed */}
            <p>Ask a question to consult the LLM Council</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === "user" ? (
                <div className="user-message">
                  <div className="message-label">You</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content || ""}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Council</div>

                  {/* Stage 1 */}
                  {msg.loading?.stage1 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 1: Collecting individual responses...</span>
                    </div>
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 */}
                  {msg.loading?.stage2 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 2: Peer rankings...</span>
                    </div>
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {/* Stage 3 */}
                  {msg.loading?.stage3 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 3: Final synthesis...</span>
                    </div>
                  )}
                  {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}
                </div>
              )}
            </div>
          ))
        )}

        {(isLoading || conversation.processing_state === "active") && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>
              {conversation.processing_state === "active"
                ? "Council is deliberating (Async)..."
                : "Consulting the council..."}
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <div className="consensus-toggle-container">
          <label className="toggle-label" title="Enable Strategic Consensus Mode">
            <input
              type="checkbox"
              checked={consensusEnabled}
              onChange={(e) => setConsensusEnabled(e.target.checked)}
            />
            <span className="toggle-text">Strategic Consensus</span>
          </label>
        </div>
        <textarea
          id="message-input"
          name="message"
          className="message-input"
          placeholder="Ask your question... (Shift+Enter for new line, Enter to send)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={3}
        />
        <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}
