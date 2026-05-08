import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.story_refiner import StoryRefinerAgent
from app.models.story import RawStory


_RAW = RawStory(title="SSO login", description="Users should log in with SSO")

_VALID_RESPONSE = {
    "title": "Login via SSO",
    "user_story": "As a user, I want SSO login, so that I manage fewer credentials.",
    "acceptance_criteria": ["Redirects to IdP", "Session persists"],
    "story_points": 3,
}


@patch("app.agents.story_refiner.anthropic.Anthropic")
def test_refine_returns_refined_story(mock_anthropic_cls: MagicMock) -> None:
    mock_msg = MagicMock()
    mock_msg.content[0].text = json.dumps(_VALID_RESPONSE)
    mock_anthropic_cls.return_value.messages.create.return_value = mock_msg

    agent = StoryRefinerAgent()
    result = agent.refine(_RAW)

    assert result.title == _VALID_RESPONSE["title"]
    assert len(result.acceptance_criteria) == 2


@patch("app.agents.story_refiner.anthropic.Anthropic")
def test_refine_raises_on_invalid_json(mock_anthropic_cls: MagicMock) -> None:
    mock_msg = MagicMock()
    mock_msg.content[0].text = "not json"
    mock_anthropic_cls.return_value.messages.create.return_value = mock_msg

    agent = StoryRefinerAgent()
    with pytest.raises(ValueError, match="valid JSON"):
        agent.refine(_RAW)
