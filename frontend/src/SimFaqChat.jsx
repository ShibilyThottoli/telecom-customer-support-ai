import { useEffect, useRef, useState } from "react";
import { Bot, MessageSquarePlus, Send, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const SESSION_STORAGE_KEY = "lauki-faq-session-id";

const GREETING = {
  id: "greeting",
  role: "assistant",
  content: "Hi! I’m your Lauki Phones assistant. What can I help you with?",
};

const SUGGESTED_QUESTIONS = [
  "How do I activate a new SIM?",
  "How do I check my data balance?",
  "How do I pay my bill?",
  "How do I switch from physical SIM to eSIM?",
  "What ID documents are accepted for KYC?",
  "Can I transfer ownership of my number?",
];

function createSessionId() {
  const sessionId = crypto.randomUUID();
  sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

function getSessionId() {
  return sessionStorage.getItem(SESSION_STORAGE_KEY) || createSessionId();
}

function ChatBubble({ message }) {
  if (message.role === "error") {
    return (
      <div className="sim-chat-row assistant-row">
        <div className="sim-chat-avatar assistant-avatar" aria-hidden="true">
          <Bot size={18} />
        </div>
        <div className="sim-chat-bubble error-bubble" role="alert">
          {message.content}
        </div>
      </div>
    );
  }

  const isUser = message.role === "user";
  return (
    <div className={`sim-chat-row ${isUser ? "user-row" : "assistant-row"}`}>
      {!isUser && (
        <div className="sim-chat-avatar assistant-avatar" aria-hidden="true">
          <Bot size={18} />
        </div>
      )}
      <div
        className={`sim-chat-bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}
      >
        {isUser ? (
          message.content
        ) : (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="sim-chat-row assistant-row">
      <div className="sim-chat-avatar assistant-avatar" aria-hidden="true">
        <Bot size={18} />
      </div>
      <div
        className="sim-chat-bubble assistant-bubble typing-bubble"
        aria-label="Lauki Phones assistant is typing"
        role="status"
      >
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}

export default function SimFaqChat() {
  const [sessionId, setSessionId] = useState(getSessionId);
  const [messages, setMessages] = useState([GREETING]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      try {
        const response = await fetch(
          `${API_URL}/sessions/${encodeURIComponent(sessionId)}/history`,
        );
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || "Could not restore this conversation.");
        }
        if (!Array.isArray(data.messages)) {
          throw new Error("The server returned invalid conversation history.");
        }

        const history = data.messages.map((message, index) => {
          if (
            !message ||
            !["user", "assistant"].includes(message.role) ||
            typeof message.content !== "string"
          ) {
            throw new Error("The server returned an invalid conversation message.");
          }
          return { ...message, id: `history-${index}` };
        });

        if (!cancelled) setMessages([GREETING, ...history]);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError.message);
          setMessages([GREETING]);
        }
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading, historyLoading]);

  const sendMessage = async (text = draft) => {
    const message = text.trim();
    if (!message || loading || historyLoading || clearing) return;

    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: message },
    ]);
    setDraft("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "The assistant couldn't reply. Please try again.");
      }
      if (typeof data.answer !== "string" || !data.answer.trim()) {
        throw new Error("The assistant returned an empty response. Please try again.");
      }

      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", content: data.answer },
      ]);
    } catch (requestError) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "error",
          content: requestError.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    if (loading || clearing) return;
    const newSessionId = createSessionId();
    setHistoryLoading(true);
    setSessionId(newSessionId);
    setMessages([GREETING]);
    setDraft("");
    setError("");
  };

  const clearMemory = async () => {
    if (loading || clearing || historyLoading) return;
    setClearing(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/sessions/${encodeURIComponent(sessionId)}/history`,
        { method: "DELETE" },
      );
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Could not clear this conversation.");
      }

      setMessages([GREETING]);
    } catch (clearError) {
      setError(clearError.message);
    } finally {
      setClearing(false);
    }
  };

  const busy = loading || historyLoading || clearing;
  const recentQuestions = messages
    .filter((message) => message.role === "user")
    .slice(-5)
    .reverse();

  return (
    <main className="sim-chat-stage">
      <div className="sim-chat-shell">
        <aside className="sim-chat-sidebar" aria-label="Recent chats">
          <div className="sim-sidebar-brand">
            <div className="sim-chat-brand-icon" aria-hidden="true">
              <Bot size={26} />
            </div>
            <div>
              <strong>Lauki Phones</strong>
              <span>Your FAQ assistant</span>
            </div>
          </div>
          <button
            className="sidebar-new-chat-button"
            type="button"
            onClick={startNewChat}
            disabled={busy}
          >
            <MessageSquarePlus size={18} />
            New chat
          </button>
          <h2 className="sidebar-heading">Recent chats</h2>
          <div className="recent-chat-list">
            {recentQuestions.length ? (
              recentQuestions.map((message) => (
                <button
                  className="recent-chat-item"
                  type="button"
                  key={message.id}
                  onClick={() => setDraft(message.content)}
                  title="Use this question again"
                  disabled={busy}
                >
                  <MessageSquarePlus size={16} aria-hidden="true" />
                  <span>
                    {message.content}
                    <small>Current conversation</small>
                  </span>
                </button>
              ))
            ) : (
              <p className="recent-chat-empty">
                Your recent questions will appear here.
              </p>
            )}
          </div>
        </aside>

        <section className="sim-chat-panel" aria-label="Lauki Phones FAQ Assistant">
          <header className="sim-chat-header">
            <div className="sim-chat-brand-icon" aria-hidden="true">
              <Bot size={22} />
            </div>
            <div className="sim-chat-brand">
              <strong>Lauki Phones</strong>
              <span className="sim-chat-status">
                <span className="status-dot" />
                Customer support
              </span>
            </div>
            <button
              className="new-chat-button"
              type="button"
              onClick={startNewChat}
              disabled={busy}
            >
              <MessageSquarePlus size={16} />
              New chat
            </button>
            <button
              className="clear-memory-button"
              type="button"
              onClick={clearMemory}
              disabled={busy || messages.length <= 1}
              aria-label="Clear conversation memory"
              title="Clear conversation memory"
            >
              <Trash2 size={17} />
            </button>
          </header>

          <div
            className="sim-chat-messages"
            role="log"
            aria-live="polite"
            aria-label="Conversation"
          >
            {historyLoading ? (
              <div className="conversation-status">Restoring your conversation…</div>
            ) : (
              messages.map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))
            )}
            {error && <div className="conversation-error" role="alert">{error}</div>}
            {loading && <TypingIndicator />}
            <div ref={endRef} />
          </div>

          <div className="suggested-questions" aria-label="Suggested questions">
            {SUGGESTED_QUESTIONS.map((question) => (
              <button
                className="suggestion-chip"
                type="button"
                key={question}
                onClick={() => sendMessage(question)}
                disabled={busy}
              >
                {question}
              </button>
            ))}
          </div>

          <form
            className="sim-chat-composer"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
          >
            <input
              className="sim-chat-input"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about Lauki Phones…"
              aria-label="Type your question"
              disabled={busy}
            />
            <button
              className="sim-chat-send"
              type="submit"
              aria-label="Send message"
              disabled={!draft.trim() || busy}
            >
              <Send size={19} />
            </button>
          </form>
          <p className="sim-chat-disclaimer">
            AI-generated answers may contain mistakes.
          </p>
        </section>
      </div>
    </main>
  );
}
