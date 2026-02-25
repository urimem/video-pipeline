import { useEffect, useRef } from "react";
import { useSessionStore } from "../../store/sessionStore";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

interface ChatPanelProps {
  onSendMessage: (text: string) => void;
}

export function ChatPanel({ onSendMessage }: ChatPanelProps) {
  const { messages, isAgentTyping, isConnected } = useSessionStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="connection-dot" data-connected={isConnected} />
        <span>{isConnected ? "Agent connected" : "Connecting…"}</span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Hi! I'm your AI video producer.</p>
            <p>Tell me what kind of video you'd like to create.</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isAgentTyping && messages[messages.length - 1]?.role !== "agent" && (
          <div className="typing-indicator">
            <span />
            <span />
            <span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={onSendMessage} disabled={isAgentTyping || !isConnected} />
    </div>
  );
}
