export function MessageList({ messages = [], loadingMessage }) {
  return (
    <div className="messages-area">
      {messages.map((m) => (
        <div key={m.id} className="message-item">
          <div className="chat-bubble chat-bubble--question">{m.question}</div>
          <div className="chat-bubble chat-bubble--answer">
            {m.answer}
            {m.inference_time != null && (
              <span className="chat-bubble-inference">
                {m.inference_time.toFixed(2)}s
              </span>
            )}
          </div>
          {m.model_used && (
            <div className="chat-bubble-model">Model: {m.model_used}</div>
          )}
        </div>
      ))}
      {loadingMessage && (
        <div className="message-item">
          <div className="chat-bubble chat-bubble--question">
            {loadingMessage.question}
          </div>
          <div className="chat-bubble chat-bubble--answer chat-bubble--loading">
            <div className="chat-bubble-dots">
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
