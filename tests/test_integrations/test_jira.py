from unittest.mock import MagicMock, patch

import pytest

from app.services.jira import JiraClient
from app.models.story import JiraTicket


_TICKET = JiraTicket(
    project_key="PROJ",
    summary="Login via SSO",
    description="As a user, I want SSO login.",
    story_points=3,
)

_JIRA_API_RESPONSE = {
    "id": "10001",
    "key": "PROJ-1",
    "self": "https://org.atlassian.net/rest/api/3/issue/10001",
}


@patch("app.services.jira.httpx.Client")
def test_create_ticket_returns_response(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = _JIRA_API_RESPONSE
    mock_response.raise_for_status = MagicMock()

    mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response

    result = JiraClient().create_ticket(_TICKET)

    assert result.ticket_key == "PROJ-1"
    assert "PROJ-1" in result.url
