import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "./api.js";
import { ChatSidebar } from "./ChatSidebar.jsx";
import { ChatHeader } from "./ChatHeader.jsx";
import { MessageList } from "./MessageList.jsx";
import { InputArea } from "./InputArea.jsx";
import { DocumentSidebar } from "./DocumentSidebar.jsx";
import { Toast } from "./Toast.jsx";
import { UploadModal } from "./UploadModal.jsx";

function App() {
  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [expandedDocId, setExpandedDocId] = useState(null);
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [toast, setToast] = useState(null);
  const editStartTimeRef = useRef(0);
  const savingTitleRef = useRef(false);

  const showToast = useCallback((msg, type = "error") => {
    setToast({ message: msg, type });
  }, []);

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
    try {
      const { id } = await api("/chats", { method: "POST", body: JSON.stringify({}) });
      await loadChats();
      setCurrentChat({ id, documents: [], messages: [] });
    } catch (err) {
      showToast(err.message);
    }
  };

  const loadChat = useCallback(async (id) => {
    const chat = await api(`/chats/${id}`);
    setCurrentChat(chat);
  }, []);

  const ask = async () => {
    if (!currentChat?.id || !question.trim()) return;
    const enabledIds = currentChat.documents?.filter((d) => d.enabled).map((d) => d.id) ?? [];
    if (!enabledIds.length) {
      showToast("Upload at least one document and ensure it is enabled.");
      return;
    }
    const trimmedQuestion = question.trim();
    setLoadingMessage({ question: trimmedQuestion });
    setQuestion("");
    setLoading(true);
    try {
      await api(`/chats/${currentChat.id}/ask`, {
        method: "POST",
        body: JSON.stringify({
          question: trimmedQuestion,
          document_ids: enabledIds,
          model_id: selectedModel || undefined,
        }),
      });
      await loadChat(currentChat.id);
      setLoadingMessage(null);
    } catch (err) {
      showToast(err.message);
      setQuestion(trimmedQuestion);
      setLoadingMessage(null);
    } finally {
      setLoading(false);
    }
  };

  const selectDoc = async (docId) => {
    if (!currentChat?.id) return;
    const doc = currentChat.documents?.find((d) => d.id === docId);
    if (!doc) return;
    const newEnabled = !doc.enabled;
    try {
      await api(`/chats/${currentChat.id}/documents/${docId}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled: newEnabled }),
      });
      await loadChat(currentChat.id);
    } catch (err) {
      showToast(err.message);
    }
  };

  const toggleDocExpand = (docId) => {
    setExpandedDocId((prev) => (prev === docId ? null : docId));
  };

  const handleUploadSuccess = useCallback(() => {
    if (currentChat?.id) loadChat(currentChat.id);
  }, [currentChat?.id, loadChat]);

  const startEditingChat = (e, chat) => {
    e.stopPropagation();
    editStartTimeRef.current = Date.now();
    setEditingChatId(chat.id);
    setEditingTitle(chat.title || "New chat");
  };

  const saveChatTitle = async () => {
    if (!editingChatId) return;
    if (Date.now() - editStartTimeRef.current < 200) return;
    if (savingTitleRef.current) return;
    savingTitleRef.current = true;
    const trimmed = editingTitle.trim() || "New chat";
    try {
      await api(`/chats/${editingChatId}`, {
        method: "PATCH",
        body: JSON.stringify({ title: trimmed }),
      });
      await loadChats();
      if (currentChat?.id === editingChatId) {
        setCurrentChat((prev) => (prev ? { ...prev, title: trimmed } : null));
      }
    } catch (err) {
      showToast(err.message);
    } finally {
      savingTitleRef.current = false;
      setEditingChatId(null);
      setEditingTitle("");
    }
  };

  const cancelEditingChat = () => {
    setEditingChatId(null);
    setEditingTitle("");
  };

  const handleTitleKeyDown = (e) => {
    if (e.key === "Enter") saveChatTitle();
    if (e.key === "Escape") cancelEditingChat();
  };

  return (
    <div className="app-layout">
      <ChatSidebar
        chats={chats}
        currentChat={currentChat}
        editingChatId={editingChatId}
        editingTitle={editingTitle}
        onNewChat={createChat}
        onSelectChat={loadChat}
        onStartEdit={startEditingChat}
        onTitleChange={setEditingTitle}
        onSaveTitle={saveChatTitle}
        onCancelEdit={cancelEditingChat}
        onTitleKeyDown={handleTitleKeyDown}
      />

      <main className="main-content">
        {!currentChat ? (
          <p>Create or select a chat.</p>
        ) : (
          <>
            <ChatHeader
              chat={currentChat}
              editingChatId={editingChatId}
              editingTitle={editingTitle}
              onTitleChange={setEditingTitle}
              onSaveTitle={saveChatTitle}
              onStartEdit={startEditingChat}
              onCancelEdit={cancelEditingChat}
              onTitleKeyDown={handleTitleKeyDown}
            />
            <MessageList
              messages={currentChat.messages}
              loadingMessage={loadingMessage}
            />
            <InputArea
              question={question}
              onQuestionChange={setQuestion}
              onAsk={ask}
              onOpenUpload={() => setUploadModalOpen(true)}
              loading={loading}
            />
          </>
        )}
      </main>

      <DocumentSidebar
        models={models}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        documents={currentChat?.documents}
        expandedDocId={expandedDocId}
        onSelectDoc={selectDoc}
        onToggleExpand={toggleDocExpand}
      />

      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        chatId={currentChat?.id}
        onUploadSuccess={handleUploadSuccess}
      />

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDismiss={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default App;
