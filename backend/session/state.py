from typing import Optional, List, Literal
from pydantic import BaseModel, Field
import uuid

PipelineStep = Literal["script", "images", "video", "complete"]


class ImageArtifact(BaseModel):
    type: Literal["character", "opening", "closing"]
    prompt: str
    url: Optional[str] = None
    task_id: Optional[str] = None


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_step: PipelineStep = "script"
    script: Optional[str] = None
    images: List[ImageArtifact] = []
    video_url: Optional[str] = None
    video_task_id: Optional[str] = None
    # Full Claude conversation history re-sent on every API call (stateless API)
    messages: List[dict] = []


# In-memory store keyed by session_id — easy to replace with Redis
sessions: dict[str, SessionState] = {}


def get_or_create_session(session_id: Optional[str] = None) -> SessionState:
    if session_id and session_id in sessions:
        return sessions[session_id]
    state = SessionState()
    sessions[state.session_id] = state
    return state
