from fastapi import APIRouter
from session.state import get_or_create_session, sessions

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/session")
async def create_session():
    """Create a new session and return its ID."""
    state = get_or_create_session()
    return {"session_id": state.session_id}


@router.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Delete a session, clearing all pipeline state."""
    sessions.pop(session_id, None)
    return {"status": "reset"}
