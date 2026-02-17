import { useState, useEffect, useCallback } from "react";

const API_BASE = "";

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || JSON.stringify(err));
  }
  return res.json();
}

function App() {
  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [urlInput, setUrlInput] = useState("");

  const loadChats = useCallback(async () => {
    const list = await api("/chats");
    setChats(list);
  }, []);

  const loadModels = useCallback(async () => {
    const list = await api("/qa/models");
    setModels(list);
    if (list.length && !selectedModel) setSelectedModel(list[0].id);
  }, [selectedModel]);

  useEffect(() => {
    loadChats();
    loadModels();
  }, [loadChats, loadModels]);

  const createChat = async () => {
    const { id } = await api("/chats", { method: "POST", body: JSON.stringify({}) });
    await loadChats();
    setCurrentChat({ id, documents: [], messages: [] });
  };

  const loadChat = async (id) => {
    const chat = await api(`/chats/${id}`);
    setCurrentChat(chat);
  };

  const uploadFiles = async (e) => {
    if (!currentChat?.id) return;
    const files = e.target.files;
    if (!files?.length) return;
    const form = new FormData();
    for (const f of files) form.append("files", f);
    const res = await fetch(`/chats/${currentChat.id}/upload`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    const data = await res.json();
    await loadChat(currentChat.id);
  };

  const addUrl = async () => {
    if (!currentChat?.id || !urlInput.trim()) return;
    await api(`/chats/${currentChat.id}/add-urls`, {
      method: "POST",
      body: JSON.stringify({ urls: [urlInput.trim()] }),
    });
    setUrlInput("");
    await loadChat(currentChat.id);
  };

  const ask = async () => {
    if (!currentChat?.id || !question.trim()) return;
    const enabledIds = currentChat.documents?.filter((d) => d.enabled).map((d) => d.id) ?? [];
    if (!enabledIds.length) {
      alert("Upload at least one document and ensure it is enabled.");
      return;
    }
    setLoading(true);
    try {
      const res = await api(`/chats/${currentChat.id}/ask`, {
        method: "POST",
        body: JSON.stringify({
          question: question.trim(),
          document_ids: enabledIds,
          model_id: selectedModel || undefined,
        }),
      });
      setQuestion("");
      await loadChat(currentChat.id);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = async (docId, enabled) => {
    if (!currentChat?.id) return;
    await api(`/chats/${currentChat.id}/documents/${docId}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    });
    await loadChat(currentChat.id);
  };

  return (
    <div style={{ display: "flex", width: "100%", minHeight: "100vh" }}>
      <aside style={{ width: 220, padding: 16, borderRight: "1px solid #333", background: "#16213e" }}>
        <button onClick={createChat} style={{ width: "100%", padding: 10, marginBottom: 16, cursor: "pointer" }}>
          New chat
        </button>
        {chats.map((c) => (
          <div
            key={c.id}
            onClick={() => loadChat(c.id)}
            style={{
              padding: 10,
              marginBottom: 4,
              cursor: "pointer",
              background: currentChat?.id === c.id ? "#0f3460" : "transparent",
              borderRadius: 6,
            }}
          >
            {c.title || "New chat"}
          </div>
        ))}
      </aside>

      <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: 16 }}>
        {!currentChat ? (
          <p>Create or select a chat.</p>
        ) : (
          <>
            <div style={{ flex: 1, overflowY: "auto", marginBottom: 16 }}>
              {(currentChat.messages || []).map((m) => (
                <div key={m.id} style={{ marginBottom: 16 }}>
                  <div style={{ color: "#aaa", fontSize: 12 }}>Q: {m.question}</div>
                  <div>A: {m.answer}</div>
                  {m.model_used && <div style={{ color: "#666", fontSize: 11 }}>Model: {m.model_used}</div>}
                </div>
              ))}
            </div>
            <div>
              <input
                type="text"
                placeholder="Ask a question..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && ask()}
                style={{ width: "100%", padding: 12, marginBottom: 8 }}
              />
              <div style={{ display: "flex", gap: 8 }}>
                <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={uploadFiles} />
                <input
                  type="text"
                  placeholder="Add URL..."
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addUrl()}
                  style={{ flex: 1, padding: 8 }}
                />
                <button onClick={addUrl}>Add URL</button>
                <button onClick={ask} disabled={loading}>
                  {loading ? "..." : "Ask"}
                </button>
              </div>
            </div>
          </>
        )}
      </main>

      <aside style={{ width: 260, padding: 16, borderLeft: "1px solid #333", background: "#16213e" }}>
        <h3 style={{ marginTop: 0 }}>Containing</h3>
        <div style={{ marginBottom: 16 }}>
          <label>Model</label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label>Documents</label>
          {(currentChat?.documents || []).map((d) => (
            <div key={d.id} style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
              <input
                type="checkbox"
                checked={!!d.enabled}
                onChange={(e) => toggleDoc(d.id, e.target.checked)}
              />
              <span style={{ fontSize: 12, overflow: "hidden", textOverflow: "ellipsis" }} title={d.display_name}>
                {d.display_name}
              </span>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

export default App;
