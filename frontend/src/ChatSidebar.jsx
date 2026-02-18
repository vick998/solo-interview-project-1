import { Plus, Pencil } from "lucide-react";

export function ChatSidebar({
  chats,
  currentChat,
  editingChatId,
  editingTitle,
  onNewChat,
  onSelectChat,
  onStartEdit,
  onTitleChange,
  onSaveTitle,
  onCancelEdit,
  onTitleKeyDown,
}) {
  return (
    <aside className="sidebar-left">
      <button type="button" className="btn-new-chat" onClick={onNewChat}>
        <Plus size={18} />
        New chat
      </button>
      <div className="sidebar-chat-list">
        {chats.map((c) => (
          <div
            key={c.id}
            className={`sidebar-item ${currentChat?.id === c.id ? "active" : ""}`}
            onClick={() => !editingChatId && onSelectChat(c.id)}
          >
            {editingChatId === c.id ? (
              <input
                type="text"
                className="sidebar-item-input"
                value={editingTitle}
                onChange={(e) => onTitleChange(e.target.value)}
                onKeyDown={onTitleKeyDown}
                onBlur={onSaveTitle}
                onClick={(e) => e.stopPropagation()}
                autoFocus
              />
            ) : (
              <>
                <span className="sidebar-item-title">{c.title || "New chat"}</span>
                <button
                  type="button"
                  className="sidebar-item-edit"
                  onClick={(e) => onStartEdit(e, c)}
                  aria-label="Rename chat"
                >
                  <Pencil size={14} />
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}
