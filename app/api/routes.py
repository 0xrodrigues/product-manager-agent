import logging

from fastapi import APIRouter, HTTPException

from app.agents.story_refiner import StoryRefinerAgent
from app.config import settings
from app.integrations.jira import JiraClient
from app.models.story import (
    JiraTicket,
    RawStory,
    RefineAndCreateResponse,
    RefinedStory,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/stories/refine", response_model=RefinedStory)
def refine_story(raw: RawStory) -> RefinedStory:
    """Refine a raw user story with AI and return the structured result."""
    try:
        return StoryRefinerAgent().refine(raw)
    except ValueError as exc:
        logger.error("Refinement failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/stories/refine-and-create", response_model=RefineAndCreateResponse)
def refine_and_create(raw: RawStory) -> RefineAndCreateResponse:
    """Refine a raw story with AI and create a Jira ticket in one step."""
    try:
        refined = StoryRefinerAgent().refine(raw)
    except ValueError as exc:
        logger.error("Refinement failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    ticket = JiraTicket(
        project_key=settings.jira_project_key,
        summary=refined.title,
        description=refined.user_story
        + "\n\nAcceptance Criteria:\n"
        + "\n".join(f"- {ac}" for ac in refined.acceptance_criteria),
        story_points=refined.story_points,
    )

    try:
        jira_response = JiraClient().create_ticket(ticket)
    except Exception as exc:
        logger.error("Jira ticket creation failed: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to create Jira ticket") from exc

    return RefineAndCreateResponse(refined_story=refined, jira_ticket=jira_response)
