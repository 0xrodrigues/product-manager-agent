import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.conversation_agent import ConversationAgent
from app.agents.interview_agent import InterviewAgent
from app.config import settings
from app.core.formatting import build_jira_description, format_story
from app.services.jira import JiraClient
from app.models.session import SessionPhase, SessionResponse
from app.models.story import (
    JiraTicket,
    JiraTicketResponse,
    RawStory,
    RefineAndCreateResponse,
)
from app.services import session_store

logger = logging.getLogger(__name__)
router = APIRouter()


class _UserMessage(BaseModel):
    message: str


@router.post("/stories/session", response_model=SessionResponse)
def create_session(raw: RawStory) -> SessionResponse:
    """Start an interview session from a raw story."""
    session = session_store.create_session()
    try:
        result = InterviewAgent().start(session, raw)
    except ValueError as exc:
        session_store.delete_session(session.id)
        logger.error("Initial interview failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session_store.update_session(session)
    return SessionResponse(
        session_id=session.id,
        phase=session.phase,
        question=result.question,
        suggestion=result.suggestion,
        refined_story=result.refined_story,
        message=result.message,
    )


@router.post("/stories/session/{session_id}", response_model=SessionResponse)
def continue_session(session_id: str, body: _UserMessage) -> SessionResponse:
    """Send a follow-up message to an existing session."""
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        if session.phase == SessionPhase.INTERVIEWING:
            result = InterviewAgent().process(session, body.message)
            if result.phase == "refining":
                session.phase = SessionPhase.REFINING
            session_store.update_session(session)
            return SessionResponse(
                session_id=session.id,
                phase=session.phase,
                question=result.question,
                suggestion=result.suggestion,
                refined_story=result.refined_story,
                message=result.message,
            )
        else:
            story, message = ConversationAgent().process(session, body.message)
            session_store.update_session(session)
            return SessionResponse(
                session_id=session.id,
                phase=session.phase,
                refined_story=story,
                message=message,
            )
    except ValueError as exc:
        logger.error("Conversation turn failed for session %s: %s", session_id, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/stories/session/{session_id}/confirm", response_model=RefineAndCreateResponse)
def confirm_session(session_id: str) -> RefineAndCreateResponse:
    """Approve the current story and create a Jira ticket."""
    session = session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.last_refined_story is None:
        raise HTTPException(status_code=422, detail="Session has no refined story to confirm")

    refined = session.last_refined_story
    formatted = format_story(refined)
    ticket = JiraTicket(
        project_key=settings.jira_project_key,
        summary=formatted.title,
        description=build_jira_description(formatted),
        story_points=formatted.story_points,
    )

    if not settings.jira_enabled:
        logger.info("Jira integration disabled — returning mock ticket")
        jira_response = JiraTicketResponse(
            ticket_id="MOCK-0",
            ticket_key="MOCK-0",
            url="http://mock/browse/MOCK-0",
        )
    else:
        try:
            jira_response = JiraClient().create_ticket(ticket)
        except Exception as exc:
            logger.error("Jira ticket creation failed: %s", exc)
            raise HTTPException(status_code=502, detail="Failed to create Jira ticket") from exc

    session_store.delete_session(session_id)
    return RefineAndCreateResponse(refined_story=formatted, jira_ticket=jira_response)


@router.delete("/stories/session/{session_id}", status_code=204)
def discard_session(session_id: str) -> None:
    """Discard a session without creating a ticket."""
    if session_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session_store.delete_session(session_id)
