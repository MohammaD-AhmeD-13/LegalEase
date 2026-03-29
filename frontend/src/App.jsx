import { useEffect, useMemo, useState } from "react";

const EXAMPLES = [
  {
    label: "Business",
    prompt: "Summarize the key obligations under section 1 of the Companies Act, 2017."
  },
  {
    label: "Employment",
    prompt: "Explain the employer obligations for employee termination under Pakistani labor law."
  },
  {
    label: "Contract",
    prompt: "What are the core requirements for a valid contract under the Contract Act, 1872?"
  },
  {
    label: "Tax",
    prompt: "List the main penalties for non-compliance in the Income Tax Ordinance, 2001."
  },
  {
    label: "Risk",
    prompt: "What risks should I watch for in a standard service agreement?"
  }
];

const DEFAULT_TOP_K = 3;
const DEFAULT_MAX_TOKENS = 128;
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const createTempId = () => `temp-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const formatTimestamp = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
};

const buildUrl = (path) => (API_BASE_URL ? `${API_BASE_URL}${path}` : path);

const requestJson = async (path, options = {}) => {
  const response = await fetch(buildUrl(path), {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    let detail = "";
    if (contentType.includes("application/json")) {
      const data = await response.json().catch(() => null);
      detail = data?.detail || JSON.stringify(data || {});
    } else {
      const text = await response.text();
      try {
        const parsed = JSON.parse(text);
        detail = parsed?.detail || text;
      } catch {
        detail = text;
      }
    }
    throw new Error(detail || "Request failed");
  }
  return response.json();
};

export default function App() {
  const [user, setUser] = useState(null);
  const [authView, setAuthView] = useState("login");
  const [authForm, setAuthForm] = useState({ name: "", email: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);

  const [query, setQuery] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState("en");
  const [exampleIndex, setExampleIndex] = useState(0);
  const [abortController, setAbortController] = useState(null);

  const canSubmit = useMemo(() => query.trim().length >= 3 && !loading, [query, loading]);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const data = await requestJson("/auth/me");
        setUser(data.user);
        await loadChats();
      } catch (err) {
        setUser(null);
      }
    };
    loadSession();
  }, []);

  const loadChats = async () => {
    const data = await requestJson("/chats");
    setChats(data.chats || []);
    if (data.chats && data.chats.length > 0) {
      await selectChat(data.chats[0].id);
    }
  };

  const selectChat = async (chatId) => {
    const data = await requestJson(`/chats/${chatId}`);
    setActiveChatId(chatId);
    setMessages(data.messages || []);
    setSources([]);
    setError("");
  };

  const startNewChat = async () => {
    const data = await requestJson("/chats", {
      method: "POST",
      body: JSON.stringify({ title: "New chat" })
    });
    setChats((prev) => [data.chat, ...prev]);
    setActiveChatId(data.chat.id);
    setMessages([]);
    setSources([]);
    setQuery("");
  };

  const updateChatTitle = (chatId, title) => {
    if (!title) return;
    setChats((prev) =>
      prev.map((chat) => (chat.id === chatId ? { ...chat, title, updated_at: new Date().toISOString() } : chat))
    );
  };

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    setAuthError("");

    try {
      const endpoint = authView === "login" ? "/auth/login" : "/auth/signup";
      const payload = authView === "login"
        ? { email: authForm.email, password: authForm.password }
        : { name: authForm.name, email: authForm.email, password: authForm.password };

      const data = await requestJson(endpoint, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setUser(data.user);
      await loadChats();
    } catch (err) {
      const message = err.message || "Authentication failed.";
      if (message.includes("Invalid credentials")) {
        setAuthError("Email or password is incorrect.");
      } else {
        setAuthError(message);
      }
    }
  };

  const handleLogout = async () => {
    try {
      await requestJson("/auth/logout", { method: "POST" });
    } finally {
      setUser(null);
      setChats([]);
      setMessages([]);
      setActiveChatId(null);
    }
  };

  const handleSubmit = async (event) => {
    if (event?.preventDefault) {
      event.preventDefault();
    }
    const trimmed = query.trim();
    if (loading) return;
    if (trimmed.length < 3) {
      setError("Please enter at least 3 characters.");
      return;
    }
    const userMessage = {
      id: createTempId(),
      role: "user",
      content: trimmed
    };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setError("");
    setSources([]);

    let chatId = activeChatId;
    if (!chatId) {
      try {
        const data = await requestJson("/chats", {
          method: "POST",
          body: JSON.stringify({ title: "New chat" })
        });
        chatId = data.chat.id;
        setChats((prev) => [data.chat, ...prev]);
        setActiveChatId(chatId);
      } catch (err) {
        setError(err.message || "Unable to create a chat yet.");
      }
    }

    const controller = new AbortController();
    setAbortController(controller);
    setLoading(true);

    try {
      const data = await requestJson("/rag/answer", {
        method: "POST",
        signal: controller.signal,
        body: JSON.stringify({
          query: trimmed,
          top_k: DEFAULT_TOP_K,
          max_new_tokens: DEFAULT_MAX_TOKENS,
          language,
          ...(chatId ? { chat_id: chatId } : {})
        })
      });

      const assistantMessage = {
        id: createTempId(),
        role: "assistant",
        content: data.answer || "",
        language: data.language || language
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setSources(data.sources || []);
      updateChatTitle(chatId, data.chat_title);
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Something went wrong.");
      }
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
    }
  };

  const handleExample = () => {
    const nextIndex = (exampleIndex + 1) % EXAMPLES.length;
    const nextPrompt = EXAMPLES[nextIndex].prompt;
    setExampleIndex(nextIndex);
    setQuery(nextPrompt);
    setError("");
    setSources([]);
    setTimeout(() => {
      const input = document.getElementById("query");
      if (input) {
        input.focus();
      }
    }, 0);
  };

  const handleComposerKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  if (!user) {
    return (
      <div className="auth">
        <div className="auth__panel">
          <div className="auth__brand">
            <h1>LegalEase</h1>
          </div>
          <div className="auth__tabs">
            <button
              type="button"
              className={authView === "login" ? "tab is-active" : "tab"}
              onClick={() => setAuthView("login")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={authView === "signup" ? "tab is-active" : "tab"}
              onClick={() => setAuthView("signup")}
            >
              Create account
            </button>
          </div>
          <form className="auth__form" onSubmit={handleAuthSubmit}>
            {authView === "signup" && (
              <label>
                Full name
                <input
                  type="text"
                  value={authForm.name}
                  onChange={(event) => setAuthForm((prev) => ({ ...prev, name: event.target.value }))}
                  required
                />
              </label>
            )}
            <label>
              Email
              <input
                type="email"
                value={authForm.email}
                onChange={(event) => setAuthForm((prev) => ({ ...prev, email: event.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <div className="input-with-action">
                <input
                  type={showPassword ? "text" : "password"}
                  value={authForm.password}
                  onChange={(event) => setAuthForm((prev) => ({ ...prev, password: event.target.value }))}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((prev) => !prev)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>
            {authError && <p className="error">{authError}</p>}
            <button type="submit" className="btn btn-primary">
              {authView === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar__top">
          <button type="button" className="btn btn-primary" onClick={startNewChat}>
            New chat
          </button>
          <button type="button" className="btn btn-secondary" onClick={handleExample}>
            Try example
          </button>
        </div>
        <div className="sidebar__examples">
          <div className="sidebar__heading">Example scenarios</div>
          <div className="example-tags">
            {EXAMPLES.map((item) => (
              <span key={item.label} className="example-tag">{item.label}</span>
            ))}
          </div>
        </div>
        <div className="sidebar__section">
          <div className="sidebar__heading">Chats</div>
          <ul className="chat-list">
            {chats.map((chat) => (
              <li key={chat.id}>
                <button
                  type="button"
                  className={activeChatId === chat.id ? "chat-list__item is-active" : "chat-list__item"}
                  onClick={() => selectChat(chat.id)}
                >
                  <span className="chat-list__title">{chat.title}</span>
                  <span className="chat-list__time">{formatTimestamp(chat.updated_at)}</span>
                </button>
              </li>
            ))}
            {!chats.length && <li className="chat-list__empty">No chats yet.</li>}
          </ul>
        </div>
        <div className="sidebar__bottom">
          <button type="button" className="sidebar__link">Settings</button>
          <div className="user-card">
            <div className="user-card__avatar">
              {user.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}
            </div>
            <div className="user-card__info">
              <p>{user.name}</p>
              <span>{user.email}</span>
            </div>
            <button type="button" className="user-card__logout" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="topbar__brand">
            <span className="topbar__brand-text">LegalEase</span>
          </div>
          <div className="topbar__badge">Secure workspace</div>
        </header>

        <section className="chat-window">
          <div className="chat-messages">
            {!messages.length && !error && <div className="empty-state" />}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message-row ${message.role === "user" ? "is-user" : "is-assistant"} ${message.language === "ur" ? "is-urdu" : ""}`}
              >
                <div className="message-card">
                  <p>{message.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="message-row is-assistant">
                <div className="message-card is-loading">
                  <p>Thinking…</p>
                </div>
              </div>
            )}
            {error && <p className="error">{error}</p>}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <div className="composer__actions">
              <button type="button" className="icon-btn" disabled title="Upload documents">
                Upload
              </button>
              <button type="button" className="icon-btn" disabled title="Voice input">
                Voice
              </button>
            </div>
            <label className="sr-only" htmlFor="query">Ask a legal question</label>
            <textarea
              id="query"
              rows="2"
              placeholder="Send a message"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={handleComposerKeyDown}
            />
            <div className="composer__controls">
              {loading ? (
                <button type="button" className="btn btn-secondary" onClick={handleStop}>
                  Stop
                </button>
              ) : (
                <button type="button" className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
                  Send
                </button>
              )}
            </div>
          </form>

          <div className="bottom-panel">
            <div className="bottom-panel__left">
              <span className="bottom-panel__label">Response language</span>
              <div className="segmented" role="group" aria-label="Response language">
                <button
                  type="button"
                  className={language === "en" ? "segmented__btn is-active" : "segmented__btn"}
                  onClick={() => setLanguage("en")}
                >
                  English
                </button>
                <button
                  type="button"
                  className={language === "ur" ? "segmented__btn is-active" : "segmented__btn"}
                  onClick={() => setLanguage("ur")}
                >
                  Urdu
                </button>
              </div>
            </div>
            <details className="sources-panel">
              <summary>Sources</summary>
              {!sources.length && <p className="muted">No sources yet.</p>}
              {sources.length > 0 && (
                <ul className="sources">
                  {sources.map((item) => (
                    <li key={item.chunk_id}>
                      <div className="source__meta">
                        <strong>{item.law_name}</strong>
                        <span>§ {item.section_id}</span>
                        <span>Score {item.score?.toFixed(3)}</span>
                      </div>
                      <p>{item.text}</p>
                    </li>
                  ))}
                </ul>
              )}
            </details>
          </div>
        </section>
      </main>
    </div>
  );
}
