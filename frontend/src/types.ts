// ── Pipeline ─────────────────────────────────────────────────────────────────
export type PipelineStep = "script" | "images" | "video" | "complete";

// ── Domain types ─────────────────────────────────────────────────────────────
export interface ImageArtifact {
  type: "character" | "opening" | "closing";
  prompt: string;
  url: string | null;
  task_id: string | null;
}

// ── Chat (UI only) ───────────────────────────────────────────────────────────
export type ChatRole = "user" | "agent";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  isStreaming: boolean;
  timestamp: number;
}

// ── WebSocket message protocol ────────────────────────────────────────────────
// Server → Client message types
export type SessionInitMessage = {
  type: "session_init";
  data: {
    session_id: string;
    pipeline_step: PipelineStep;
    script: string | null;
    images: ImageArtifact[];
    video_url: string | null;
  };
};

export type AgentTokenMessage = {
  type: "agent_token";
  data: { token: string };
};

export type AgentTurnCompleteMessage = {
  type: "agent_turn_complete";
  data: Record<string, never>;
};

export type ToolUseMessage = {
  type: "tool_use";
  data: { tool_name: string; tool_input: Record<string, unknown> };
};

export type ArtifactUpdateMessage = {
  type: "artifact_update";
  data: {
    artifact_type:
      | "script"
      | "image_pending"
      | "image_ready"
      | "video_pending"
      | "video_ready";
    [key: string]: unknown;
  };
};

export type PipelineStepUpdateMessage = {
  type: "pipeline_step_update";
  data: { step: PipelineStep };
};

export type ErrorMessage = {
  type: "error";
  data: { message: string; recoverable: boolean };
};

export type PongMessage = { type: "pong"; data: Record<string, never> };

export type ServerMessage =
  | SessionInitMessage
  | AgentTokenMessage
  | AgentTurnCompleteMessage
  | ToolUseMessage
  | ArtifactUpdateMessage
  | PipelineStepUpdateMessage
  | ErrorMessage
  | PongMessage;

// Client → Server
export type ClientMessage =
  | { type: "user_message"; data: { text: string } }
  | { type: "ping"; data: Record<string, never> };
