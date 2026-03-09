  # Video Pipeline

  A two-tier web application for video content creation using AI tools with real-time collaboration capabilities.

  ## Architecture

  The application consists of:
  - **Backend**: Python 3.11+ / FastAPI / WebSockets / OpenAI SDK (pointed at kie.ai)
  - **Frontend**: React 18 / Vite / TypeScript / Zustand

  ## Features

  - Real-time collaborative video creation
  - AI-powered script generation, image generation, and video synthesis
  - WebSocket-based communication for real-time updates
  - Pipeline step management with artifact tracking
  - Responsive web interface with real-time feedback

  ## Running the App

  ### Prerequisites

  1. Python 3.11+
  2. Node.js 18+
  3. A kie.ai API key (single key for all kie.ai services)

  ### Backend Setup

  ```bash
  cd backend
  source .venv/bin/activate
  pip install -r requirements.txt

  Copy .env.example → .env and fill in KIE_API_KEY:

  cp .env.example .env
  # Edit .env to add your KIE_API_KEY

  Start the backend server:

  uvicorn main:app --reload --port 8000
  ```
  ### Frontend Setup
  ```bash
  cd frontend
  npm install
  npm run dev   # http://localhost:5173
  ```

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

  The agent uses Gemini 2.5 Flash via kie.ai (OpenAI-compatible API) with function calling and four tools:

  1. update_script — saves script artifact
  2. generate_image — calls google/nano-banana via kie.ai, emits pending+ready WS events
  3. generate_video — calls kling-3.0/video (image-to-video) via kie.ai, emits pending+ready WS events
  4. update_pipeline_step — advances pipeline state, emits WS event

  The agentic loop in agent/agent.py handles streaming text tokens (forwarded to WS as agent_token), accumulates tool call fragments across chunks, then executes tools
  iteratively until finish_reason != "tool_calls".

  Dynamic system prompt injection on every API call via developer role message: includes current pipeline_step and artifact state to prevent the model from skipping
  steps.

  ### kie.ai API Integration

  All services use a single KIE_API_KEY. The unified client in clients/kie_ai.py handles:

  - Chat (Gemini 2.5 Flash): POST /gemini-2.5-flash/v1/chat/completions — OpenAI-compatible, used via the OpenAI Python SDK with custom base_url
  - Image gen (google/nano-banana): POST /api/v1/jobs/createTask → poll GET /api/v1/jobs/recordInfo
  - Video gen (kling-3.0/video): Same createTask/recordInfo pattern, but image-to-video (requires image_url input)

  ### WebSocket Protocol

  All frames: { "type": "<type>", "data": { ... } }

  Server→Client:
  - session_init
  - agent_token
  - agent_turn_complete
  - tool_use
  - artifact_update
  - pipeline_step_update
  - error
  - pong

  Client→Server:
  - user_message
  - ping

  ## Known Limitations

  - In-memory session store — lost on server restart (easy to replace with Redis)
  - Full conversation history re-sent to Gemini each turn — may hit context limits for very long sessions
  - Images generated sequentially (one tool call per image)
  - Pipeline step ordering enforced via system prompt, not backend validation

  ## License

  This project is licensed under the MIT License.
