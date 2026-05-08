import json
import logging
from pathlib import Path

import anthropic

from app.config import settings
from app.models.story import RawStory, RefinedStory

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "refine_story.txt"


class StoryRefinerAgent:
    """Uses Claude to transform a raw story description into a structured user story."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")

    def refine(self, raw: RawStory) -> RefinedStory:
        """Send the raw story to Claude and return the refined result.

        Raises:
            anthropic.APIError: on API failures.
            ValueError: if the model returns invalid JSON.
        """
        prompt = self._prompt_template.format(
            title=raw.title,
            description=raw.description,
        )
        logger.info("Refining story: %s", raw.title)

        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_json = message.content[0].text
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.error("Model returned invalid JSON: %s", raw_json)
            raise ValueError("Model did not return valid JSON") from exc

        return RefinedStory(**data)
