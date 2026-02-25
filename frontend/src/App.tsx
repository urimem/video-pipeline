import { useEffect, useRef } from "react";
import { PipelineBar } from "./components/layout/PipelineBar";
import { TwoPanel } from "./components/layout/TwoPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import { useSessionStore } from "./store/sessionStore";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export default function App() {
  const { sessionId, setSessionId, pipelineStep } = useSessionStore();
  const hasFetched = useRef(false);

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    const existing = localStorage.getItem("session_id");
    if (existing) {
      setSessionId(existing);
    } else {
      fetch(`${BACKEND_URL}/session`, { method: "POST" })
        .then((r) => r.json())
        .then(({ session_id }: { session_id: string }) => {
          localStorage.setItem("session_id", session_id);
          setSessionId(session_id);
        })
        .catch(console.error);
    }
  }, [setSessionId]);

  const { sendMessage } = useWebSocket(sessionId);

  return (
    <div className="app-root">
      <header className="app-header">
        <span className="app-logo">🎬</span>
        <span className="app-title">Video Pipeline</span>
        <PipelineBar currentStep={pipelineStep} />
      </header>
      <main className="app-main">
        <TwoPanel onSendMessage={sendMessage} />
      </main>
    </div>
  );
}
