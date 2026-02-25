from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from session.state import get_or_create_session
from agent.agent import run_agent_turn

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    state = get_or_create_session(session_id)

    async def ws_send(msg: dict) -> None:
        await websocket.send_json(msg)

    # Send current session state immediately on connect
    await ws_send({
        "type": "session_init",
        "data": {
            "session_id": state.session_id,
            "pipeline_step": state.pipeline_step,
            "script": state.script,
            "images": [img.model_dump() for img in state.images],
            "video_url": state.video_url,
        },
    })

    try:
        while True:
            raw = await websocket.receive_json()
            msg_type = raw.get("type")

            if msg_type == "user_message":
                user_text = raw["data"]["text"]
                try:
                    await run_agent_turn(user_text, state, ws_send)
                except Exception as e:
                    await ws_send({
                        "type": "error",
                        "data": {"message": str(e), "recoverable": True},
                    })

            elif msg_type == "ping":
                await ws_send({"type": "pong", "data": {}})

    except WebSocketDisconnect:
        # Session state persists in memory for reconnection
        pass
