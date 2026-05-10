from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.models.story import RefinedStory


class SessionPhase(str, Enum):
    INTERVIEWING = "interviewing"
    REFINING = "refining"


class SessionMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Session(BaseModel):
    id: str
    phase: SessionPhase = SessionPhase.INTERVIEWING
    history: list[SessionMessage] = Field(default_factory=list)
    last_refined_story: RefinedStory | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionResponse(BaseModel):
    session_id: str
    phase: SessionPhase
    question: str | None = None
    suggestion: str | None = None
    refined_story: RefinedStory | None = None
    message: str | None = None
