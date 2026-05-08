from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.story import JiraTicketResponse, RefinedStory

client = TestClient(app)

_REFINED = RefinedStory(
    title="Login via SSO",
    user_story="As a user, I want to log in via SSO, so that I don't manage separate credentials.",
    acceptance_criteria=["SSO redirects correctly", "Session is persisted after login"],
    story_points=3,
)

_JIRA_RESP = JiraTicketResponse(
    ticket_id="10001",
    ticket_key="PROJ-1",
    url="https://org.atlassian.net/browse/PROJ-1",
)


@patch("app.api.routes.StoryRefinerAgent")
def test_refine_story_returns_refined_story(mock_agent_cls: MagicMock) -> None:
    mock_agent_cls.return_value.refine.return_value = _REFINED
    response = client.post(
        "/api/v1/stories/refine",
        json={"title": "SSO login", "description": "Users should log in with SSO"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == _REFINED.title


@patch("app.api.routes.JiraClient")
@patch("app.api.routes.StoryRefinerAgent")
def test_refine_and_create_returns_combined_response(
    mock_agent_cls: MagicMock, mock_jira_cls: MagicMock
) -> None:
    mock_agent_cls.return_value.refine.return_value = _REFINED
    mock_jira_cls.return_value.create_ticket.return_value = _JIRA_RESP
    response = client.post(
        "/api/v1/stories/refine-and-create",
        json={"title": "SSO login", "description": "Users should log in with SSO"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["jira_ticket"]["ticket_key"] == "PROJ-1"
