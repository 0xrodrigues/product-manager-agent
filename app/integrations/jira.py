import logging
from base64 import b64encode

import httpx

from app.config import settings
from app.models.story import JiraTicket, JiraTicketResponse

logger = logging.getLogger(__name__)


class JiraClient:
    """HTTP client for the Jira REST API v3."""

    def __init__(self) -> None:
        token = b64encode(
            f"{settings.jira_user_email}:{settings.jira_api_token}".encode()
        ).decode()
        self._base_url = settings.jira_base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_ticket(self, ticket: JiraTicket) -> JiraTicketResponse:
        """Create a Jira issue and return its key and URL.

        Raises:
            httpx.HTTPStatusError: on 4xx/5xx responses.
        """
        payload = self._build_payload(ticket)
        logger.info("Creating Jira ticket in project %s", ticket.project_key)

        with httpx.Client(headers=self._headers) as client:
            response = client.post(
                f"{self._base_url}/rest/api/3/issue",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        return JiraTicketResponse(
            ticket_id=data["id"],
            ticket_key=data["key"],
            url=f"{self._base_url}/browse/{data['key']}",
        )

    def _build_payload(self, ticket: JiraTicket) -> dict:
        """Convert a JiraTicket model into the Jira REST API payload format."""
        payload: dict = {
            "fields": {
                "project": {"key": ticket.project_key},
                "summary": ticket.summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": ticket.description}],
                        }
                    ],
                },
                "issuetype": {"name": ticket.issue_type},
            }
        }
        if ticket.story_points is not None:
            payload["fields"]["story_points"] = ticket.story_points
        return payload
