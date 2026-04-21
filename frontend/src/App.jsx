import { useEffect, useMemo, useRef, useState } from "react";

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
  const { allow401 = false, ...fetchOptions } = options;
  const response = await fetch(buildUrl(path), {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(fetchOptions.headers || {})
    },
    ...fetchOptions
  });

  if (!response.ok) {
    if (response.status === 401 && allow401) {
      return { unauthenticated: true };
    }
    if (response.status === 401 && !path.startsWith("/auth/")) {
      const authError = new Error("Not authenticated");
      authError.name = "AuthError";
      throw authError;
    }
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

const requestForm = async (path, formData) => {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    credentials: "include",
    body: formData
  });

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/")) {
      const authError = new Error("Not authenticated");
      authError.name = "AuthError";
      throw authError;
    }
    const contentType = response.headers.get("content-type") || "";
    let detail = "";
    if (contentType.includes("application/json")) {
      const data = await response.json().catch(() => null);
      detail = data?.detail || JSON.stringify(data || {});
    } else {
      detail = await response.text();
    }
    throw new Error(detail || "Request failed");
  }
  return response.json();
};

const formatReviewMessage = (filename, review) => {
  const lines = [];
  lines.push(`Document review: ${filename}`);
  lines.push("");
  if (review.summary) {
    lines.push("Summary:");
    lines.push(review.summary);
    lines.push("");
  }
  lines.push("Risky clauses:");
  if (review.risky_clauses?.length) {
    review.risky_clauses.forEach((item, index) => {
      const severity = (item.severity || "Medium").toUpperCase();
      lines.push(`${index + 1}. [${severity}] ${item.reason}`);
      lines.push(`   Clause: ${item.clause}`);
    });
  } else {
    lines.push("- No risky clauses found.");
  }
  lines.push("");
  lines.push("Compliance issues:");
  if (review.compliance_issues?.length) {
    review.compliance_issues.forEach((issue) => {
      lines.push(`- ${issue.issue}: ${issue.reason}`);
    });
  } else {
    lines.push("- None flagged.");
  }
  lines.push("");
  lines.push("Recommendations:");
  if (review.recommendations?.length) {
    review.recommendations.forEach((item) => lines.push(`- ${item}`));
  } else {
    lines.push("- None provided.");
  }
  return lines.join("\n");
};

const ensureSummaryHeading = (summary) => {
  const trimmed = (summary || "").trim();
  if (!trimmed) {
    return "Summary:\nNo summary returned.";
  }
  const lines = trimmed.split("\n").map((line) => line.trim());
  const cleanedLines = [];
  let summarySeen = false;
  for (const line of lines) {
    if (/^summary:\s*$/i.test(line)) {
      if (summarySeen) {
        continue;
      }
      summarySeen = true;
      cleanedLines.push("Summary:");
      continue;
    }
    cleanedLines.push(line);
  }
  if (!summarySeen) {
    return `Summary:\n${cleanedLines.join("\n").trim()}`;
  }
  return cleanedLines.join("\n").trim();
};

const formatSummaryMessage = (summary) => ensureSummaryHeading(summary);

