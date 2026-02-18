import { Pencil } from "lucide-react";

export function ChatHeader({
  chat,
  editingChatId,
  editingTitle,
  onTitleChange,
  onSaveTitle,
  onStartEdit,
  onCancelEdit,
  onTitleKeyDown,
}) {
  if (!chat) return null;

  return (
    <header className="chat-header">
      {editingChatId === chat.id ? (
        <input
          type="text"
          className="chat-header-input"
          value={editingTitle}
          onChange={(e) => onTitleChange(e.target.value)}
          onKeyDown={onTitleKeyDown}
          onBlur={onSaveTitle}
          autoFocus
        />
      ) : (
        <>
          <h2 className="chat-header-title">{chat.title || "New chat"}</h2>
          <button
            type="button"
            className="chat-header-edit"
            onClick={(e) => onStartEdit(e, chat)}
            aria-label="Rename chat"
          >
            <Pencil size={16} />
          </button>
        </>
      )}
    </header>
  );
}
