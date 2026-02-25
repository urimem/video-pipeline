import { create } from "zustand";
import type { PipelineStep, ChatMessage, ImageArtifact } from "../types";

interface SessionStore {
  // Connection state
  sessionId: string | null;
  isConnected: boolean;

  // Pipeline
  pipelineStep: PipelineStep;

  // Chat
  messages: ChatMessage[];
  isAgentTyping: boolean;

  // Artifacts
  script: string | null;
  images: ImageArtifact[];
  videoUrl: string | null;

  // Actions
  setConnected: (v: boolean) => void;
  setSessionId: (id: string) => void;
  initFromSession: (data: {
    session_id: string;
    pipeline_step: PipelineStep;
    script: string | null;
    images: ImageArtifact[];
    video_url: string | null;
  }) => void;
  addUserMessage: (text: string) => void;
  appendAgentToken: (token: string) => void;
  finaliseAgentMessage: () => void;
  setScript: (script: string) => void;
  addOrUpdateImage: (index: number, patch: Partial<ImageArtifact>) => void;
  setVideoUrl: (url: string) => void;
  setPipelineStep: (step: PipelineStep) => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessionId: null,
  isConnected: false,
  pipelineStep: "script",
  messages: [],
  isAgentTyping: false,
  script: null,
  images: [],
  videoUrl: null,

  setConnected: (v) => set({ isConnected: v }),
  setSessionId: (id) => set({ sessionId: id }),

  initFromSession: (data) =>
    set({
      sessionId: data.session_id,
      pipelineStep: data.pipeline_step,
      script: data.script,
      images: data.images,
      videoUrl: data.video_url,
    }),

  addUserMessage: (text) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          id: crypto.randomUUID(),
          role: "user" as const,
          content: text,
          isStreaming: false,
          timestamp: Date.now(),
        },
      ],
    })),

  appendAgentToken: (token) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "agent" && last.isStreaming) {
        msgs[msgs.length - 1] = { ...last, content: last.content + token };
      } else {
        msgs.push({
          id: crypto.randomUUID(),
          role: "agent" as const,
          content: token,
          isStreaming: true,
          timestamp: Date.now(),
        });
      }
      return { messages: msgs, isAgentTyping: true };
    }),

  finaliseAgentMessage: () =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.isStreaming ? { ...m, isStreaming: false } : m
      ),
      isAgentTyping: false,
    })),

  setScript: (script) => set({ script }),

  addOrUpdateImage: (index, patch) =>
    set((s) => {
      const images = [...s.images];
      images[index] = { ...(images[index] ?? {}), ...patch } as ImageArtifact;
      return { images };
    }),

  setVideoUrl: (url) => set({ videoUrl: url }),
  setPipelineStep: (step) => set({ pipelineStep: step }),
}));