const downloadPdf = (base64, filename) => {
  if (!base64) return;
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i += 1) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const blob = new Blob([new Uint8Array(byteNumbers)], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || "document.pdf";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const renderInline = (text, keyPrefix) => {
  const parts = String(text || "").split("**");
  return parts.map((part, index) =>
    index % 2 === 1
      ? <strong key={`${keyPrefix}-b-${index}`}>{part}</strong>
      : <span key={`${keyPrefix}-t-${index}`}>{part}</span>
  );
};

const renderMessageContent = (content) => {
  const lines = String(content || "").split("\n");
  const blocks = [];
  let listItems = [];

  const flushList = () => {
    if (listItems.length) {
      blocks.push({ type: "list", items: listItems });
      listItems = [];
    }
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    const bulletMatch = /^[-*]\s+(.+)/.exec(trimmed);
    if (bulletMatch) {
      listItems.push(bulletMatch[1]);
      return;
    }
    flushList();
    if (!trimmed) {
      blocks.push({ type: "spacer" });
      return;
    }
    if (/:$/.test(trimmed)) {
      blocks.push({ type: "heading", text: trimmed });
      return;
    }
    blocks.push({ type: "text", text: trimmed });
  });
  flushList();

  return blocks.map((block, index) => {
    if (block.type === "heading") {
      return (
        <p key={`h-${index}`} className="message-heading">
          {renderInline(block.text, `h-${index}`)}
        </p>
      );
    }
    if (block.type === "list") {
      return (
        <ul key={`l-${index}`} className="message-list">
          {block.items.map((item, itemIndex) => (
            <li key={`li-${index}-${itemIndex}`}>{renderInline(item, `li-${index}-${itemIndex}`)}</li>
          ))}
        </ul>
      );
    }
    if (block.type === "spacer") {
      return <div key={`s-${index}`} className="message-spacer" />;
    }
    return (
      <p key={`p-${index}`}>
        {renderInline(block.text, `p-${index}`)}
      </p>
    );
  });
};

const truncateTitle = (title, maxLength = 28) => {
  const value = String(title || "").trim();
  if (value.length <= maxLength) return value;
  return `${value.slice(0, Math.max(0, maxLength - 3))}...`;
};

