import { useMemo, useState } from "react";

const DEFAULT_QUERY = "Summarize the key obligations under section 1 of the Companies Act, 2017.";

export default function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [topK, setTopK] = useState(3);
  const [maxTokens, setMaxTokens] = useState(128);

  const canSubmit = useMemo(() => query.trim().length >= 3 && !loading, [query, loading]);

  const runQuery = async (text) => {
    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch("/rag/answer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query: text,
          top_k: Number(topK),
          max_new_tokens: Number(maxTokens)
        })
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Request failed");
      }

      const data = await response.json();
      setAnswer(data.answer || "");
      setSources(data.sources || []);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!canSubmit) return;
    runQuery(query.trim());
  };

  const handleExample = () => {
    setQuery(DEFAULT_QUERY);
    runQuery(DEFAULT_QUERY);
  };

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>LegalEase</h1>
          <p>Pakistan-specific legal assistant (Urdu + English) powered by Qwen + RAG.</p>
        </div>
        <div className="app__badge">RAG ready</div>
      </header>

      <main className="app__main">
        <form className="card" onSubmit={handleSubmit}>
          <label htmlFor="query">Ask a legal question</label>
          <textarea
            id="query"
            rows="4"
            placeholder="Type your query here..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />

          <div className="controls">
            <div className="control">
              <label>Top K</label>
              <input
                type="number"
                min="1"
                max="20"
                value={topK}
                onChange={(event) => setTopK(event.target.value)}
              />
            </div>
            <div className="control">
              <label>Max Tokens</label>
              <input
                type="number"
                min="32"
                max="1024"
                value={maxTokens}
                onChange={(event) => setMaxTokens(event.target.value)}
              />
            </div>
            <div className="actions">
              <button type="button" className="btn btn-secondary" onClick={handleExample} disabled={loading}>
                Try example
              </button>
              <button type="submit" className="btn" disabled={!canSubmit}>
                {loading ? "Thinking…" : "Ask LegalEase"}
              </button>
            </div>
          </div>
        </form>

        <section className="card">
          <h2>Answer</h2>
          {error && <p className="error">{error}</p>}
          {!error && !answer && <p className="muted">Submit a query to see the answer.</p>}
          {answer && <p className="answer">{answer}</p>}
        </section>

        <section className="card">
          <h2>Sources</h2>
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
        </section>
      </main>
    </div>
  );
}
