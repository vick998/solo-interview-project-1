import { Paperclip, SendHorizontal } from "lucide-react";

export function InputArea({
  question,
  onQuestionChange,
  onAsk,
  onOpenUpload,
  loading,
}) {
  return (
    <div className="input-area">
      <button
        type="button"
        className="btn-round"
        onClick={onOpenUpload}
        aria-label="Upload documents"
      >
        <Paperclip size={20} />
      </button>
      <textarea
        placeholder="Ask a question..."
        value={question}
        onChange={(e) => onQuestionChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onAsk();
          }
        }}
        rows={1}
      />
      <button
        type="button"
        className="btn-round"
        onClick={onAsk}
        disabled={loading}
        aria-label="Send"
      >
        <SendHorizontal size={20} />
      </button>
    </div>
  );
}
