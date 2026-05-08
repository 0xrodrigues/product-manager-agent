from pydantic import BaseModel, Field


class RawStory(BaseModel):
    """Input: unrefined user story from the requester."""

    title: str = Field(..., description="Short title of the story")
    description: str = Field(..., description="Free-form description of the need")


class RefinedStory(BaseModel):
    """Output: structured user story after AI refinement."""

    title: str
    user_story: str = Field(..., description="As a <role>, I want <goal>, so that <reason>")
    acceptance_criteria: list[str]
    story_points: int | None = None


class JiraTicket(BaseModel):
    """Represents the payload sent to Jira."""

    project_key: str
    summary: str
    description: str
    issue_type: str = "Story"
    story_points: int | None = None


class JiraTicketResponse(BaseModel):
    """Jira API response after ticket creation."""

    ticket_id: str
    ticket_key: str
    url: str


class RefineAndCreateResponse(BaseModel):
    """Combined response returned to the API caller."""

    refined_story: RefinedStory
    jira_ticket: JiraTicketResponse
