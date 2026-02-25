# Video Pipeline — Technical Notes

## Architecture

Two-tier web application:
- **Backend**: Python 3.11+ / FastAPI / WebSockets / Anthropic SDK
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

Copy `.env.example` → `.env` and fill in `ANTHROPIC_API_KEY`.

## Backend Structure

```
backend/
  main.py              # FastAPI app + CORS; loads .env
  api/routes.py        # POST /session, DELETE /session/{id}, GET /health
  api/websocket.py     # WS /ws/{session_id} — dispatches to agent
  agent/agent.py       # Claude streaming + agentic tool loop (core logic)
  agent/tools.py       # Tool JSON schemas for Claude
  agent/system_prompt.py # 3-step pipeline instructions injected each turn
  agent/tool_handlers.py # Tool dispatch → clients + artifact WS updates
  session/state.py     # SessionState Pydantic model + in-memory sessions dict
  clients/nano_banana.py # Image gen stub (submit + poll pattern)
  clients/kling_ai.py    # Video gen stub (submit + poll pattern)
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

Claude claude-sonnet-4-6 with tool use. 4 tools:
- `update_script` — saves script artifact
- `generate_image` — calls Nano Banana, emits pending+ready WS events
- `generate_video` — calls Kling AI (async), emits pending+ready WS events
- `update_pipeline_step` — advances pipeline state, emits WS event

The agentic loop in `agent/agent.py` handles streaming text tokens (forwarded to WS as `agent_token`), then tool calls iteratively until `stop_reason == "end_turn"`.

Dynamic system prompt injection on every API call: includes current `pipeline_step` and artifact state to prevent Claude from skipping steps.

## WebSocket Protocol

All frames: `{ "type": "<type>", "data": { ... } }`

Server→Client: `session_init`, `agent_token`, `agent_turn_complete`, `tool_use`, `artifact_update`, `pipeline_step_update`, `error`, `pong`
Client→Server: `user_message`, `ping`

## Replacing Stub API Clients

Both `clients/nano_banana.py` and `clients/kling_ai.py` use `_submit_job()` + `_poll_result()` pattern. Replace those two methods with real `httpx` calls when API keys are available. The `generate()` interface stays the same.

## Known Limitations

- In-memory session store — lost on server restart (easy to replace with Redis)
- Full conversation history re-sent to Claude each turn — may hit context limits for very long sessions
- Images generated sequentially (one tool call per image)
- Pipeline step ordering enforced via system prompt, not backend validation