const findGeneratedDocumentMessage = (chatMessages, title) => {
  if (!Array.isArray(chatMessages) || !title) return null;
  const target = `Generate document: ${title}`;
  for (let index = chatMessages.length - 1; index >= 0; index -= 1) {
    const message = chatMessages[index];
    if (message.role === "user" && message.content === target) {
      const next = chatMessages[index + 1];
      if (next && next.role === "assistant") {
        return next;
      }
    }
  }
  return null;
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
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewMode, setReviewMode] = useState("summary");
  const [reviewFile, setReviewFile] = useState(null);
  const [reviewError, setReviewError] = useState("");
  const [reviewResult, setReviewResult] = useState(null);
  const [reviewing, setReviewing] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [translatedMessages, setTranslatedMessages] = useState({});
  const [showTranslations, setShowTranslations] = useState(false);
  const [translatingMessages, setTranslatingMessages] = useState(false);
  const [translationError, setTranslationError] = useState("");

  const [templates, setTemplates] = useState([]);
  const [templateId, setTemplateId] = useState("");
  const [templateFields, setTemplateFields] = useState({});
  const [templateError, setTemplateError] = useState("");
  const [polishWithLlm, setPolishWithLlm] = useState(false);
  const [generatingDocument, setGeneratingDocument] = useState(false);
  const [lastGenerated, setLastGenerated] = useState(null);
  const [editedDocument, setEditedDocument] = useState("");
  const [generatorView, setGeneratorView] = useState(false);
  const [riskView, setRiskView] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [generatedDocsByChat, setGeneratedDocsByChat] = useState({});
  const [editedDocsByChat, setEditedDocsByChat] = useState({});
  const [generatedDocs, setGeneratedDocs] = useState([]);
  const editorRef = useRef(null);

  const userInitials = useMemo(() => {
    if (!user?.name) return "LE";
    return user.name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  }, [user]);

  const isFullWidthField = (field) =>
    /purpose|description|scope|details|notes|consideration/i.test(`${field?.label || ""} ${field?.key || ""}`);

  const canSubmit = useMemo(() => query.trim().length >= 3 && !loading, [query, loading]);
  const selectedTemplate = useMemo(
    () => templates.find((template) => template.id === templateId) || null,
    [templates, templateId]
  );

  useEffect(() => {
    const loadSession = async () => {
      try {
        const data = await requestJson("/auth/me", { allow401: true });
        if (data?.unauthenticated) {
          setUser(null);
          return;
        }
        setUser(data.user);
        await loadTemplates();
        await loadChats();
        await loadDocumentBadges();
      } catch (err) {
        setUser(null);
      }
    };
    loadSession();
  }, []);

  const handleAuthFailure = () => {
    setUser(null);
    setChats([]);
    setMessages([]);
    setActiveChatId(null);
    setError("");
    setTemplates([]);
    setTemplateId("");
    setTemplateFields({});
    setTemplateError("");
    setPolishWithLlm(false);
    setGeneratingDocument(false);
    setLastGenerated(null);
    setGeneratedDocsByChat({});
    setEditedDocsByChat({});
    setGeneratedDocs([]);
    setTranslatedMessages({});
    setShowTranslations(false);
    setTranslatingMessages(false);
    setTranslationError("");
  };

  const initializeTemplateFields = (template) => {
    if (!template?.fields) return {};
    return template.fields.reduce((acc, field) => {
      const defaultValue = field.default || "";
      acc[field.key] = defaultValue;
      return acc;
    }, {});
  };

  const loadTemplates = async () => {
    try {
      const data = await requestJson("/documents/templates");
      const templatesList = Array.isArray(data) ? data : [];
      setTemplates(templatesList);
      if (templatesList.length) {
        const first = templatesList[0];
        setTemplateId(first.id);
        setTemplateFields(initializeTemplateFields(first));
        setTemplateError("");
      }
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setTemplateError(err.message || "Unable to load templates.");
    }
  };

  const loadDocumentBadges = async () => {
    try {
      const data = await requestJson("/documents/badges");
      setGeneratedDocs(Array.isArray(data) ? data : []);
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
    }
  };

  const loadChats = async () => {
    try {
      const data = await requestJson("/chats");
      setChats(data.chats || []);
      if (data.chats && data.chats.length > 0) {
        await selectChat(data.chats[0].id);
      }
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      throw err;
    }
  };

  const selectChat = async (chatId, options = {}) => {
    try {
      const data = await requestJson(`/chats/${chatId}`);
      setActiveChatId(chatId);
      setMessages(data.messages || []);
      setSources([]);
      setError("");
      setShowTranslations(false);
      setTranslatedMessages({});
      setTranslationError("");
      setRiskView(false);
      if (options.openDocumentTitle) {
        const matched = findGeneratedDocumentMessage(data.messages || [], options.openDocumentTitle);
        if (matched) {
          const docPayload = {
            title: options.openDocumentTitle,
            content: matched.content,
            filename: null,
            pdfBase64: null
          };
          setLastGenerated(docPayload);
          setEditedDocument(matched.content || "");
          setGeneratorView(true);
          setShowEditor(true);
          setTemplateError("");
        } else {
          setLastGenerated(null);
          setEditedDocument("");
          setGeneratorView(true);
          setShowEditor(false);
          setTemplateError("Unable to load this document from the chat history yet.");
        }
        return;
      }
      const storedDoc = generatedDocsByChat[chatId];
      if (storedDoc) {
        const storedEdit = editedDocsByChat[chatId] || storedDoc.content || "";
        setLastGenerated(storedDoc);
        setEditedDocument(storedEdit);
        setGeneratorView(true);
        setShowEditor(true);
      } else {
        setGeneratorView(false);
        setShowEditor(false);
      }
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      throw err;
    }
  };

  const handleOpenDocumentBadge = async (doc) => {
    if (!doc?.chat_id) {
      setLastGenerated(null);
      setEditedDocument("");
      setGeneratorView(true);
      setRiskView(false);
      setShowEditor(false);
      setTemplateError("This document is not linked to a chat yet.");
      return;
    }
    try {
      await selectChat(doc.chat_id, { openDocumentTitle: doc.title });
    } catch (err) {
      setError(err.message || "Unable to open this document.");
    }
  };

  const startNewChat = async () => {
    setGeneratorView(false);
    setRiskView(false);
    setShowEditor(false);
    try {
      const data = await requestJson("/chats", {
        method: "POST",
        body: JSON.stringify({ title: "New chat" })
      });
      setChats((prev) => [data.chat, ...prev]);
      setActiveChatId(data.chat.id);
      setMessages([]);
      setSources([]);
      setQuery("");
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      throw err;
    }
  };

  const updateChatTitle = (chatId, title) => {
    if (!title) return;
    setChats((prev) =>
      prev.map((chat) => (chat.id === chatId ? { ...chat, title, updated_at: new Date().toISOString() } : chat))
    );
  };

  const handleDeleteChat = async (chatId) => {
    const chat = chats.find((item) => item.id === chatId);
    if (!chat) return;
    const confirmed = window.confirm(`Delete chat "${chat.title}"? This cannot be undone.`);
    if (!confirmed) return;

    try {
      await requestJson(`/chats/${chatId}`, { method: "DELETE" });
      setChats((prev) => prev.filter((item) => item.id !== chatId));
      if (activeChatId === chatId) {
        const remaining = chats.filter((item) => item.id !== chatId);
        if (remaining.length) {
          await selectChat(remaining[0].id);
        } else {
          setActiveChatId(null);
          setMessages([]);
          setSources([]);
        }
      }
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setError(err.message || "Unable to delete this chat.");
    }
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
      await loadTemplates();
      await loadChats();
      await loadDocumentBadges();
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
      handleAuthFailure();
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
    setShowTranslations(false);
    setTranslatedMessages({});
    setTranslationError("");

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
        if (err.name === "AuthError") {
          handleAuthFailure();
          return;
        }
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
        language: data.language || language,
        referral: data.needs_referral ? data.referral_expert : null
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setSources(data.sources || []);
      updateChatTitle(chatId, data.chat_title);
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
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

  const handleTranslateResponses = async () => {
    if (!activeChatId || translatingMessages) return;
    if (showTranslations) {
      setShowTranslations(false);
      return;
    }
    setTranslatingMessages(true);
    setTranslationError("");
    try {
      const data = await requestJson(`/chats/${activeChatId}/translate?target=ur`, {
        method: "POST"
      });
      const map = {};
      (data.messages || []).forEach((item) => {
        if (item.translated_content) {
          map[item.id] = item.translated_content;
        }
      });
      setTranslatedMessages(map);
      setShowTranslations(true);
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setTranslationError(err.message || "Unable to translate responses.");
    } finally {
      setTranslatingMessages(false);
    }
  };

  const handleExample = () => {
    setGeneratorView(false);
    setRiskView(false);
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

  const handleExampleSelect = (prompt) => {
    setGeneratorView(false);
    setRiskView(false);
    setQuery(prompt);
    setError("");
    setSources([]);
    setTimeout(() => {
      const input = document.getElementById("query");
      if (input) {
        input.focus();
      }
    }, 0);
  };

  const handleTemplateChange = (event) => {
    const nextId = event.target.value;
    const nextTemplate = templates.find((template) => template.id === nextId);
    setTemplateId(nextId);
    setTemplateFields(initializeTemplateFields(nextTemplate));
    setTemplateError("");
  };

  const handleTemplateFieldChange = (key, value) => {
    setTemplateFields((prev) => ({ ...prev, [key]: value }));
  };

  const validateTemplateFields = () => {
    if (!selectedTemplate) {
      return "Select a template first.";
    }
    const missing = selectedTemplate.fields
      .filter((field) => field.required)
      .filter((field) => !String(templateFields[field.key] || "").trim())
      .map((field) => field.label);
    if (missing.length) {
      return `Please fill: ${missing.join(", ")}.`;
    }
    return "";
  };

  const handleGenerateDocument = async () => {
    const validationError = validateTemplateFields();
    if (validationError) {
      setTemplateError(validationError);
      return;
    }

    setTemplateError("");
    setGeneratingDocument(true);

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
        if (err.name === "AuthError") {
          handleAuthFailure();
          return;
        }
        setTemplateError(err.message || "Unable to create a chat yet.");
        setGeneratingDocument(false);
        return;
      }
    }

    try {
      const payload = {
        template_id: selectedTemplate.id,
        fields: templateFields,
        language,
        polish_with_llm: polishWithLlm,
        include_pdf: false,
        ...(chatId ? { chat_id: chatId } : {})
      };
      const data = await requestJson("/documents/generate", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      setSources([]);
      updateChatTitle(chatId, data.title);

      const pdfBase64 = data.pdf_base64 || null;
      const docPayload = {
        title: data.title,
        content: data.content,
        filename: data.filename,
        pdfBase64
      };
      setLastGenerated(docPayload);
      setGeneratedDocsByChat((prev) => ({ ...prev, [chatId]: docPayload }));
      setEditedDocsByChat((prev) => ({ ...prev, [chatId]: data.content || "" }));
      setEditedDocument(data.content || "");
      setGeneratorView(true);
      setRiskView(false);
      setShowEditor(true);
      await loadDocumentBadges();
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setTemplateError(err.message || "Unable to generate the document.");
    } finally {
      setGeneratingDocument(false);
    }
  };
  const applyEditorFormat = (prefix, suffix = "") => {
    const textarea = editorRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const before = editedDocument.slice(0, start);
    const selected = editedDocument.slice(start, end) || "";
    const after = editedDocument.slice(end);
    const next = `${before}${prefix}${selected}${suffix}${after}`;
    handleEditedDocumentChange(next);
    requestAnimationFrame(() => {
      const cursor = start + prefix.length + selected.length + suffix.length;
      textarea.focus();
      textarea.setSelectionRange(cursor, cursor);
    });
  };

  const handleEditorHeading = () => applyEditorFormat("\n## ");
  const handleEditorBold = () => applyEditorFormat("**", "**");
  const handleEditorBullet = () => applyEditorFormat("\n- ");

  const handleEditedDocumentChange = (value) => {
    setEditedDocument(value);
    if (activeChatId) {
      setEditedDocsByChat((prev) => ({ ...prev, [activeChatId]: value }));
    }
  };


  const handleDownloadGenerated = async () => {
    const chatId = activeChatId;
    const storedDoc = (chatId && generatedDocsByChat[chatId]) || lastGenerated;
    const currentDraft = (chatId && editedDocsByChat[chatId]) || editedDocument;
    if (!storedDoc?.title || !currentDraft.trim()) {
      setTemplateError("Generate a document first.");
      return;
    }
    setTemplateError("");
    try {
      const data = await requestJson("/documents/render/pdf", {
        method: "POST",
        body: JSON.stringify({
          title: storedDoc.title,
          content: currentDraft
        })
      });
      const nextDoc = {
        ...storedDoc,
        pdfBase64: data.pdf_base64,
        filename: data.filename
      };
      setLastGenerated(nextDoc);
      if (chatId) {
        setGeneratedDocsByChat((prev) => ({ ...prev, [chatId]: nextDoc }));
        setEditedDocsByChat((prev) => ({ ...prev, [chatId]: currentDraft }));
      }
      downloadPdf(data.pdf_base64, data.filename);
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setTemplateError(err.message || "Unable to download the document.");
    }
  };

  const handleComposerKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  const openReviewModal = (mode = "summary") => {
    setReviewMode(mode);
    setReviewOpen(true);
    setReviewError("");
  };

  const closeReviewModal = () => {
    setReviewOpen(false);
    setReviewFile(null);
    setReviewError("");
    setReviewResult(null);
    setReviewing(false);
    setSummarizing(false);
  };

  const handleReviewFileChange = (event) => {
    const file = event.target.files?.[0] || null;
    setReviewResult(null);
    if (!file) {
      setReviewFile(null);
      return;
    }
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith(".pdf") && !lowerName.endsWith(".docx")) {
      setReviewError("Only PDF and DOCX files are supported.");
      setReviewFile(null);
      return;
    }
    setReviewError("");
    setReviewFile(file);
  };

  const handleReviewSubmit = async () => {
    if (!reviewFile || reviewing) return;
    setReviewError("");
    setReviewing(true);

    try {
      const formData = new FormData();
      formData.append("file", reviewFile);
      if (activeChatId) {
        formData.append("chat_id", activeChatId);
      }
      const data = await requestForm("/documents/review", formData);
      setReviewResult(data);
      const userMessage = {
        id: createTempId(),
        role: "user",
        content: `Uploaded document: ${reviewFile.name}`
      };
      const assistantMessage = {
        id: createTempId(),
        role: "assistant",
        content: formatReviewMessage(reviewFile.name, data)
      };
      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      if (activeChatId) {
        updateChatTitle(activeChatId, `Document Review: ${reviewFile.name}`);
      }
      setReviewOpen(false);
      setReviewFile(null);
      setReviewError("");
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setReviewError(err.message || "Unable to review this document yet.");
    } finally {
      setReviewing(false);
    }
  };

  const handleSummarySubmit = async () => {
    if (!reviewFile || summarizing) return;
    setReviewError("");
    setSummarizing(true);

    try {
      const formData = new FormData();
      formData.append("file", reviewFile);
      formData.append("language", language);
      if (activeChatId) {
        formData.append("chat_id", activeChatId);
      }
      const data = await requestForm("/documents/summarize", formData);
      const userMessage = {
        id: createTempId(),
        role: "user",
        content: `Summarize document: ${reviewFile.name}`
      };
      const assistantMessage = {
        id: createTempId(),
        role: "assistant",
        content: formatSummaryMessage(data.summary),
        language: data.language || language
      };
      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      if (activeChatId) {
        updateChatTitle(activeChatId, `Document Summary: ${reviewFile.name}`);
      }
      setReviewOpen(false);
      setReviewFile(null);
      setReviewError("");
    } catch (err) {
      if (err.name === "AuthError") {
        handleAuthFailure();
        return;
      }
      setReviewError(err.message || "Unable to summarize this document yet.");
    } finally {
      setSummarizing(false);
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
            Try Example [{EXAMPLES[exampleIndex].label}]
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setGeneratorView((prev) => !prev);
              setRiskView(false);
            }}
          >
            {generatorView ? "Back to chat" : "Generate Document"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setRiskView((prev) => !prev);
              setGeneratorView(false);
            }}
          >
            {riskView ? "Back to chat" : "Risk Analyzer"}
          </button>
        </div>
        <details className="sidebar__section sidebar__section--chats" open>
          <summary className="sidebar__heading sidebar__heading--accordion">Chats</summary>
          <div className="chat-list__scroll">
            <ul className="chat-list">
              {chats.map((chat) => (
                <li key={chat.id}>
                  <div className="chat-list__row">
                    <button
                      type="button"
                      className={activeChatId === chat.id ? "chat-list__item is-active" : "chat-list__item"}
                      onClick={() => selectChat(chat.id)}
                    >
                      <span className="chat-list__title">{truncateTitle(chat.title)}</span>
                      <span className="chat-list__time">{formatTimestamp(chat.updated_at)}</span>
                    </button>
                    <button
                      type="button"
                      className="chat-delete"
                      onClick={() => handleDeleteChat(chat.id)}
                      aria-label={`Delete ${chat.title}`}
                      title="Delete chat"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path
                          d="M4 7h16M9 7V5h6v2M7 7l1 12h8l1-12M10 11v6M14 11v6"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.6"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </button>
                  </div>
                </li>
              ))}
              {!chats.length && <li className="chat-list__empty">No chats yet.</li>}
            </ul>
          </div>
        </details>
        <div className="sidebar__bottom">
          <div className="user-card">
            <div className="user-card__header">
              <div className="user-card__identity">
                <div className="user-card__avatar">
                  {user.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}
                </div>
                <div className="user-card__info">
                  <p>{user.name}</p>
                  <span>{user.email}</span>
                </div>
              </div>
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
          <span className="topbar__badge">
            {generatorView ? "Document generator" : riskView ? "Risk analyzer" : "Legal assistant"}
          </span>
        </header>

        {generatorView ? (
          <section className="generator-view">
            <div className="generator-card">
              <div className="generator-card__header">
                <div>
                  <h2>Document generator</h2>
                  <p className="muted">Fill the fields below to generate a document draft.</p>
                </div>
                <button type="button" className="btn btn-secondary" onClick={() => setGeneratorView(false)}>
                  Back to chat
                </button>
              </div>
              <div className="generator">
                {!templates.length && <p className="muted">Templates unavailable.</p>}
                {templates.length > 0 && (
                  <>
                    {!showEditor ? (
                      <>
                        <label className="generator__field">
                          <span>Template</span>
                          <select
                            className="generator__select"
                            value={templateId}
                            onChange={handleTemplateChange}
                          >
                            {templates.map((template) => (
                              <option key={template.id} value={template.id}>
                                {template.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <div className="generator__grid">
                          {selectedTemplate?.fields?.map((field) => (
                            <label
                              key={field.key}
                              className={`generator__field ${isFullWidthField(field) ? "generator__field--full" : ""}`}
                            >
                              <span>
                                {field.label}
                                {field.required ? " *" : ""}
                              </span>
                              <input
                                type="text"
                                value={templateFields[field.key] || ""}
                                onChange={(event) => handleTemplateFieldChange(field.key, event.target.value)}
                                placeholder={field.placeholder || ""}
                              />
                            </label>
                          ))}
                        </div>
                        <label className="generator__toggle">
                          <input
                            type="checkbox"
                            checked={polishWithLlm}
                            onChange={(event) => setPolishWithLlm(event.target.checked)}
                          />
                          <span>LLM polish</span>
                        </label>
                        {templateError && <p className="error">{templateError}</p>}
                        <div className="generator__actions generator__actions--form">
                          {activeChatId && generatedDocsByChat[activeChatId] && (
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => {
                                const storedDoc = generatedDocsByChat[activeChatId];
                                const storedEdit = editedDocsByChat[activeChatId] || storedDoc.content || "";
                                setLastGenerated(storedDoc);
                                setEditedDocument(storedEdit);
                                setShowEditor(true);
                              }}
                            >
                              Back to document
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={handleGenerateDocument}
                            disabled={generatingDocument || !selectedTemplate}
                          >
                            {generatingDocument ? "Generating..." : "Generate"}
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="generator__preview">
                        <div className="generator__preview-header">
                          <span>Draft (editable)</span>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => setShowEditor(false)}
                          >
                            Edit form
                          </button>
                        </div>
                        <div className="generator__toolbar">
                          <button type="button" onClick={handleEditorHeading}>Heading</button>
                          <button type="button" onClick={handleEditorBold}>Bold</button>
                          <button type="button" onClick={handleEditorBullet}>Bullet</button>
                        </div>
                        <textarea
                          ref={editorRef}
                          rows="12"
                          value={editedDocument}
                          onChange={(event) => handleEditedDocumentChange(event.target.value)}
                        />
                        <div className="generator__actions">
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={handleDownloadGenerated}
                          >
                            Download PDF
                          </button>
                        </div>
                        <p className="muted">Edits here affect the downloaded PDF only.</p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </section>
        ) : riskView ? (
          <section className="risk-view">
            <div className="risk-card">
              <div className="risk-card__header">
                <div>
                  <h2>Risk analyzer</h2>
                  <p className="muted">
                    Upload a contract to highlight risky clauses, compliance gaps, and key obligations.
                  </p>
                </div>
                <button type="button" className="btn btn-secondary" onClick={() => setRiskView(false)}>
                  Back to chat
                </button>
              </div>
              <div className="risk-card__panel">
                <strong>What you get</strong>
                <ul className="review-bullets">
                  <li>Risk severity tags with explanations.</li>
                  <li>Compliance issues mapped to relevant laws.</li>
                  <li>Plain-language summary for quick review.</li>
                </ul>
              </div>
              <div className="risk-card__actions">
                <button type="button" className="btn btn-primary" onClick={() => openReviewModal("review")}>
                  Upload for review
                </button>
              </div>
            </div>
          </section>
        ) : (
          <section className="chat-window">
            <div className="chat-messages">
              {!messages.length && !error && <div className="empty-state" />}
              {messages.map((message) => {
                const translated = showTranslations && translatedMessages[message.id];
                const displayLanguage = translated ? "ur" : message.language;
                const displayContent = translated || message.content;
                return (
                  <div
                    key={message.id}
                    className={`message-row ${message.role === "user" ? "is-user" : "is-assistant"} ${displayLanguage === "ur" ? "is-urdu" : ""}`}
                  >
                    <div className="message-avatar">
                      {message.role === "user" ? userInitials : "LE"}
                    </div>
                    <div className="message-card">
                      {message.role === "assistant" ? renderMessageContent(displayContent) : <p>{displayContent}</p>}
                      {message.referral && (
                        <div className="referral-card">
                          <div className="referral-card__header">
                            <div className="referral-avatar">
                              {message.referral.photo_url ? (
                                <img src={message.referral.photo_url} alt={message.referral.name} />
                              ) : (
                                <span>{message.referral.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span>
                              )}
                            </div>
                            <div>
                              <strong>{message.referral.name}</strong>
                              <p className="muted">{message.referral.title}</p>
                            </div>
                          </div>
                          <div className="referral-card__details">
                            <span>Domain: {message.referral.domain}</span>
                            <span>Experience: {message.referral.experience}</span>
                            <span>Email: {message.referral.email}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              {loading && (
                <div className="message-row is-assistant">
                  <div className="message-avatar">LE</div>
                  <div className="message-card is-loading">
                    <p>Thinking…</p>
                  </div>
                </div>
              )}
              {error && <p className="error">{error}</p>}
            </div>

            <form className="composer" onSubmit={handleSubmit}>
              <div className="composer__actions">
                <button type="button" className="icon-btn" onClick={() => openReviewModal("summary")} title="Upload documents">
                  Generate a plain-language summary of a legal document
                </button>
                <button type="button" className="icon-btn" disabled title="Voice input">
                  Voice
                </button>
              </div>
              <label className="sr-only" htmlFor="query">Ask a legal question</label>
              <textarea
                id="query"
                rows="1"
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
        )}

        {reviewOpen && (
          <div className="modal-overlay" role="dialog" aria-modal="true">
            <div className="modal">
              <div className="modal__header">
                <div>
                  <h2>{reviewMode === "review" ? "Document review" : "Document summary"}</h2>
                  <p className="muted">
                    {reviewMode === "review"
                      ? "Upload a PDF or DOCX for compliance review or a plain-language summary."
                      : "Upload a PDF or DOCX for a plain-language summary."}
                  </p>
                </div>
                <button type="button" className="modal__close" onClick={closeReviewModal}>Close</button>
              </div>
              <div className="modal__body">
                <label className="file-drop">
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleReviewFileChange}
                  />
                  <div>
                    <strong>{reviewFile ? reviewFile.name : "Drop a file or click to upload "}</strong>
                    <span>PDF or DOCX only. Max 10MB.</span>
                  </div>
                </label>

                {reviewError && <p className="error">{reviewError}</p>}

              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn-secondary" onClick={closeReviewModal}>
                  Close
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleSummarySubmit}
                  disabled={!reviewFile || reviewing || summarizing}
                >
                  {summarizing ? "Summarizing..." : "Summarize document"}
                </button>
                {reviewMode === "review" && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleReviewSubmit}
                    disabled={!reviewFile || reviewing || summarizing}
                  >
                    {reviewing ? "Reviewing..." : "Review document"}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
