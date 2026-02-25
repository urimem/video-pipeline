import type { ChatMessage as ChatMessageType } from "../../types";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isAgent = message.role === "agent";

  return (
    <div className={`chat-message ${isAgent ? "agent" : "user"}`}>
      <div className="message-avatar">{isAgent ? "🤖" : "👤"}</div>
      <div className="message-bubble">
        <span className="message-text">{message.content}</span>
        {message.isStreaming && <span className="streaming-cursor" />}
      </div>
    </div>
  );
}
