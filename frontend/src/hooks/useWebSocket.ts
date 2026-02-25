import { useEffect, useRef, useCallback } from "react";
import { useSessionStore } from "../store/sessionStore";
import type { ServerMessage } from "../types";

const WS_BASE = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);

  const dispatch = useCallback((msg: ServerMessage) => {
    const store = useSessionStore.getState();
    switch (msg.type) {
      case "session_init":
        store.initFromSession(msg.data);
        break;

      case "agent_token":
        store.appendAgentToken(msg.data.token);
        break;

      case "agent_turn_complete":
        store.finaliseAgentMessage();
        break;

      case "tool_use":
        // Could show a subtle indicator — currently a no-op
        break;

      case "artifact_update": {
        const d = msg.data;
        if (d.artifact_type === "script") {
          store.setScript(d.script as string);
        } else if (d.artifact_type === "image_pending") {
          store.addOrUpdateImage(d.index as number, {
            type: d.image_type as "character" | "opening" | "closing",
            prompt: d.prompt as string,
            url: null,
            task_id: null,
          });
        } else if (d.artifact_type === "image_ready") {
          store.addOrUpdateImage(d.index as number, { url: d.url as string });
        } else if (d.artifact_type === "video_ready") {
          store.setVideoUrl(d.video_url as string);
        }
        break;
      }

      case "pipeline_step_update":
        store.setPipelineStep(msg.data.step);
        break;

      case "error":
        console.error("[Agent error]", msg.data.message);
        break;

      case "pong":
        break;
    }
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(`${WS_BASE}/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => useSessionStore.getState().setConnected(true);
    ws.onclose = () => useSessionStore.getState().setConnected(false);
    ws.onerror = (e) => console.error("[WebSocket error]", e);
    ws.onmessage = (e: MessageEvent) => {
      try {
        const msg = JSON.parse(e.data as string) as ServerMessage;
        dispatch(msg);
      } catch (err) {
        console.error("[Failed to parse WS message]", err);
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping", data: {} }));
      }
    }, 20_000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [sessionId, dispatch]);

  const sendMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    useSessionStore.getState().addUserMessage(text);
    wsRef.current.send(
      JSON.stringify({ type: "user_message", data: { text } })
    );
  }, []);

  return { sendMessage };
}
