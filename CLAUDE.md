# Video Pipeline — Technical Notes

## Architecture

Two-tier web application:
- **Backend**: Python 3.13 / FastAPI / WebSockets / OpenAI SDK
- **Frontend**: React 18 / Vite / TypeScript / Zustand

## Running the App

```bash
# Backend (from project root)
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev   # http://localhost:5173
```

Copy `.env.example` → `.env` (project root) and fill in both keys:
- `KIE_API_KEY` — kie.ai key for image and video generation
- `OPENAI_API_KEY` — OpenAI key for the chat agent (gpt-5.1-chat-latest)

## Backend Structure

```
backend/
  main.py              # FastAPI app + CORS; loads .env
  api/routes.py        # POST /session, DELETE /session/{id}, GET /health
  api/websocket.py     # WS /ws/{session_id} — dispatches to agent
  agent/agent.py       # Gemini 2.5 Flash streaming + agentic tool loop (core logic)
  agent/tools.py       # Tool JSON schemas (OpenAI function-calling format)
  agent/system_prompt.py # 3-step pipeline instructions injected each turn
  agent/tool_handlers.py # Tool dispatch → kie.ai client + artifact WS updates
  session/state.py     # SessionState Pydantic model + in-memory sessions dict
  clients/kie_ai.py    # Unified kie.ai client (image gen + video gen)
```

## Frontend Structure

```
frontend/src/
  types.ts             # All WS message types + domain types
  store/sessionStore.ts # Zustand store (single source of truth)
  hooks/useWebSocket.ts # WS connection + message dispatcher
  components/layout/   # TwoPanel, PipelineBar
  components/chat/     # ChatPanel, ChatMessage, ChatInput
  components/artifacts/ # ArtifactPanel, ScriptArtifact, ImagesArtifact, VideoArtifact
```

## Agent Design

`gpt-5.1-chat-latest` via OpenAI API (`https://api.openai.com/v1`) with function calling. 4 tools:
- `update_script` — saves script artifact
- `generate_image` — calls google/nano-banana via kie.ai, emits pending+ready WS events
- `generate_video` — calls kling-3.0/video (image-to-video) via kie.ai, emits pending+ready WS events
- `update_pipeline_step` — advances pipeline state, emits WS event

The agentic loop in `agent/agent.py` handles streaming text tokens (forwarded to WS as `agent_token`), accumulates tool call fragments across chunks, then executes tools iteratively until `finish_reason != "tool_calls"`.

Dynamic system prompt injection on every API call via `system` role message: includes current `pipeline_step` and artifact state to prevent the model from skipping steps.

## kie.ai API Integration

`KIE_API_KEY` is used only for image and video generation (chat uses OpenAI directly). The unified client in `clients/kie_ai.py` handles:
- **Image gen (google/nano-banana)**: `POST /api/v1/jobs/createTask` → poll `GET /api/v1/jobs/recordInfo`
- **Video gen (kling-3.0/video)**: Same createTask/recordInfo pattern, but image-to-video (requires `image_url` input)

## WebSocket Protocol

All frames: `{ "type": "<type>", "data": { ... } }`

Server→Client: `session_init`, `agent_token`, `agent_turn_complete`, `tool_use`, `artifact_update`, `pipeline_step_update`, `error`, `pong`
Client→Server: `user_message`, `ping`

## Known Limitations

- In-memory session store — lost on server restart (easy to replace with Redis)
- Full conversation history re-sent to Gemini each turn — may hit context limits for very long sessions
- Images generated sequentially (one tool call per image)
- Pipeline step ordering enforced via system prompt, not backend validation
